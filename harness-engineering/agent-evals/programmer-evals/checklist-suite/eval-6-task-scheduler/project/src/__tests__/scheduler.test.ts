import {
  handleTask,
  scorePriority,
  assignTask,
  TaskInput,
  ScheduleResult,
  ScheduleError,
  WorkloadService,
} from '../scheduler';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Fixed reference timestamp for deterministic tests: 2026-06-01T00:00:00Z */
const FIXED_NOW = new Date('2026-06-01T00:00:00Z').getTime();
const fixedClock = () => FIXED_NOW;

/** Return an ISO date string N days after FIXED_NOW. */
function futureDate(days: number): string {
  return new Date(FIXED_NOW + days * 24 * 60 * 60 * 1000).toISOString();
}

/** Return an ISO date string N days before FIXED_NOW. */
function pastDate(days: number): string {
  return new Date(FIXED_NOW - days * 24 * 60 * 60 * 1000).toISOString();
}

/** Build a valid TaskInput with sensible defaults, overridable per-field. */
function buildInput(overrides: Partial<TaskInput> = {}): TaskInput {
  return {
    title: 'Fix login bug',
    description: 'Users cannot log in on Safari',
    priority: 'high',
    dueDate: futureDate(7),
    assigneeId: 'user-42',
    tags: ['bug', 'frontend'],
    ...overrides,
  };
}

/** Stub ID generator for deterministic task IDs. */
const stubId = () => 'task-test-001';

/** Create a mock WorkloadService with configurable capacity. */
function buildWorkloadService(overrides?: {
  activeTasks?: number;
  maxTasks?: number;
  recordThrows?: Error;
  getThrows?: Error;
}): WorkloadService {
  const active = overrides?.activeTasks ?? 2;
  const max = overrides?.maxTasks ?? 10;
  return {
    getAssignee: overrides?.getThrows
      ? jest.fn().mockRejectedValue(overrides.getThrows)
      : jest.fn().mockResolvedValue({
          id: 'user-42',
          maxTasks: max,
          activeTasks: active,
          completedTasks: 5,
        }),
    recordAssignment: overrides?.recordThrows
      ? jest.fn().mockRejectedValue(overrides.recordThrows)
      : jest.fn().mockResolvedValue(undefined),
  };
}

/** Type guard: result is a successful ScheduleResult. */
function isResult(r: ScheduleResult | ScheduleError): r is ScheduleResult {
  return 'taskId' in r;
}

/** Type guard: result is a ScheduleError. */
function isError(r: ScheduleResult | ScheduleError): r is ScheduleError {
  return 'error' in r;
}

// ---------------------------------------------------------------------------
// scorePriority — pure scoring
// ---------------------------------------------------------------------------

describe('scorePriority', () => {
  it('returns the base score for a far-future due date with no tags', () => {
    // 100 days out => urgency bonus = max(0, 30 - 200) = 0
    const score = scorePriority(
      { priority: 'high', dueDate: futureDate(100), tags: [] },
      { now: fixedClock },
    );
    expect(score).toBe(60);
  });

  it('returns base + urgency for a near due date', () => {
    // 5 days out => urgency = round(30 - 10) = 20
    const score = scorePriority(
      { priority: 'low', dueDate: futureDate(5), tags: [] },
      { now: fixedClock },
    );
    expect(score).toBe(10 + 20); // 30
  });

  it('caps urgency bonus at 30 when due date is today', () => {
    // 0 days => urgency = 30
    const score = scorePriority(
      { priority: 'low', dueDate: futureDate(0.001), tags: [] },
      { now: fixedClock },
    );
    // base 10 + urgency 30 = 40
    expect(score).toBe(40);
  });

  it('adds tag weights from the options parameter', () => {
    const score = scorePriority(
      { priority: 'medium', dueDate: futureDate(100), tags: ['security', 'p0'] },
      { tagWeights: { security: 15, p0: 10 }, now: fixedClock },
    );
    // base 30 + urgency 0 + tags 25 = 55
    expect(score).toBe(55);
  });

  it('ignores unknown tags gracefully', () => {
    const score = scorePriority(
      { priority: 'medium', dueDate: futureDate(100), tags: ['unknown'] },
      { tagWeights: { security: 15 }, now: fixedClock },
    );
    expect(score).toBe(30);
  });

  it('clamps total score to 100', () => {
    const score = scorePriority(
      { priority: 'critical', dueDate: futureDate(0.001), tags: ['bonus'] },
      { tagWeights: { bonus: 50 }, now: fixedClock },
    );
    expect(score).toBe(100);
  });

  it('returns higher scores for critical than low priority', () => {
    const low = scorePriority(
      { priority: 'low', dueDate: futureDate(10), tags: [] },
      { now: fixedClock },
    );
    const critical = scorePriority(
      { priority: 'critical', dueDate: futureDate(10), tags: [] },
      { now: fixedClock },
    );
    expect(critical).toBeGreaterThan(low);
  });

  it('uses default Date.now when no clock is provided', () => {
    const score = scorePriority(
      { priority: 'medium', dueDate: futureDate(100), tags: [] },
    );
    expect(typeof score).toBe('number');
    expect(score).toBeGreaterThanOrEqual(0);
    expect(score).toBeLessThanOrEqual(100);
  });

  it('returns base score with empty tags array', () => {
    const score = scorePriority(
      { priority: 'critical', dueDate: futureDate(100), tags: [] },
      { now: fixedClock },
    );
    expect(score).toBe(90);
  });
});

// ---------------------------------------------------------------------------
// assignTask
// ---------------------------------------------------------------------------

describe('assignTask', () => {
  it('returns assigneeId when user has capacity', async () => {
    const ws = buildWorkloadService({ activeTasks: 2, maxTasks: 10 });
    const result = await assignTask(
      { taskId: 'task-1', assigneeId: 'user-42' },
      { workloadService: ws },
    );
    expect(result).toBe('user-42');
    expect(ws.recordAssignment).toHaveBeenCalledWith('task-1', 'user-42');
  });

  it('returns null when user is at max capacity', async () => {
    const ws = buildWorkloadService({ activeTasks: 10, maxTasks: 10 });
    const result = await assignTask(
      { taskId: 'task-1', assigneeId: 'user-42' },
      { workloadService: ws },
    );
    expect(result).toBeNull();
    expect(ws.recordAssignment).not.toHaveBeenCalled();
  });

  it('returns null when user is over capacity', async () => {
    const ws = buildWorkloadService({ activeTasks: 12, maxTasks: 10 });
    const result = await assignTask(
      { taskId: 'task-1', assigneeId: 'user-42' },
      { workloadService: ws },
    );
    expect(result).toBeNull();
  });

  it('awaits recordAssignment before returning', async () => {
    let recorded = false;
    const ws: WorkloadService = {
      getAssignee: jest.fn().mockResolvedValue({
        id: 'user-42',
        maxTasks: 10,
        activeTasks: 2,
        completedTasks: 0,
      }),
      recordAssignment: jest.fn().mockImplementation(async () => {
        recorded = true;
      }),
    };
    const result = await assignTask(
      { taskId: 'task-1', assigneeId: 'user-42' },
      { workloadService: ws },
    );
    expect(result).toBe('user-42');
    expect(recorded).toBe(true);
  });

  it('propagates workload service errors', async () => {
    const ws = buildWorkloadService({
      getThrows: new Error('service unavailable'),
    });
    await expect(
      assignTask({ taskId: 'task-1', assigneeId: 'user-42' }, { workloadService: ws }),
    ).rejects.toThrow('service unavailable');
  });
});

// ---------------------------------------------------------------------------
// handleTask — validation
// ---------------------------------------------------------------------------

describe('handleTask — validation', () => {
  it('rejects empty title', async () => {
    const result = await handleTask(buildInput({ title: '' }), {
      now: fixedClock,
      generateId: stubId,
    });
    expect(isError(result)).toBe(true);
    if (isError(result)) {
      expect(result.error).toBe('Title is required');
    }
  });

  it('rejects whitespace-only title', async () => {
    const result = await handleTask(buildInput({ title: '   ' }), {
      now: fixedClock,
      generateId: stubId,
    });
    expect(isError(result)).toBe(true);
    if (isError(result)) {
      expect(result.error).toBe('Title is required');
    }
  });

  it('rejects invalid priority', async () => {
    const result = await handleTask(buildInput({ priority: 'urgent' }), {
      now: fixedClock,
      generateId: stubId,
    });
    expect(isError(result)).toBe(true);
    if (isError(result)) {
      expect(result.error).toBe('Invalid priority: urgent');
    }
  });

  it('rejects past due date', async () => {
    const result = await handleTask(buildInput({ dueDate: pastDate(5) }), {
      now: fixedClock,
      generateId: stubId,
    });
    expect(isError(result)).toBe(true);
    if (isError(result)) {
      expect(result.error).toContain('future');
    }
  });

  it('rejects unparseable due date', async () => {
    const result = await handleTask(buildInput({ dueDate: 'not-a-date' }), {
      now: fixedClock,
      generateId: stubId,
    });
    expect(isError(result)).toBe(true);
    if (isError(result)) {
      expect(result.error).toContain('valid date');
    }
  });
});

// ---------------------------------------------------------------------------
// handleTask — success paths
// ---------------------------------------------------------------------------

describe('handleTask — success', () => {
  it('returns a full ScheduleResult with workload service', async () => {
    const ws = buildWorkloadService();
    const result = await handleTask(buildInput(), {
      now: fixedClock,
      generateId: stubId,
      workloadService: ws,
    });

    expect(isResult(result)).toBe(true);
    if (!isResult(result)) return;

    expect(result.taskId).toBe('task-test-001');
    expect(typeof result.priorityScore).toBe('number');
    expect(result.priorityScore).toBeGreaterThanOrEqual(0);
    expect(result.priorityScore).toBeLessThanOrEqual(100);
    expect(result.assignedTo).toBe('user-42');
    expect(result.scheduledAt).toBe(new Date(FIXED_NOW).toISOString());
    expect(result.warnings).toEqual([]);
  });

  it('includes a warning when assignee is at capacity', async () => {
    const ws = buildWorkloadService({ activeTasks: 10, maxTasks: 10 });
    const result = await handleTask(buildInput(), {
      now: fixedClock,
      generateId: stubId,
      workloadService: ws,
    });

    expect(isResult(result)).toBe(true);
    if (!isResult(result)) return;

    expect(result.assignedTo).toBeNull();
    expect(result.warnings).toHaveLength(1);
    expect(result.warnings[0]).toContain('at capacity');
  });

  it('includes a warning when no workload service is provided', async () => {
    const result = await handleTask(buildInput(), {
      now: fixedClock,
      generateId: stubId,
    });

    expect(isResult(result)).toBe(true);
    if (!isResult(result)) return;

    expect(result.assignedTo).toBeNull();
    expect(result.warnings).toHaveLength(1);
    expect(result.warnings[0]).toContain('No workload service');
  });

  it('includes a warning when workload service throws', async () => {
    const ws = buildWorkloadService({
      getThrows: new Error('connection refused'),
    });
    const result = await handleTask(buildInput(), {
      now: fixedClock,
      generateId: stubId,
      workloadService: ws,
    });

    expect(isResult(result)).toBe(true);
    if (!isResult(result)) return;

    expect(result.assignedTo).toBeNull();
    expect(result.warnings).toHaveLength(1);
    expect(result.warnings[0]).toContain('connection refused');
  });

  it('applies tag weights from options', async () => {
    const ws = buildWorkloadService();
    const withTags = await handleTask(
      buildInput({ tags: ['security'] }),
      {
        now: fixedClock,
        generateId: stubId,
        tagWeights: { security: 15 },
        workloadService: ws,
      },
    );
    const withoutTags = await handleTask(
      buildInput({ tags: [] }),
      {
        now: fixedClock,
        generateId: stubId,
        workloadService: ws,
      },
    );

    expect(isResult(withTags)).toBe(true);
    expect(isResult(withoutTags)).toBe(true);
    if (isResult(withTags) && isResult(withoutTags)) {
      expect(withTags.priorityScore).toBeGreaterThan(withoutTags.priorityScore);
    }
  });

  it('uses custom ID generator', async () => {
    const result = await handleTask(buildInput(), {
      now: fixedClock,
      generateId: () => 'custom-id-abc',
    });

    expect(isResult(result)).toBe(true);
    if (isResult(result)) {
      expect(result.taskId).toBe('custom-id-abc');
    }
  });

  it('produces a valid ISO scheduledAt timestamp', async () => {
    const result = await handleTask(buildInput(), {
      now: fixedClock,
      generateId: stubId,
    });

    expect(isResult(result)).toBe(true);
    if (isResult(result)) {
      expect(new Date(result.scheduledAt).toISOString()).toBe(result.scheduledAt);
    }
  });
});
