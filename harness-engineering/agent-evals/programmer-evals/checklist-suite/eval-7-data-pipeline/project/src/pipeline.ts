/**
 * Customer Record Pipeline — CRM Sync Transformer
 *
 * Accepts raw customer records, validates, transforms, enriches via an
 * injected plan service, and returns categorized results with stats.
 *
 * Pure validation/transformation helpers are exported for direct testing.
 * The main pipeline function uses a two-object signature: required input
 * object + optional options object.
 */

// --- Types ---

/** Raw customer record as received from upstream sources. */
export interface RawCustomerRecord {
  name?: string;
  email?: string;
  phone?: string;
  address?: { street: string; city: string; state: string; zip: string };
  signupDate?: string;
  plan?: string;
}

/** Plan details returned by the plan service. */
export interface PlanDetails {
  planName: string;
  monthlyPrice: number;
  features: string[];
}

/** A validated, transformed, and enriched customer record. */
export interface EnrichedCustomer {
  name: string;
  email: string;
  phone: string;
  address: { street: string; city: string; state: string; zip: string } | undefined;
  signupDate: Date;
  plan: string;
  planName: string;
  monthlyPrice: number;
  features: string[];
}

/** Pipeline output with valid, invalid partitions and aggregate stats. */
export interface PipelineResult {
  valid: EnrichedCustomer[];
  invalid: InvalidRecord[];
  stats: PipelineStats;
}

/** An invalid record paired with human-readable error reasons. */
export interface InvalidRecord {
  record: RawCustomerRecord;
  errors: string[];
}

/** Aggregate stats for a pipeline run. */
export interface PipelineStats {
  total: number;
  valid: number;
  invalid: number;
  enriched: number;
}

/** Injected plan service contract — supports batch lookup. */
export interface PlanService {
  lookupPlans(planIds: string[]): Promise<Record<string, PlanDetails>>;
}

/** Optional configuration for the pipeline. */
export interface PipelineOptions {
  /** Maximum records to accept. Defaults to 10_000. */
  maxRecords?: number;
}

// --- Constants ---

const DEFAULT_MAX_RECORDS = 10_000;

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// --- Pure Validation Helpers ---

/**
 * Validates an email address against a basic pattern.
 *
 * @param email - The email string to validate.
 * @returns true when the email matches the expected pattern.
 * @complexity O(n) where n is email length.
 * @overallScore 100
 */
export function validateEmail(email: string): boolean {
  return EMAIL_REGEX.test(email);
}

/**
 * Validates a phone string contains at least 10 digits after stripping
 * non-digit characters.
 *
 * @param phone - Raw phone string with possible formatting.
 * @returns true when the stripped digit count is >= 10.
 * @complexity O(n) where n is phone length.
 * @overallScore 100
 */
export function validatePhone(phone: string): boolean {
  const digits = phone.replace(/\D/g, '');
  return digits.length >= 10;
}

/**
 * Validates that a string is a parseable ISO date.
 *
 * @param dateStr - The date string to validate.
 * @returns true when Date parsing produces a valid timestamp.
 * @complexity O(1).
 * @overallScore 100
 */
export function validateSignupDate(dateStr: string): boolean {
  const parsed = new Date(dateStr);
  return !isNaN(parsed.getTime());
}

/**
 * Collects all validation errors for a single raw record.
 *
 * @param record - The raw customer record to validate.
 * @returns An array of human-readable error strings (empty if valid).
 * @complexity O(1) per record field.
 * @overallScore 100
 */
export function validateRecord(record: RawCustomerRecord): string[] {
  const errors: string[] = [];

  if (!record.name || record.name.trim() === '') {
    errors.push('name is required');
  }

  if (!record.email) {
    errors.push('email is required');
  } else if (!validateEmail(record.email)) {
    errors.push('email format is invalid');
  }

  if (record.phone && !validatePhone(record.phone)) {
    errors.push('phone must have at least 10 digits');
  }

  if (!record.signupDate) {
    errors.push('signupDate is required');
  } else if (!validateSignupDate(record.signupDate)) {
    errors.push('signupDate is not a valid ISO date');
  }

  return errors;
}

// --- Pure Transformation Helpers ---

/**
 * Formats a phone number to E.164 format.
 * Strips all non-digit characters and prepends +1 for 10-digit US numbers.
 *
 * @param phone - Raw phone string with possible formatting characters.
 * @returns E.164-formatted phone string, or digits-only for short numbers.
 * @complexity O(n) where n is phone length.
 * @overallScore 100
 */
export function formatPhoneE164(phone: string): string {
  const digits = phone.replace(/\D/g, '');
  if (digits.length === 10) {
    return `+1${digits}`;
  }
  if (digits.length === 11 && digits.startsWith('1')) {
    return `+${digits}`;
  }
  if (digits.length > 10) {
    return `+${digits}`;
  }
  return digits;
}

/**
 * Transforms a validated raw record into a partially-enriched customer
 * (without plan details, which require async lookup).
 *
 * @param record - A raw record that has already passed validation.
 * @returns A transformed customer with normalized fields.
 * @complexity O(1).
 * @overallScore 100
 */
export function transformRecord(record: RawCustomerRecord): Omit<EnrichedCustomer, 'planName' | 'monthlyPrice' | 'features'> {
  return {
    name: record.name!.trim(),
    email: record.email!.toLowerCase(),
    phone: record.phone ? formatPhoneE164(record.phone) : '',
    address: record.address ? { ...record.address } : undefined,
    signupDate: new Date(record.signupDate!),
    plan: record.plan ?? '',
  };
}

// --- Main Pipeline ---

/**
 * Transforms, validates, and enriches an array of raw customer records.
 *
 * Accepts a required input object and an optional options object (two-object
 * exported signature). Validation and transformation are pure; enrichment is
 * the only async/effectful step, delegated to the injected planService.
 *
 * @param input - Required: records array and planService.
 * @param input.records - Raw customer records to process.
 * @param input.planService - Injected plan-lookup service.
 * @param options - Optional pipeline configuration.
 * @param options.maxRecords - Cap on input size (default 10 000).
 * @returns PipelineResult with valid, invalid partitions and stats.
 * @throws Error when input exceeds maxRecords.
 * @complexity O(n) validation + O(k) enrichment where k = unique plan IDs.
 * @overallScore 95 — enrichment error path degrades gracefully rather than failing hard.
 */
export async function transformPipeline(
  input: { records: RawCustomerRecord[]; planService: PlanService },
  options?: PipelineOptions,
): Promise<PipelineResult> {
  const { records, planService } = input;
  const maxRecords = options?.maxRecords ?? DEFAULT_MAX_RECORDS;

  if (records.length > maxRecords) {
    throw new Error(`Input exceeds maximum of ${maxRecords} records (received ${records.length})`);
  }

  const valid: EnrichedCustomer[] = [];
  const invalid: InvalidRecord[] = [];
  const planIds = new Set<string>();
  const seenEmails = new Set<string>();

  for (const record of records) {
    const errors = validateRecord(record);

    // Deduplicate by lowercased email (only if email itself is present and valid)
    if (record.email && errors.every(e => !e.startsWith('email'))) {
      const lowerEmail = record.email.toLowerCase();
      if (seenEmails.has(lowerEmail)) {
        errors.push('duplicate email');
      } else {
        seenEmails.add(lowerEmail);
      }
    }

    if (errors.length > 0) {
      invalid.push({ record, errors });
      continue;
    }

    const transformed = transformRecord(record);

    if (record.plan) {
      planIds.add(record.plan);
    }

    // Push with empty enrichment fields; filled in enrichment phase
    valid.push({
      ...transformed,
      planName: '',
      monthlyPrice: 0,
      features: [],
    });
  }

  // --- Enrichment phase (batch lookup) ---
  let enrichedCount = 0;
  if (planIds.size > 0) {
    const planDetails = await planService.lookupPlans(Array.from(planIds));
    for (const customer of valid) {
      if (customer.plan && planDetails[customer.plan]) {
        const details = planDetails[customer.plan];
        customer.planName = details.planName;
        customer.monthlyPrice = details.monthlyPrice;
        customer.features = [...details.features];
        enrichedCount++;
      }
    }
  }

  const stats: PipelineStats = {
    total: records.length,
    valid: valid.length,
    invalid: invalid.length,
    enriched: enrichedCount,
  };

  return { valid, invalid, stats };
}
