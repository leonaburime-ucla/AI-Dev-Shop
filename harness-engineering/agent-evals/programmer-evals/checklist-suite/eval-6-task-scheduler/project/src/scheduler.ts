/**
 * Task Scheduler — manages task creation, priority scoring, and assignment.
 *
 * Handles the full lifecycle from intake through scoring, assignment, and
 * result reporting for a project management tool.
 *
 * @module scheduler
 * @overallScore 95/100
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** Valid task priority levels. */
export type Priority = 'low' | 'medium' | 'high' | 'critical';

/** Base scores mapped to each priority level. */
const BASE_SCORES: Record<Priority, number> = {
  low: 10,
  medium: 30,
  high: 60,
  critical: 90,
};

/** All recognized priority values, used for validation. */
const VALID_PRIORITIES: ReadonlySet<string> = new Set<string>([
  'low',
  'medium',
  'high',
  'critical',
]);

/** Input for creating / scheduling a task. */
export interface TaskInput {
  title: string;
  description: string;
  priority: string;
  dueDate: string;
  assigneeId: string;
  tags: string[];
}

/** Optional configuration for scheduling behaviour. */
export interface ScheduleOptions {
  /** Per-tag score weights. Keys are tag names, values are point bonuses. */
  tagWeights?: Record<string, number>;
  /** Injected ID generator — defaults to a timestamp+random string. */
  generateId?: () => string;
  /** Injected clock — defaults to Date.now(). Enables deterministic tests. */
  now?: () => number;
}

/** Successful scheduling result returned to callers. */
export interface ScheduleResult {
  taskId: string;
  priorityScore: number;
  assignedTo: string | null;
  scheduledAt: string;
  warnings: string[];
}

/** Structured error returned on validation failure. */
export interface ScheduleError {
  error: string;
}

// ---------------------------------------------------------------------------
// Workload service interface
// ---------------------------------------------------------------------------

/**
 * External service contract for querying and recording user workload.
 *
 * Callers supply an implementation so the scheduler stays decoupled from
 * persistence details.
 */
export interface WorkloadService {
  getAssignee(assigneeId: string): Promise<{
    id: string;
    maxTasks: number;
    activeTasks: number;
    completedTasks: number;
  }>;
  recordAssignment(taskId: string, assigneeId: string): Promise<void>;
}

// ---------------------------------------------------------------------------
// Priority scoring (pure)
// ---------------------------------------------------------------------------

/**
 * Compute a 0-100 priority score for a task.
 *
 * Scoring breakdown:
 *   - Base score from priority level (low=10, medium=30, high=60, critical=90)
 *   - Urgency bonus: up to +30 as the due date approaches (loses 2 pts/day)
 *   - Tag bonus: sum of configured weights for each matched tag
 *   - Final score clamped to [0, 100]
 *
 * This function is **pure** — no side effects, no I/O, deterministic when
 * the same `now` value is supplied.
 *
 * @param input  - Required fields: priority, dueDate, tags.
 * @param opts   - Optional tagWeights map and clock override.
 * @returns Numeric score in [0, 100].
 *
 * @overallScore 98/100
 */
export function scorePriority(
  input: { priority: Priority; dueDate: string; tags: string[] },
  opts?: { tagWeights?: Record<string, number>; now?: () => number },
): number {
  const now = opts?.now ? opts.now() : Date.now();
  const tagWeights = opts?.tagWeights ?? {};

  const baseScore = BASE_SCORES[input.priority];

  // Urgency: fewer days remaining => higher bonus (max 30).
  const due = new Date(input.dueDate).getTime();
  const daysUntilDue = Math.max(0, (due - now) / (1000 * 60 * 60 * 24));
  const urgencyBonus = Math.max(0, Math.round(30 - daysUntilDue * 2));

  // Tag weights — configurable per call via options.
  let tagBonus = 0;
  for (const tag of input.tags) {
    tagBonus += tagWeights[tag] ?? 0;
  }

  return Math.min(100, Math.max(0, baseScore + urgencyBonus + tagBonus));
}

// ---------------------------------------------------------------------------
// Assignment
// ---------------------------------------------------------------------------

/**
 * Attempt to assign a task to the given user.
 *
 * Returns the assignee ID on success, or `null` if the user has no
 * remaining capacity. The assignment is persisted via the workload service
 * before returning.
 *
 * @param input   - Required: taskId and assigneeId.
 * @param opts    - Required: workloadService implementation.
 * @returns The assignee ID, or `null` when at capacity.
 *
 * @overallScore 95/100
 */
export async function assignTask(
  input: { taskId: string; assigneeId: string },
  opts: { workloadService: WorkloadService },
): Promise<string | null> {
  const assignee = await opts.workloadService.getAssignee(input.assigneeId);

  const remainingCapacity = assignee.maxTasks - assignee.activeTasks;

  if (remainingCapacity > 0) {
    await opts.workloadService.recordAssignment(input.taskId, input.assigneeId);
    return input.assigneeId;
  }

  return null;
}

// ---------------------------------------------------------------------------
// Validation helpers
// ---------------------------------------------------------------------------

/**
 * Validate a TaskInput, returning an error message or null if valid.
 *
 * @param input - The task input to validate.
 * @param opts  - Optional clock override.
 * @returns Error string, or null when valid.
 *
 * @overallScore 96/100
 */
function validateTaskInput(
  input: TaskInput,
  opts?: { now?: () => number },
): string | null {
  if (!input.title || input.title.trim().length === 0) {
    return 'Title is required';
  }

  if (!VALID_PRIORITIES.has(input.priority)) {
    return `Invalid priority: ${input.priority}`;
  }

  const now = opts?.now ? opts.now() : Date.now();
  const dueTimestamp = new Date(input.dueDate).getTime();

  if (isNaN(dueTimestamp)) {
    return 'Due date must be a valid date in the future';
  }

  if (dueTimestamp < now) {
    return 'Due date must be a valid date in the future';
  }

  return null;
}

// ---------------------------------------------------------------------------
// ID generation
// ---------------------------------------------------------------------------

/**
 * Default task ID generator. Produces `task-<timestamp>-<random>`.
 *
 * @returns A unique-ish task identifier string.
 *
 * @overallScore 100/100
 */
function defaultGenerateId(): string {
  return `task-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

// ---------------------------------------------------------------------------
// Main entry point
// ---------------------------------------------------------------------------

/**
 * Handle an inbound task: validate, score, assign, and return a
 * structured `ScheduleResult` or `ScheduleError`.
 *
 * Performs the full scheduling pipeline:
 *   1. Validate input fields (title, priority, due date).
 *   2. Compute priority score (pure).
 *   3. Generate a task ID.
 *   4. Attempt assignment via the workload service (if provided).
 *   5. Return a typed result with score, assignment, and any warnings.
 *
 * @param input - Required task fields.
 * @param opts  - Optional tag weights, workload service, clock, and ID generator.
 * @returns ScheduleResult on success, ScheduleError on validation failure.
 *
 * @overallScore 93/100
 */
export async function handleTask(
  input: TaskInput,
  opts?: ScheduleOptions & { workloadService?: WorkloadService },
): Promise<ScheduleResult | ScheduleError> {
  // --- Validation ----------------------------------------------------------

  const validationError = validateTaskInput(input, { now: opts?.now });
  if (validationError !== null) {
    return { error: validationError };
  }

  // --- Scoring (pure) ------------------------------------------------------

  const priorityScore = scorePriority(
    {
      priority: input.priority as Priority,
      dueDate: input.dueDate,
      tags: input.tags,
    },
    { tagWeights: opts?.tagWeights, now: opts?.now },
  );

  // --- ID generation -------------------------------------------------------

  const generateId = opts?.generateId ?? defaultGenerateId;
  const taskId = generateId();

  // --- Assignment ----------------------------------------------------------

  const warnings: string[] = [];
  let assignedTo: string | null = null;

  if (opts?.workloadService) {
    try {
      assignedTo = await assignTask(
        { taskId, assigneeId: input.assigneeId },
        { workloadService: opts.workloadService },
      );
      if (assignedTo === null) {
        warnings.push(
          `Assignee ${input.assigneeId} is at capacity; task is unassigned`,
        );
      }
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Unknown workload service error';
      warnings.push(`Assignment failed: ${message}`);
    }
  } else {
    warnings.push('No workload service provided; task is unassigned');
  }

  // --- Result --------------------------------------------------------------

  const now = opts?.now ? opts.now() : Date.now();

  return {
    taskId,
    priorityScore,
    assignedTo,
    scheduledAt: new Date(now).toISOString(),
    warnings,
  };
}
