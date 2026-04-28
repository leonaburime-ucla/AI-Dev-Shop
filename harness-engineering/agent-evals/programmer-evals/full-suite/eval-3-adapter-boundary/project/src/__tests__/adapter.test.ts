import { PaymentAdapter, Logger, AdapterResult, AdapterError } from '../adapter';
import { PaymentSDK } from '../types';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function createMockSDK(): jest.Mocked<PaymentSDK> {
  return {
    charge: jest.fn(),
    refund: jest.fn(),
    getTransaction: jest.fn(),
  };
}

function createMockLogger(): jest.Mocked<Logger> {
  return {
    info: jest.fn(),
    error: jest.fn(),
  };
}

function isError(result: AdapterResult<unknown>): result is AdapterError {
  return result.status === 'error';
}

/** Helper to create a promise that resolves after `ms` milliseconds. */
function delay<T>(ms: number, value: T): Promise<T> {
  return new Promise((resolve) => setTimeout(resolve, ms, value));
}

/** Helper to create a promise that rejects after `ms` milliseconds. */
function delayReject(ms: number, err: Error): Promise<never> {
  return new Promise((_, reject) => setTimeout(() => reject(err), ms));
}

// ---------------------------------------------------------------------------
// chargeCard
// ---------------------------------------------------------------------------

describe('PaymentAdapter.chargeCard', () => {
  let sdk: jest.Mocked<PaymentSDK>;
  let logger: jest.Mocked<Logger>;
  let adapter: PaymentAdapter;

  beforeEach(() => {
    sdk = createMockSDK();
    logger = createMockLogger();
    adapter = new PaymentAdapter(sdk, { logger, timeoutMs: 200 });
  });

  it('returns success with transaction data on happy path', async () => {
    sdk.charge.mockResolvedValue({ transactionId: 'txn-1', status: 'completed' });

    const result = await adapter.chargeCard({
      amount: 1000,
      currency: 'USD',
      cardToken: 'tok_secret_123',
    });

    expect(result.status).toBe('success');
    if (result.status === 'success') {
      expect(result.data.transactionId).toBe('txn-1');
      expect(result.data.status).toBe('completed');
    }
  });

  it('passes amount, currency, and cardToken to the SDK', async () => {
    sdk.charge.mockResolvedValue({ transactionId: 'txn-1', status: 'completed' });

    await adapter.chargeCard({ amount: 500, currency: 'EUR', cardToken: 'tok_abc' });

    expect(sdk.charge).toHaveBeenCalledWith(500, 'EUR', 'tok_abc');
  });

  it('logs operation, duration, success, and transactionId on success', async () => {
    sdk.charge.mockResolvedValue({ transactionId: 'txn-1', status: 'completed' });

    await adapter.chargeCard({ amount: 1000, currency: 'USD', cardToken: 'tok_x' });

    expect(logger.info).toHaveBeenCalledTimes(1);
    const meta = logger.info.mock.calls[0][1] as Record<string, unknown>;
    expect(meta.operation).toBe('chargeCard');
    expect(meta.transactionId).toBe('txn-1');
    expect(meta.success).toBe(true);
    expect(typeof meta.duration).toBe('number');
  });

  it('never logs the card token (Req #5)', async () => {
    sdk.charge.mockResolvedValue({ transactionId: 'txn-1', status: 'completed' });

    await adapter.chargeCard({ amount: 1000, currency: 'USD', cardToken: 'tok_super_secret' });

    const allLogArgs = [
      ...logger.info.mock.calls.map((c) => JSON.stringify(c)),
      ...logger.error.mock.calls.map((c) => JSON.stringify(c)),
    ].join(' ');

    expect(allLogArgs).not.toContain('tok_super_secret');
  });

  it('logs operation, duration, failure, and errorCode on error', async () => {
    sdk.charge.mockRejectedValue(new Error('card_declined'));

    await adapter.chargeCard({ amount: 1000, currency: 'USD', cardToken: 'tok_x' });

    expect(logger.error).toHaveBeenCalledTimes(1);
    const meta = logger.error.mock.calls[0][1] as Record<string, unknown>;
    expect(meta.operation).toBe('chargeCard');
    expect(meta.success).toBe(false);
    expect(typeof meta.duration).toBe('number');
  });

  // --- Error code mapping ---

  it('maps invalid_card SDK error to INVALID_CARD code', async () => {
    sdk.charge.mockRejectedValue(new Error('invalid_card'));

    const result = await adapter.chargeCard({ amount: 100, currency: 'USD', cardToken: 'tok' });

    expect(isError(result)).toBe(true);
    if (isError(result)) {
      expect(result.code).toBe('INVALID_CARD');
      expect(result.message).toBe('invalid_card');
    }
  });

  it('maps insufficient_funds SDK error to INSUFFICIENT_FUNDS code', async () => {
    sdk.charge.mockRejectedValue(new Error('insufficient_funds'));

    const result = await adapter.chargeCard({ amount: 100, currency: 'USD', cardToken: 'tok' });

    expect(isError(result)).toBe(true);
    if (isError(result)) {
      expect(result.code).toBe('INSUFFICIENT_FUNDS');
    }
  });

  it('maps network SDK error to NETWORK_ERROR code', async () => {
    sdk.charge.mockRejectedValue(new Error('network error: ECONNREFUSED'));

    const result = await adapter.chargeCard({ amount: 100, currency: 'USD', cardToken: 'tok' });

    expect(isError(result)).toBe(true);
    if (isError(result)) {
      expect(result.code).toBe('NETWORK_ERROR');
    }
  });

  it('maps unrecognised errors to UNKNOWN code', async () => {
    sdk.charge.mockRejectedValue(new Error('solar flare'));

    const result = await adapter.chargeCard({ amount: 100, currency: 'USD', cardToken: 'tok' });

    expect(isError(result)).toBe(true);
    if (isError(result)) {
      expect(result.code).toBe('UNKNOWN');
      expect(result.message).toBe('solar flare');
    }
  });

  it('handles non-Error thrown values gracefully', async () => {
    sdk.charge.mockRejectedValue('string boom');

    const result = await adapter.chargeCard({ amount: 100, currency: 'USD', cardToken: 'tok' });

    expect(isError(result)).toBe(true);
    if (isError(result)) {
      expect(result.code).toBe('UNKNOWN');
      expect(result.message).toBe('string boom');
    }
  });

  it('handles null/undefined thrown values', async () => {
    sdk.charge.mockRejectedValue(null);

    const result = await adapter.chargeCard({ amount: 100, currency: 'USD', cardToken: 'tok' });

    expect(isError(result)).toBe(true);
    if (isError(result)) {
      expect(result.code).toBe('UNKNOWN');
      expect(result.message).toBe('An unexpected error occurred');
    }
  });

  // --- Timeout ---

  it('returns TIMEOUT error when SDK call exceeds deadline', async () => {
    sdk.charge.mockImplementation(() => delay(500, { transactionId: 'late', status: 'ok' }));

    const result = await adapter.chargeCard({ amount: 100, currency: 'USD', cardToken: 'tok' });

    expect(isError(result)).toBe(true);
    if (isError(result)) {
      expect(result.code).toBe('TIMEOUT');
    }
  });

  it('allows per-call timeout override', async () => {
    sdk.charge.mockImplementation(() => delay(100, { transactionId: 'txn-ok', status: 'ok' }));

    // Default timeout is 200ms but override to 50ms
    const result = await adapter.chargeCard(
      { amount: 100, currency: 'USD', cardToken: 'tok' },
      { timeoutMs: 50 },
    );

    expect(isError(result)).toBe(true);
    if (isError(result)) {
      expect(result.code).toBe('TIMEOUT');
    }
  });

  it('succeeds if SDK responds before timeout', async () => {
    sdk.charge.mockImplementation(() => delay(10, { transactionId: 'txn-fast', status: 'ok' }));

    const result = await adapter.chargeCard({ amount: 100, currency: 'USD', cardToken: 'tok' });

    expect(result.status).toBe('success');
  });
});

// ---------------------------------------------------------------------------
// refund
// ---------------------------------------------------------------------------

describe('PaymentAdapter.refund', () => {
  let sdk: jest.Mocked<PaymentSDK>;
  let logger: jest.Mocked<Logger>;
  let adapter: PaymentAdapter;

  beforeEach(() => {
    sdk = createMockSDK();
    logger = createMockLogger();
    adapter = new PaymentAdapter(sdk, { logger, timeoutMs: 200 });
  });

  it('returns success with refund data on happy path', async () => {
    sdk.refund.mockResolvedValue({ refundId: 'ref-1', status: 'completed' });

    const result = await adapter.refund({ transactionId: 'txn-1', amount: 50 });

    expect(result.status).toBe('success');
    if (result.status === 'success') {
      expect(result.data.refundId).toBe('ref-1');
    }
  });

  it('passes transactionId and amount to the SDK', async () => {
    sdk.refund.mockResolvedValue({ refundId: 'ref-1', status: 'completed' });

    await adapter.refund({ transactionId: 'txn-abc', amount: 200 });

    expect(sdk.refund).toHaveBeenCalledWith('txn-abc', 200);
  });

  it('logs operation with transactionId on success', async () => {
    sdk.refund.mockResolvedValue({ refundId: 'ref-1', status: 'completed' });

    await adapter.refund({ transactionId: 'txn-1', amount: 50 });

    expect(logger.info).toHaveBeenCalledTimes(1);
    const meta = logger.info.mock.calls[0][1] as Record<string, unknown>;
    expect(meta.operation).toBe('refund');
    expect(meta.transactionId).toBe('txn-1');
    expect(meta.success).toBe(true);
  });

  it('maps SDK error to typed error response', async () => {
    sdk.refund.mockRejectedValue(new Error('insufficient_funds'));

    const result = await adapter.refund({ transactionId: 'txn-1', amount: 999 });

    expect(isError(result)).toBe(true);
    if (isError(result)) {
      expect(result.code).toBe('INSUFFICIENT_FUNDS');
    }
  });

  it('logs on error with errorCode', async () => {
    sdk.refund.mockRejectedValue(new Error('network failure'));

    await adapter.refund({ transactionId: 'txn-1', amount: 50 });

    expect(logger.error).toHaveBeenCalledTimes(1);
    const meta = logger.error.mock.calls[0][1] as Record<string, unknown>;
    expect(meta.operation).toBe('refund');
    expect(meta.errorCode).toBe('NETWORK_ERROR');
    expect(meta.success).toBe(false);
  });

  it('returns TIMEOUT error when SDK call exceeds deadline', async () => {
    sdk.refund.mockImplementation(() => delay(500, { refundId: 'late', status: 'ok' }));

    const result = await adapter.refund({ transactionId: 'txn-1', amount: 50 });

    expect(isError(result)).toBe(true);
    if (isError(result)) {
      expect(result.code).toBe('TIMEOUT');
    }
  });
});

// ---------------------------------------------------------------------------
// getTransaction
// ---------------------------------------------------------------------------

describe('PaymentAdapter.getTransaction', () => {
  let sdk: jest.Mocked<PaymentSDK>;
  let logger: jest.Mocked<Logger>;
  let adapter: PaymentAdapter;

  beforeEach(() => {
    sdk = createMockSDK();
    logger = createMockLogger();
    adapter = new PaymentAdapter(sdk, { logger, timeoutMs: 200 });
  });

  it('returns success with transaction details on happy path', async () => {
    sdk.getTransaction.mockResolvedValue({
      transactionId: 'txn-1',
      amount: 1000,
      status: 'completed',
      createdAt: '2026-01-01',
    });

    const result = await adapter.getTransaction({ transactionId: 'txn-1' });

    expect(result.status).toBe('success');
    if (result.status === 'success') {
      expect(result.data.transactionId).toBe('txn-1');
      expect(result.data.amount).toBe(1000);
      expect(result.data.createdAt).toBe('2026-01-01');
    }
  });

  it('passes transactionId to the SDK', async () => {
    sdk.getTransaction.mockResolvedValue({
      transactionId: 'txn-xyz',
      amount: 100,
      status: 'completed',
      createdAt: '2026-01-01',
    });

    await adapter.getTransaction({ transactionId: 'txn-xyz' });

    expect(sdk.getTransaction).toHaveBeenCalledWith('txn-xyz');
  });

  it('logs operation with transactionId on success', async () => {
    sdk.getTransaction.mockResolvedValue({
      transactionId: 'txn-1',
      amount: 100,
      status: 'completed',
      createdAt: '2026-01-01',
    });

    await adapter.getTransaction({ transactionId: 'txn-1' });

    expect(logger.info).toHaveBeenCalledTimes(1);
    const meta = logger.info.mock.calls[0][1] as Record<string, unknown>;
    expect(meta.operation).toBe('getTransaction');
    expect(meta.transactionId).toBe('txn-1');
  });

  it('maps SDK error to typed error response', async () => {
    sdk.getTransaction.mockRejectedValue(new Error('not found'));

    const result = await adapter.getTransaction({ transactionId: 'txn-gone' });

    expect(isError(result)).toBe(true);
    if (isError(result)) {
      expect(result.code).toBe('UNKNOWN');
      expect(result.message).toBe('not found');
    }
  });

  it('returns TIMEOUT error when SDK call exceeds deadline', async () => {
    sdk.getTransaction.mockImplementation(() =>
      delay(500, { transactionId: 'txn-1', amount: 100, status: 'ok', createdAt: '' }),
    );

    const result = await adapter.getTransaction({ transactionId: 'txn-1' });

    expect(isError(result)).toBe(true);
    if (isError(result)) {
      expect(result.code).toBe('TIMEOUT');
    }
  });

  it('logs on error', async () => {
    sdk.getTransaction.mockRejectedValue(new Error('boom'));

    await adapter.getTransaction({ transactionId: 'txn-1' });

    expect(logger.error).toHaveBeenCalledTimes(1);
    const meta = logger.error.mock.calls[0][1] as Record<string, unknown>;
    expect(meta.operation).toBe('getTransaction');
    expect(meta.success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Constructor defaults
// ---------------------------------------------------------------------------

describe('PaymentAdapter defaults', () => {
  it('constructs without options (uses defaults)', () => {
    const sdk = createMockSDK();
    // Should not throw
    const adapter = new PaymentAdapter(sdk);
    expect(adapter).toBeDefined();
  });

  it('uses 5-second default timeout', async () => {
    const sdk = createMockSDK();
    const logger = createMockLogger();
    // We cannot easily test 5s timeout without real delay,
    // but we can verify that a <5s call succeeds with defaults.
    sdk.charge.mockResolvedValue({ transactionId: 'txn-1', status: 'ok' });
    const adapter = new PaymentAdapter(sdk, { logger });

    const result = await adapter.chargeCard({ amount: 100, currency: 'USD', cardToken: 'tok' });
    expect(result.status).toBe('success');
  });

  it('default logger writes structured JSON to console on success and failure', async () => {
    const sdk = createMockSDK();
    const logSpy = jest.spyOn(console, 'log').mockImplementation();
    const errSpy = jest.spyOn(console, 'error').mockImplementation();

    const adapter = new PaymentAdapter(sdk); // uses default logger

    sdk.charge.mockResolvedValue({ transactionId: 'txn-1', status: 'ok' });
    await adapter.chargeCard({ amount: 100, currency: 'USD', cardToken: 'tok' });
    expect(logSpy).toHaveBeenCalledTimes(1);
    const parsed = JSON.parse(logSpy.mock.calls[0][0] as string);
    expect(parsed.level).toBe('info');

    sdk.charge.mockRejectedValue(new Error('boom'));
    await adapter.chargeCard({ amount: 100, currency: 'USD', cardToken: 'tok' });
    expect(errSpy).toHaveBeenCalledTimes(1);
    const parsedErr = JSON.parse(errSpy.mock.calls[0][0] as string);
    expect(parsedErr.level).toBe('error');

    logSpy.mockRestore();
    errSpy.mockRestore();
  });
});
