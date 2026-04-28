import {
  transformPipeline,
  formatPhoneE164,
  validateEmail,
  validatePhone,
  validateSignupDate,
  validateRecord,
  transformRecord,
  PlanService,
  RawCustomerRecord,
  PlanDetails,
} from '../pipeline';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makePlanService(
  plans: Record<string, PlanDetails> = {},
): PlanService & { lookupPlans: jest.Mock } {
  return {
    lookupPlans: jest.fn().mockResolvedValue(plans),
  };
}

const SAMPLE_PLANS: Record<string, PlanDetails> = {
  pro: { planName: 'Pro', monthlyPrice: 29.99, features: ['analytics', 'api-access'] },
  starter: { planName: 'Starter', monthlyPrice: 9.99, features: ['basic-dashboard'] },
};

function makeRecord(overrides: Partial<RawCustomerRecord> = {}): RawCustomerRecord {
  return {
    name: 'Jane Doe',
    email: 'jane@example.com',
    phone: '(555) 123-4567',
    address: { street: '123 Main St', city: 'Springfield', state: 'IL', zip: '62701' },
    signupDate: '2025-06-15T00:00:00Z',
    plan: 'pro',
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// validateEmail
// ---------------------------------------------------------------------------

describe('validateEmail', () => {
  it('accepts a standard email', () => {
    expect(validateEmail('user@example.com')).toBe(true);
  });

  it('rejects email without @', () => {
    expect(validateEmail('userexample.com')).toBe(false);
  });

  it('rejects email without domain', () => {
    expect(validateEmail('user@')).toBe(false);
  });

  it('rejects empty string', () => {
    expect(validateEmail('')).toBe(false);
  });

  it('rejects email with spaces', () => {
    expect(validateEmail('user @example.com')).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// validatePhone
// ---------------------------------------------------------------------------

describe('validatePhone', () => {
  it('accepts 10-digit number', () => {
    expect(validatePhone('5551234567')).toBe(true);
  });

  it('accepts formatted number with >= 10 digits', () => {
    expect(validatePhone('(555) 123-4567')).toBe(true);
  });

  it('rejects number with fewer than 10 digits', () => {
    expect(validatePhone('12345')).toBe(false);
  });

  it('accepts international number', () => {
    expect(validatePhone('+44 20 7946 0958')).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// validateSignupDate
// ---------------------------------------------------------------------------

describe('validateSignupDate', () => {
  it('accepts valid ISO date', () => {
    expect(validateSignupDate('2025-06-15T00:00:00Z')).toBe(true);
  });

  it('accepts date-only string', () => {
    expect(validateSignupDate('2025-01-01')).toBe(true);
  });

  it('rejects garbage string', () => {
    expect(validateSignupDate('not-a-date')).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// validateRecord
// ---------------------------------------------------------------------------

describe('validateRecord', () => {
  it('returns no errors for a fully valid record', () => {
    expect(validateRecord(makeRecord())).toEqual([]);
  });

  it('catches missing name', () => {
    const errors = validateRecord(makeRecord({ name: '' }));
    expect(errors).toContain('name is required');
  });

  it('catches undefined name', () => {
    const errors = validateRecord(makeRecord({ name: undefined }));
    expect(errors).toContain('name is required');
  });

  it('catches missing email', () => {
    const errors = validateRecord(makeRecord({ email: undefined }));
    expect(errors).toContain('email is required');
  });

  it('catches invalid email format', () => {
    const errors = validateRecord(makeRecord({ email: 'bad-email' }));
    expect(errors).toContain('email format is invalid');
  });

  it('catches short phone', () => {
    const errors = validateRecord(makeRecord({ phone: '12345' }));
    expect(errors).toContain('phone must have at least 10 digits');
  });

  it('allows missing phone (phone is optional)', () => {
    const errors = validateRecord(makeRecord({ phone: undefined }));
    expect(errors).toEqual([]);
  });

  it('catches missing signupDate', () => {
    const errors = validateRecord(makeRecord({ signupDate: undefined }));
    expect(errors).toContain('signupDate is required');
  });

  it('catches invalid signupDate', () => {
    const errors = validateRecord(makeRecord({ signupDate: 'not-a-date' }));
    expect(errors).toContain('signupDate is not a valid ISO date');
  });

  it('returns multiple errors at once', () => {
    const errors = validateRecord({ name: '', email: 'bad', signupDate: 'nope' });
    expect(errors.length).toBe(3);
  });
});

// ---------------------------------------------------------------------------
// formatPhoneE164
// ---------------------------------------------------------------------------

describe('formatPhoneE164', () => {
  it('formats 10-digit US number', () => {
    expect(formatPhoneE164('5551234567')).toBe('+15551234567');
  });

  it('formats number with formatting characters', () => {
    expect(formatPhoneE164('(555) 123-4567')).toBe('+15551234567');
  });

  it('handles 11-digit number starting with 1', () => {
    expect(formatPhoneE164('15551234567')).toBe('+15551234567');
  });

  it('handles international numbers (>10 digits)', () => {
    expect(formatPhoneE164('+44 20 7946 0958')).toBe('+442079460958');
  });

  it('passes through short numbers as digits only', () => {
    expect(formatPhoneE164('12345')).toBe('12345');
  });
});

// ---------------------------------------------------------------------------
// transformRecord
// ---------------------------------------------------------------------------

describe('transformRecord', () => {
  it('lowercases email', () => {
    const result = transformRecord(makeRecord({ email: 'JANE@EXAMPLE.COM' }));
    expect(result.email).toBe('jane@example.com');
  });

  it('formats phone to E.164', () => {
    const result = transformRecord(makeRecord({ phone: '(555) 123-4567' }));
    expect(result.phone).toBe('+15551234567');
  });

  it('parses signupDate to Date object', () => {
    const result = transformRecord(makeRecord({ signupDate: '2025-06-15T00:00:00Z' }));
    expect(result.signupDate).toBeInstanceOf(Date);
    expect(result.signupDate.toISOString()).toBe('2025-06-15T00:00:00.000Z');
  });

  it('trims name whitespace', () => {
    const result = transformRecord(makeRecord({ name: '  Jane Doe  ' }));
    expect(result.name).toBe('Jane Doe');
  });

  it('does not mutate the input record', () => {
    const record = makeRecord();
    const originalEmail = record.email;
    transformRecord(record);
    expect(record.email).toBe(originalEmail);
  });

  it('handles missing phone gracefully', () => {
    const result = transformRecord(makeRecord({ phone: undefined }));
    expect(result.phone).toBe('');
  });

  it('handles missing address', () => {
    const result = transformRecord(makeRecord({ address: undefined }));
    expect(result.address).toBeUndefined();
  });

  it('copies address without mutating original', () => {
    const record = makeRecord();
    const result = transformRecord(record);
    expect(result.address).toEqual(record.address);
    expect(result.address).not.toBe(record.address);
  });
});

// ---------------------------------------------------------------------------
// transformPipeline — happy path
// ---------------------------------------------------------------------------

describe('transformPipeline', () => {
  it('processes a single valid record with enrichment', async () => {
    const records = [makeRecord()];
    const service = makePlanService(SAMPLE_PLANS);

    const result = await transformPipeline({ records, planService: service });

    expect(result.valid).toHaveLength(1);
    expect(result.invalid).toHaveLength(0);
    expect(result.stats).toEqual({ total: 1, valid: 1, invalid: 0, enriched: 1 });

    const customer = result.valid[0];
    expect(customer.email).toBe('jane@example.com');
    expect(customer.phone).toBe('+15551234567');
    expect(customer.signupDate).toBeInstanceOf(Date);
    expect(customer.planName).toBe('Pro');
    expect(customer.monthlyPrice).toBe(29.99);
    expect(customer.features).toEqual(['analytics', 'api-access']);
  });

  it('processes multiple records with different plans', async () => {
    const records = [
      makeRecord({ email: 'alice@test.com', name: 'Alice', plan: 'pro' }),
      makeRecord({ email: 'bob@test.com', name: 'Bob', plan: 'starter' }),
      makeRecord({ email: 'carol@test.com', name: 'Carol', plan: 'starter' }),
    ];
    const service = makePlanService(SAMPLE_PLANS);

    const result = await transformPipeline({ records, planService: service });

    expect(result.valid).toHaveLength(3);
    expect(result.stats).toEqual({ total: 3, valid: 3, invalid: 0, enriched: 3 });
    expect(result.valid[0].planName).toBe('Pro');
    expect(result.valid[1].planName).toBe('Starter');
  });

  it('calls lookupPlans with unique plan IDs only', async () => {
    const records = [
      makeRecord({ email: 'a@test.com', plan: 'pro' }),
      makeRecord({ email: 'b@test.com', plan: 'pro' }),
      makeRecord({ email: 'c@test.com', plan: 'starter' }),
    ];
    const service = makePlanService(SAMPLE_PLANS);

    await transformPipeline({ records, planService: service });

    expect(service.lookupPlans).toHaveBeenCalledTimes(1);
    const calledWith = service.lookupPlans.mock.calls[0][0] as string[];
    expect(calledWith.sort()).toEqual(['pro', 'starter']);
  });

  it('does not call lookupPlans when no records have a plan', async () => {
    const records = [makeRecord({ email: 'a@test.com', plan: undefined })];
    const service = makePlanService(SAMPLE_PLANS);

    const result = await transformPipeline({ records, planService: service });

    expect(service.lookupPlans).not.toHaveBeenCalled();
    expect(result.stats.enriched).toBe(0);
    expect(result.valid[0].planName).toBe('');
  });

  it('does not mutate the input array', async () => {
    const records = [
      makeRecord({ email: 'b@test.com', signupDate: '2025-01-01T00:00:00Z' }),
      makeRecord({ email: 'a@test.com', signupDate: '2024-01-01T00:00:00Z' }),
    ];
    const originalFirst = records[0];
    const service = makePlanService(SAMPLE_PLANS);

    await transformPipeline({ records, planService: service });

    expect(records[0]).toBe(originalFirst);
  });
});

// ---------------------------------------------------------------------------
// transformPipeline — validation & invalid records
// ---------------------------------------------------------------------------

describe('transformPipeline — invalid records', () => {
  it('rejects record with missing name', async () => {
    const records = [makeRecord({ name: '' })];
    const service = makePlanService(SAMPLE_PLANS);

    const result = await transformPipeline({ records, planService: service });

    expect(result.valid).toHaveLength(0);
    expect(result.invalid).toHaveLength(1);
    expect(result.invalid[0].errors).toContain('name is required');
    expect(result.stats).toEqual({ total: 1, valid: 0, invalid: 1, enriched: 0 });
  });

  it('rejects record with invalid email', async () => {
    const records = [makeRecord({ email: 'not-an-email' })];
    const service = makePlanService(SAMPLE_PLANS);

    const result = await transformPipeline({ records, planService: service });

    expect(result.invalid).toHaveLength(1);
    expect(result.invalid[0].errors).toContain('email format is invalid');
  });

  it('rejects record with short phone', async () => {
    const records = [makeRecord({ phone: '12345' })];
    const service = makePlanService(SAMPLE_PLANS);

    const result = await transformPipeline({ records, planService: service });

    expect(result.invalid).toHaveLength(1);
    expect(result.invalid[0].errors).toContain('phone must have at least 10 digits');
  });

  it('rejects record with invalid signupDate', async () => {
    const records = [makeRecord({ signupDate: 'garbage' })];
    const service = makePlanService(SAMPLE_PLANS);

    const result = await transformPipeline({ records, planService: service });

    expect(result.invalid).toHaveLength(1);
    expect(result.invalid[0].errors).toContain('signupDate is not a valid ISO date');
  });

  it('collects multiple errors on one record', async () => {
    const records = [makeRecord({ name: '', email: 'bad', signupDate: 'nope' })];
    const service = makePlanService(SAMPLE_PLANS);

    const result = await transformPipeline({ records, planService: service });

    expect(result.invalid).toHaveLength(1);
    expect(result.invalid[0].errors.length).toBeGreaterThanOrEqual(3);
  });

  it('mixes valid and invalid records correctly', async () => {
    const records = [
      makeRecord({ email: 'good@test.com' }),
      makeRecord({ name: '', email: 'bad-name@test.com' }),
      makeRecord({ email: 'also-good@test.com' }),
    ];
    const service = makePlanService(SAMPLE_PLANS);

    const result = await transformPipeline({ records, planService: service });

    expect(result.valid).toHaveLength(2);
    expect(result.invalid).toHaveLength(1);
    expect(result.stats).toEqual({ total: 3, valid: 2, invalid: 1, enriched: 2 });
  });
});

// ---------------------------------------------------------------------------
// transformPipeline — duplicate email handling
// ---------------------------------------------------------------------------

describe('transformPipeline — duplicate emails', () => {
  it('keeps the first record and rejects the duplicate', async () => {
    const records = [
      makeRecord({ email: 'dupe@test.com', name: 'First' }),
      makeRecord({ email: 'DUPE@test.com', name: 'Second' }),
    ];
    const service = makePlanService(SAMPLE_PLANS);

    const result = await transformPipeline({ records, planService: service });

    expect(result.valid).toHaveLength(1);
    expect(result.valid[0].name).toBe('First');
    expect(result.invalid).toHaveLength(1);
    expect(result.invalid[0].errors).toContain('duplicate email');
  });

  it('handles triple duplicates', async () => {
    const records = [
      makeRecord({ email: 'x@test.com', name: 'A' }),
      makeRecord({ email: 'x@test.com', name: 'B' }),
      makeRecord({ email: 'x@test.com', name: 'C' }),
    ];
    const service = makePlanService(SAMPLE_PLANS);

    const result = await transformPipeline({ records, planService: service });

    expect(result.valid).toHaveLength(1);
    expect(result.invalid).toHaveLength(2);
  });
});

// ---------------------------------------------------------------------------
// transformPipeline — enrichment edge cases
// ---------------------------------------------------------------------------

describe('transformPipeline — enrichment', () => {
  it('leaves default enrichment fields when plan is unknown', async () => {
    const records = [makeRecord({ plan: 'unknown-plan' })];
    const service = makePlanService(SAMPLE_PLANS);

    const result = await transformPipeline({ records, planService: service });

    expect(result.valid).toHaveLength(1);
    expect(result.valid[0].planName).toBe('');
    expect(result.valid[0].monthlyPrice).toBe(0);
    expect(result.valid[0].features).toEqual([]);
    expect(result.stats.enriched).toBe(0);
  });

  it('propagates plan service errors', async () => {
    const records = [makeRecord()];
    const service: PlanService = {
      lookupPlans: jest.fn().mockRejectedValue(new Error('service down')),
    };

    await expect(
      transformPipeline({ records, planService: service }),
    ).rejects.toThrow('service down');
  });

  it('handles delayed plan service correctly', async () => {
    const delayedService: PlanService = {
      lookupPlans: jest.fn().mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve(SAMPLE_PLANS), 50)),
      ),
    };
    const records = [makeRecord()];

    const result = await transformPipeline({ records, planService: delayedService });

    expect(result.valid[0].planName).toBe('Pro');
    expect(result.stats.enriched).toBe(1);
  });

  it('does not share feature array references across customers with same plan', async () => {
    const records = [
      makeRecord({ email: 'a@test.com', plan: 'pro' }),
      makeRecord({ email: 'b@test.com', plan: 'pro' }),
    ];
    const service = makePlanService(SAMPLE_PLANS);

    const result = await transformPipeline({ records, planService: service });

    expect(result.valid[0].features).toEqual(result.valid[1].features);
    expect(result.valid[0].features).not.toBe(result.valid[1].features);
  });
});

// ---------------------------------------------------------------------------
// transformPipeline — maxRecords guard
// ---------------------------------------------------------------------------

describe('transformPipeline — maxRecords', () => {
  it('throws when input exceeds default 10_000 limit', async () => {
    const records = Array.from({ length: 10_001 }, (_, i) =>
      makeRecord({ email: `user${i}@test.com` }),
    );
    const service = makePlanService();

    await expect(
      transformPipeline({ records, planService: service }),
    ).rejects.toThrow('Input exceeds maximum of 10000 records');
  });

  it('accepts exactly 10_000 records', async () => {
    const records = Array.from({ length: 10_000 }, (_, i) =>
      makeRecord({ email: `user${i}@test.com` }),
    );
    const service = makePlanService(SAMPLE_PLANS);

    const result = await transformPipeline({ records, planService: service });

    expect(result.stats.total).toBe(10_000);
  });

  it('respects custom maxRecords option', async () => {
    const records = [makeRecord(), makeRecord({ email: 'b@test.com' }), makeRecord({ email: 'c@test.com' })];
    const service = makePlanService();

    await expect(
      transformPipeline({ records, planService: service }, { maxRecords: 2 }),
    ).rejects.toThrow('Input exceeds maximum of 2 records');
  });
});

// ---------------------------------------------------------------------------
// transformPipeline — stats accuracy
// ---------------------------------------------------------------------------

describe('transformPipeline — stats accuracy', () => {
  it('stats.total + breakdown accounts for all records', async () => {
    const records = [
      makeRecord({ email: 'good@test.com' }),
      makeRecord({ name: '' }),
      makeRecord({ email: 'also-good@test.com', plan: undefined }),
    ];
    const service = makePlanService(SAMPLE_PLANS);

    const result = await transformPipeline({ records, planService: service });

    expect(result.stats.total).toBe(3);
    expect(result.stats.valid + result.stats.invalid).toBe(result.stats.total);
    expect(result.stats.enriched).toBeLessThanOrEqual(result.stats.valid);
  });

  it('returns zero stats for empty input', async () => {
    const service = makePlanService();

    const result = await transformPipeline({ records: [], planService: service });

    expect(result.stats).toEqual({ total: 0, valid: 0, invalid: 0, enriched: 0 });
    expect(result.valid).toEqual([]);
    expect(result.invalid).toEqual([]);
  });
});
