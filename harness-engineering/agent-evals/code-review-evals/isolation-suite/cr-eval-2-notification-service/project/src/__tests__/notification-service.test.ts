/**
 * Tests for Notification Service.
 *
 * Coverage: formatting, sending, retries, channel availability, legacy compat.
 */

import {
  formatMessage,
  sendNotification,
  legacyNotify,
  processPendingNotifications,
  type NotificationRequest,
  type ChannelProvider,
  type NotificationStore,
  type NotificationRecord,
  type NotificationChannel,
} from '../notification-service';

// --- Test helpers ---

function makeMockProvider(overrides: Partial<ChannelProvider> = {}): ChannelProvider {
  return {
    send: jest.fn().mockResolvedValue({ success: true }),
    isAvailable: jest.fn().mockResolvedValue(true),
    ...overrides,
  };
}

function makeMockStore(overrides: Partial<NotificationStore> = {}): NotificationStore {
  return {
    save: jest.fn().mockResolvedValue(undefined),
    findById: jest.fn().mockResolvedValue(null),
    findPending: jest.fn().mockResolvedValue([]),
    ...overrides,
  };
}

function makeProviders(
  overrides: Partial<Record<NotificationChannel, ChannelProvider>> = {},
): Record<NotificationChannel, ChannelProvider> {
  return {
    email: makeMockProvider(),
    sms: makeMockProvider(),
    push: makeMockProvider(),
    ...overrides,
  };
}

function makeRequest(overrides: Partial<NotificationRequest> = {}): NotificationRequest {
  return {
    recipientId: 'USER-001',
    channel: 'email',
    subject: 'Test Notification',
    body: 'Hello, this is a test notification.',
    priority: 'high',
    ...overrides,
  };
}

// --- formatMessage tests ---

describe('formatMessage', () => {
  it('should format email with subject', () => {
    const result = formatMessage('email', 'Hello', 'Body text');
    expect(result).toBe('Subject: Hello\n\nBody text');
  });

  it('should format email without subject', () => {
    const result = formatMessage('email', undefined, 'Body text');
    expect(result).toBe('Body text');
  });

  it('should truncate SMS to 160 chars', () => {
    const longMessage = 'A'.repeat(200);
    const result = formatMessage('sms', undefined, longMessage);
    expect(result.length).toBeLessThanOrEqual(160);
    expect(result).toContain('...');
  });

  it('should not truncate short SMS', () => {
    const result = formatMessage('sms', undefined, 'Short message');
    expect(result).toBe('Short message');
  });

  it('should truncate push to 100 chars and strip newlines', () => {
    const longMessage = 'Line 1\nLine 2\n' + 'A'.repeat(200);
    const result = formatMessage('push', undefined, longMessage);
    expect(result.length).toBeLessThanOrEqual(100);
    expect(result).not.toContain('\n');
  });

  it('should return body for unknown channel', () => {
    const result = formatMessage('carrier-pigeon' as NotificationChannel, undefined, 'Body');
    expect(result).toBe('Body');
  });
});

// --- sendNotification tests ---

describe('sendNotification', () => {
  it('should send a notification successfully', async () => {
    const providers = makeProviders();
    const store = makeMockStore();

    const result = await sendNotification(makeRequest(), { providers, store });

    expect(result.status).toBe('sent');
    expect(result.notificationId).toBeTruthy();
    expect(store.save).toHaveBeenCalledTimes(1);
  });

  it('should throw for unknown channel', async () => {
    const providers = {} as Record<NotificationChannel, ChannelProvider>;
    const store = makeMockStore();

    await expect(
      sendNotification(
        makeRequest({ channel: 'fax' as NotificationChannel }),
        { providers, store },
      ),
    ).rejects.toThrow('Unknown channel');
  });

  it('should queue when channel is unavailable', async () => {
    const emailProvider = makeMockProvider({
      isAvailable: jest.fn().mockResolvedValue(false),
    });
    const providers = makeProviders({ email: emailProvider });
    const store = makeMockStore();

    const result = await sendNotification(makeRequest(), { providers, store });

    expect(result.status).toBe('queued');
    expect(store.save).toHaveBeenCalledTimes(1);
  });

  it('should retry on failure and eventually succeed', async () => {
    const emailProvider = makeMockProvider({
      send: jest.fn()
        .mockResolvedValueOnce({ success: false, error: 'Temporary failure' })
        .mockResolvedValueOnce({ success: true }),
    });
    const providers = makeProviders({ email: emailProvider });
    const store = makeMockStore();

    const result = await sendNotification(makeRequest(), { providers, store });

    expect(result.status).toBe('sent');
    expect(emailProvider.send).toHaveBeenCalledTimes(2);
  }, 15000);

  it('should fail after all retries exhausted', async () => {
    const emailProvider = makeMockProvider({
      send: jest.fn().mockResolvedValue({ success: false, error: 'Persistent failure' }),
    });
    const providers = makeProviders({ email: emailProvider });
    const store = makeMockStore();

    const result = await sendNotification(makeRequest(), { providers, store });

    expect(result.status).toBe('failed');
    expect(result.error).toBe('Persistent failure');
    expect(emailProvider.send).toHaveBeenCalledTimes(3);
  }, 30000);

  it('should handle provider throwing exceptions', async () => {
    const emailProvider = makeMockProvider({
      send: jest.fn().mockRejectedValue(new Error('Network error')),
    });
    const providers = makeProviders({ email: emailProvider });
    const store = makeMockStore();

    const result = await sendNotification(makeRequest(), { providers, store });

    expect(result.status).toBe('failed');
    expect(result.error).toBe('Network error');
  }, 30000);
});

// --- legacyNotify tests ---

describe('legacyNotify', () => {
  it('should return true on success', async () => {
    const provider = makeMockProvider();
    const result = await legacyNotify('user@example.com', 'Hello', provider);
    expect(result).toBe(true);
  });

  it('should return false on failure', async () => {
    const provider = makeMockProvider({
      send: jest.fn().mockResolvedValue({ success: false }),
    });
    const result = await legacyNotify('user@example.com', 'Hello', provider);
    expect(result).toBe(false);
  });

  it('should return false on exception', async () => {
    const provider = makeMockProvider({
      send: jest.fn().mockRejectedValue(new Error('Boom')),
    });
    const result = await legacyNotify('user@example.com', 'Hello', provider);
    expect(result).toBe(false);
  });
});

// --- processPendingNotifications tests ---

describe('processPendingNotifications', () => {
  it('should process pending notifications', async () => {
    const pending: NotificationRecord[] = [
      {
        id: 'NOTIF-1',
        recipientId: 'USER-001',
        channel: 'email',
        body: 'Pending message',
        formattedBody: 'Pending message',
        priority: 'high',
        status: 'queued',
        attempts: 0,
      },
    ];
    const providers = makeProviders();
    const store = makeMockStore({
      findPending: jest.fn().mockResolvedValue(pending),
    });

    const results = await processPendingNotifications('email', { providers, store });

    expect(results).toHaveLength(1);
    expect(results[0].status).toBe('sent');
  });

  it('should return empty array when no pending', async () => {
    const providers = makeProviders();
    const store = makeMockStore();

    const results = await processPendingNotifications('email', { providers, store });

    expect(results).toHaveLength(0);
  });
});
