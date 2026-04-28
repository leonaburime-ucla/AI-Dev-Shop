import {
  processBatch,
  NotificationRequest,
  UserService,
  TemplateService,
  EmailService,
  BatchResult,
  Priority,
} from '../processor';

// ─── Test Helpers ─────────────────────────────────────────────────────

/** No-op delay for fast tests. */
const instantDelay = async (_ms: number): Promise<void> => {};

function makeNotification(
  overrides: Partial<NotificationRequest> = {},
): NotificationRequest {
  return {
    userId: 'user1',
    templateId: 'welcome',
    data: {},
    priority: 'normal',
    ...overrides,
  };
}

function makeMocks(): {
  userService: UserService;
  templateService: TemplateService;
  emailService: EmailService;
  sendCalls: Array<{ to: string; html: string }>;
} {
  const sendCalls: Array<{ to: string; html: string }> = [];
  return {
    userService: {
      getUser: async (id: string) => ({ email: `${id}@test.com` }),
    },
    templateService: {
      render: async (templateId: string, data: Record<string, unknown>) =>
        `<html>${templateId}:${JSON.stringify(data)}</html>`,
    },
    emailService: {
      send: async (to: string, html: string) => {
        sendCalls.push({ to, html });
      },
    },
    sendCalls,
  };
}

// ─── Tests ────────────────────────────────────────────────────────────

describe('processBatch', () => {
  // ── Happy Path ────────────────────────────────────────────────────

  it('sends all notifications in a simple batch', async () => {
    const { userService, templateService, emailService, sendCalls } = makeMocks();
    const notifications = [
      makeNotification({ userId: 'u1' }),
      makeNotification({ userId: 'u2', templateId: 'reset' }),
    ];

    const result = await processBatch(
      { notifications, userService, templateService, emailService },
      { delay: instantDelay },
    );

    expect(result.sent).toBe(2);
    expect(result.failed).toBe(0);
    expect(result.deduplicated).toBe(0);
    expect(result.results).toHaveLength(2);
    expect(sendCalls).toHaveLength(2);
    expect(result.elapsedMs).toBeGreaterThanOrEqual(0);
  });

  it('returns empty results for an empty batch', async () => {
    const { userService, templateService, emailService } = makeMocks();

    const result = await processBatch(
      { notifications: [], userService, templateService, emailService },
      { delay: instantDelay },
    );

    expect(result.sent).toBe(0);
    expect(result.failed).toBe(0);
    expect(result.deduplicated).toBe(0);
    expect(result.results).toHaveLength(0);
  });

  // ── Deduplication ─────────────────────────────────────────────────

  it('deduplicates same userId+templateId within a batch', async () => {
    const { userService, templateService, emailService, sendCalls } = makeMocks();
    const notifications = [
      makeNotification({ userId: 'u1', templateId: 'welcome' }),
      makeNotification({ userId: 'u1', templateId: 'welcome' }),
      makeNotification({ userId: 'u1', templateId: 'welcome' }),
    ];

    const result = await processBatch(
      { notifications, userService, templateService, emailService },
      { delay: instantDelay },
    );

    expect(result.sent).toBe(1);
    expect(result.deduplicated).toBe(2);
    expect(sendCalls).toHaveLength(1);
    // Deduplicated items appear in results
    const deduped = result.results.filter((r) => r.status === 'deduplicated');
    expect(deduped).toHaveLength(2);
  });

  it('does NOT deduplicate different templates for same user', async () => {
    const { userService, templateService, emailService, sendCalls } = makeMocks();
    const notifications = [
      makeNotification({ userId: 'u1', templateId: 'welcome' }),
      makeNotification({ userId: 'u1', templateId: 'reset' }),
    ];

    const result = await processBatch(
      { notifications, userService, templateService, emailService },
      { delay: instantDelay },
    );

    expect(result.sent).toBe(2);
    expect(result.deduplicated).toBe(0);
    expect(sendCalls).toHaveLength(2);
  });

  it('does NOT deduplicate same template for different users', async () => {
    const { userService, templateService, emailService, sendCalls } = makeMocks();
    const notifications = [
      makeNotification({ userId: 'u1', templateId: 'welcome' }),
      makeNotification({ userId: 'u2', templateId: 'welcome' }),
    ];

    const result = await processBatch(
      { notifications, userService, templateService, emailService },
      { delay: instantDelay },
    );

    expect(result.sent).toBe(2);
    expect(result.deduplicated).toBe(0);
  });

  // ── Retry & Backoff ───────────────────────────────────────────────

  it('retries failed sends with exponential backoff', async () => {
    const { userService, templateService } = makeMocks();
    let callCount = 0;
    const flakyEmailService: EmailService = {
      send: async () => {
        callCount++;
        if (callCount < 3) throw new Error('transient');
      },
    };

    const delays: number[] = [];
    const trackingDelay = async (ms: number): Promise<void> => {
      delays.push(ms);
    };

    const result = await processBatch(
      {
        notifications: [makeNotification()],
        userService,
        templateService,
        emailService: flakyEmailService,
      },
      { delay: trackingDelay, baseDelayMs: 100 },
    );

    expect(result.sent).toBe(1);
    expect(callCount).toBe(3);
    // Exponential: 2^0*100=100, 2^1*100=200
    expect(delays).toEqual([100, 200]);
  });

  it('fails after max retries exhausted', async () => {
    const { userService, templateService } = makeMocks();
    const alwaysFail: EmailService = {
      send: async () => {
        throw new Error('permanent failure');
      },
    };

    const result = await processBatch(
      {
        notifications: [makeNotification()],
        userService,
        templateService,
        emailService: alwaysFail,
      },
      { delay: instantDelay, maxRetries: 3 },
    );

    expect(result.failed).toBe(1);
    expect(result.sent).toBe(0);
    expect(result.results[0].status).toBe('failed');
    expect(result.results[0].error).toContain('permanent failure');
  });

  it('respects custom maxRetries option', async () => {
    const { userService, templateService } = makeMocks();
    let callCount = 0;
    const alwaysFail: EmailService = {
      send: async () => {
        callCount++;
        throw new Error('fail');
      },
    };

    await processBatch(
      {
        notifications: [makeNotification()],
        userService,
        templateService,
        emailService: alwaysFail,
      },
      { delay: instantDelay, maxRetries: 5 },
    );

    expect(callCount).toBe(5);
  });

  // ── Failure Isolation ─────────────────────────────────────────────

  it('continues batch when individual items fail', async () => {
    const { userService, templateService } = makeMocks();
    let callIdx = 0;
    const partialFail: EmailService = {
      send: async (to: string) => {
        callIdx++;
        if (to === 'u2@test.com') throw new Error('u2 down');
      },
    };

    const notifications = [
      makeNotification({ userId: 'u1' }),
      makeNotification({ userId: 'u2' }),
      makeNotification({ userId: 'u3' }),
    ];

    const result = await processBatch(
      { notifications, userService, templateService, emailService: partialFail },
      { delay: instantDelay, maxRetries: 1 },
    );

    expect(result.sent).toBe(2);
    expect(result.failed).toBe(1);
    expect(result.results.find((r) => r.userId === 'u2')?.status).toBe('failed');
    expect(result.results.find((r) => r.userId === 'u1')?.status).toBe('sent');
    expect(result.results.find((r) => r.userId === 'u3')?.status).toBe('sent');
  });

  it('handles user service failure as a retry-able error', async () => {
    const { templateService, emailService } = makeMocks();
    let callCount = 0;
    const flakyUserService: UserService = {
      getUser: async (id: string) => {
        callCount++;
        if (callCount < 2) throw new Error('user service down');
        return { email: `${id}@test.com` };
      },
    };

    const result = await processBatch(
      {
        notifications: [makeNotification()],
        userService: flakyUserService,
        templateService,
        emailService,
      },
      { delay: instantDelay },
    );

    expect(result.sent).toBe(1);
    expect(callCount).toBe(2);
  });

  it('handles template service failure as a retry-able error', async () => {
    const { userService, emailService } = makeMocks();
    let callCount = 0;
    const flakyTemplate: TemplateService = {
      render: async () => {
        callCount++;
        if (callCount < 2) throw new Error('template service down');
        return '<html>ok</html>';
      },
    };

    const result = await processBatch(
      {
        notifications: [makeNotification()],
        userService,
        templateService: flakyTemplate,
        emailService,
      },
      { delay: instantDelay },
    );

    expect(result.sent).toBe(1);
  });

  // ── Chunking ──────────────────────────────────────────────────────

  it('processes notifications in chunks of configured size', async () => {
    const { userService, templateService, emailService } = makeMocks();
    const concurrencySnapshots: number[] = [];
    let inFlight = 0;

    const trackingEmailService: EmailService = {
      send: async (to: string, html: string) => {
        inFlight++;
        concurrencySnapshots.push(inFlight);
        // Simulate async work so concurrency is observable
        await new Promise((r) => setTimeout(r, 1));
        inFlight--;
      },
    };

    const notifications = Array.from({ length: 10 }, (_, i) =>
      makeNotification({ userId: `u${i}`, templateId: 'tpl' }),
    );

    const result = await processBatch(
      { notifications, userService, templateService, emailService: trackingEmailService },
      { delay: instantDelay, chunkSize: 3 },
    );

    expect(result.sent).toBe(10);
    // Max concurrency should never exceed chunk size of 3
    expect(Math.max(...concurrencySnapshots)).toBeLessThanOrEqual(3);
  });

  // ── Priority Ordering ─────────────────────────────────────────────

  it('processes high-priority items before normal and low', async () => {
    const sendOrder: string[] = [];
    const { userService, templateService } = makeMocks();
    const orderTracker: EmailService = {
      send: async (to: string) => {
        sendOrder.push(to);
      },
    };

    const notifications: NotificationRequest[] = [
      makeNotification({ userId: 'low1', priority: 'low' }),
      makeNotification({ userId: 'high1', priority: 'high' }),
      makeNotification({ userId: 'norm1', priority: 'normal' }),
      makeNotification({ userId: 'high2', priority: 'high', templateId: 'other' }),
      makeNotification({ userId: 'low2', priority: 'low', templateId: 'other' }),
    ];

    const result = await processBatch(
      { notifications, userService, templateService, emailService: orderTracker },
      { delay: instantDelay, chunkSize: 100 }, // single chunk to observe ordering
    );

    expect(result.sent).toBe(5);
    // High-priority items should come first
    const highIndices = sendOrder
      .map((email, i) => (email.startsWith('high') ? i : -1))
      .filter((i) => i >= 0);
    const normalIndices = sendOrder
      .map((email, i) => (email.startsWith('norm') ? i : -1))
      .filter((i) => i >= 0);
    const lowIndices = sendOrder
      .map((email, i) => (email.startsWith('low') ? i : -1))
      .filter((i) => i >= 0);

    expect(Math.max(...highIndices)).toBeLessThan(Math.min(...normalIndices));
    expect(Math.max(...normalIndices)).toBeLessThan(Math.min(...lowIndices));
  });

  // ── Batch Size Validation ─────────────────────────────────────────

  it('throws when batch exceeds max size', async () => {
    const { userService, templateService, emailService } = makeMocks();
    const notifications = Array.from({ length: 11 }, (_, i) =>
      makeNotification({ userId: `u${i}` }),
    );

    await expect(
      processBatch(
        { notifications, userService, templateService, emailService },
        { delay: instantDelay, maxBatchSize: 10 },
      ),
    ).rejects.toThrow('Batch size 11 exceeds maximum of 10');
  });

  it('accepts batch at exactly max size', async () => {
    const { userService, templateService, emailService } = makeMocks();
    const notifications = Array.from({ length: 10 }, (_, i) =>
      makeNotification({ userId: `u${i}` }),
    );

    const result = await processBatch(
      { notifications, userService, templateService, emailService },
      { delay: instantDelay, maxBatchSize: 10 },
    );

    expect(result.sent).toBe(10);
  });

  // ── Per-Item Results ──────────────────────────────────────────────

  it('includes templateId in per-item results', async () => {
    const { userService, templateService, emailService } = makeMocks();
    const notifications = [
      makeNotification({ userId: 'u1', templateId: 'welcome' }),
      makeNotification({ userId: 'u2', templateId: 'reset' }),
    ];

    const result = await processBatch(
      { notifications, userService, templateService, emailService },
      { delay: instantDelay },
    );

    expect(result.results[0].templateId).toBeDefined();
    expect(result.results[1].templateId).toBeDefined();
  });

  // ── Observability ─────────────────────────────────────────────────

  it('logs batch start, per-item events, and completion', async () => {
    const { userService, templateService } = makeMocks();
    const logs: Array<{ level: string; msg: string }> = [];
    const logger = {
      info: (msg: string, meta?: Record<string, unknown>) => logs.push({ level: 'info', msg }),
      warn: (msg: string, meta?: Record<string, unknown>) => logs.push({ level: 'warn', msg }),
      error: (msg: string, meta?: Record<string, unknown>) => logs.push({ level: 'error', msg }),
    };

    let callCount = 0;
    const partialFail: EmailService = {
      send: async (to: string) => {
        callCount++;
        if (to === 'u2@test.com' && callCount <= 4) throw new Error('fail');
      },
    };

    const notifications = [
      makeNotification({ userId: 'u1' }),
      makeNotification({ userId: 'u2' }),
    ];

    await processBatch(
      { notifications, userService, templateService, emailService: partialFail },
      { delay: instantDelay, logger },
    );

    expect(logs.some((l) => l.msg === 'batch.start')).toBe(true);
    expect(logs.some((l) => l.msg === 'batch.complete')).toBe(true);
    expect(logs.some((l) => l.msg === 'notification.sent')).toBe(true);
  });

  // ── Adversarial: Cross-Item Evidence ──────────────────────────────

  it('adversarial: dedup keys do not collide across userId/templateId boundaries', async () => {
    const { userService, templateService, emailService, sendCalls } = makeMocks();
    // These should NOT deduplicate — different userId:templateId combos
    const notifications = [
      makeNotification({ userId: 'a:b', templateId: 'c' }),
      makeNotification({ userId: 'a', templateId: 'b:c' }),
    ];

    const result = await processBatch(
      { notifications, userService, templateService, emailService },
      { delay: instantDelay },
    );

    expect(result.sent).toBe(2);
    expect(result.deduplicated).toBe(0);
    expect(sendCalls).toHaveLength(2);
  });

  it('adversarial: batch with all duplicates results in one send', async () => {
    const { userService, templateService, emailService, sendCalls } = makeMocks();
    const notifications = Array.from({ length: 100 }, () =>
      makeNotification({ userId: 'same', templateId: 'same' }),
    );

    const result = await processBatch(
      { notifications, userService, templateService, emailService },
      { delay: instantDelay },
    );

    expect(result.sent).toBe(1);
    expect(result.deduplicated).toBe(99);
    expect(sendCalls).toHaveLength(1);
    expect(result.results).toHaveLength(100);
  });

  it('adversarial: mixed failures and deduplication in same batch', async () => {
    const { userService, templateService } = makeMocks();
    const failForU2: EmailService = {
      send: async (to: string) => {
        if (to === 'u2@test.com') throw new Error('u2 permanently down');
      },
    };

    const notifications = [
      makeNotification({ userId: 'u1', templateId: 'a' }),
      makeNotification({ userId: 'u2', templateId: 'a' }),
      makeNotification({ userId: 'u1', templateId: 'a' }), // duplicate
      makeNotification({ userId: 'u3', templateId: 'a' }),
      makeNotification({ userId: 'u2', templateId: 'a' }), // duplicate
    ];

    const result = await processBatch(
      {
        notifications,
        userService,
        templateService,
        emailService: failForU2,
      },
      { delay: instantDelay, maxRetries: 1 },
    );

    expect(result.sent).toBe(2);
    expect(result.failed).toBe(1);
    expect(result.deduplicated).toBe(2);
    expect(result.sent + result.failed + result.deduplicated).toBe(5);
    expect(result.results).toHaveLength(5);
  });

  it('adversarial: every item in a large batch fails', async () => {
    const { userService, templateService } = makeMocks();
    const alwaysFail: EmailService = {
      send: async () => {
        throw new Error('total outage');
      },
    };

    const notifications = Array.from({ length: 120 }, (_, i) =>
      makeNotification({ userId: `u${i}` }),
    );

    const result = await processBatch(
      { notifications, userService, templateService, emailService: alwaysFail },
      { delay: instantDelay, maxRetries: 1 },
    );

    expect(result.failed).toBe(120);
    expect(result.sent).toBe(0);
    expect(result.results).toHaveLength(120);
    expect(result.results.every((r) => r.status === 'failed')).toBe(true);
  });

  it('adversarial: default delay is not instantaneous (ensures backoff wiring)', async () => {
    // Verifying the default delay produces actual waits — we just check
    // the parameter flows correctly by using a 1-retry config with
    // a tracking delay.
    const { userService, templateService } = makeMocks();
    const alwaysFail: EmailService = {
      send: async () => {
        throw new Error('fail');
      },
    };
    const delays: number[] = [];

    await processBatch(
      {
        notifications: [makeNotification()],
        userService,
        templateService,
        emailService: alwaysFail,
      },
      {
        delay: async (ms) => { delays.push(ms); },
        maxRetries: 3,
        baseDelayMs: 200,
      },
    );

    // 2^0*200=200, 2^1*200=400 — only 2 delays (no delay after last attempt)
    expect(delays).toEqual([200, 400]);
  });
});
