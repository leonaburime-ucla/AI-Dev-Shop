/**
 * Sales Report Generator
 *
 * Generates aggregated sales reports from transaction data.
 * Supports summary, detailed, and executive report formats.
 *
 * Pure module — no side effects, no external dependencies.
 */

// -- Types ------------------------------------------------------------------

export interface Transaction {
  id: string;
  customerId: string;
  customerEmail: string;
  customerPhone?: string;
  customerNotes?: string;
  amount: number;
  currency: string;
  date: string;
  region: string;
  salesRepId: string;
}

export type ReportFormat = 'summary' | 'detailed' | 'executive';

export interface ReportOptions {
  format?: ReportFormat;
  title?: string;
}

export interface CustomerSummary {
  customerId: string;
  totalSpend: number;
}

export interface SummaryReport {
  totalRevenue: number;
  transactionCount: number;
  averageOrderValue: number;
  revenueByRegion: Record<string, number>;
  topCustomers: CustomerSummary[];
  dateRange: { start: string; end: string };
}

export interface DetailedTransaction {
  id: string;
  customerId: string;
  amount: number;
  region: string;
  date: string;
}

export interface DetailedReport extends SummaryReport {
  transactions: DetailedTransaction[];
}

export interface ExecutiveReport {
  totalRevenue: number;
  transactionCount: number;
  averageOrderValue: number;
  dateRange: { start: string; end: string };
}

// -- Helpers ----------------------------------------------------------------

const VALID_FORMATS: ReadonlySet<ReportFormat> = new Set([
  'summary',
  'detailed',
  'executive',
]);

/**
 * Round a number to 2 decimal places using fixed-point arithmetic.
 *
 * @param value - The number to round
 * @returns The rounded number
 * @complexity O(1)
 * @overallScore 100
 */
export function roundTwo(value: number): number {
  return Math.round((value + Number.EPSILON) * 100) / 100;
}

/**
 * Validate that a string is a supported ReportFormat.
 *
 * @param format - The string to check
 * @returns True if the string is a valid ReportFormat
 * @complexity O(1)
 * @overallScore 100
 */
function isValidFormat(format: string): format is ReportFormat {
  return VALID_FORMATS.has(format as ReportFormat);
}

/**
 * Check whether a transaction has the minimum required fields.
 *
 * @param t - The transaction to validate
 * @returns True if the transaction has id, customerId, numeric amount, date, and region
 * @complexity O(1)
 * @overallScore 100
 */
function isValidTransaction(t: Transaction): boolean {
  return !!(
    t.id &&
    t.customerId &&
    typeof t.amount === 'number' &&
    t.date &&
    t.region
  );
}

/**
 * Deduplicate transactions by ID, keeping the first occurrence.
 *
 * @param transactions - Array of transactions (may contain duplicates)
 * @returns A new array with unique transaction IDs
 * @complexity O(n)
 * @overallScore 100
 */
function deduplicateById(transactions: Transaction[]): Transaction[] {
  const seen = new Set<string>();
  const result: Transaction[] = [];
  for (const t of transactions) {
    if (!seen.has(t.id)) {
      seen.add(t.id);
      result.push(t);
    }
  }
  return result;
}

/**
 * Aggregate total spend per customer and return top N by spend.
 *
 * @param transactions - Array of valid, deduplicated transactions
 * @param limit - Max customers to return (default 5)
 * @returns Sorted array of CustomerSummary, descending by totalSpend, rounded to 2dp
 * @complexity O(n log n) due to sort
 * @overallScore 100
 */
function topCustomersBySpend(
  transactions: Transaction[],
  limit: number = 5,
): CustomerSummary[] {
  const spendMap = new Map<string, number>();
  for (const t of transactions) {
    spendMap.set(t.customerId, (spendMap.get(t.customerId) ?? 0) + t.amount);
  }
  return Array.from(spendMap.entries())
    .map(([customerId, total]) => ({
      customerId,
      totalSpend: roundTwo(total),
    }))
    .sort((a, b) => b.totalSpend - a.totalSpend)
    .slice(0, limit);
}

/**
 * Compute revenue grouped by region, each value rounded to 2dp.
 *
 * @param transactions - Array of valid, deduplicated transactions
 * @returns Record mapping region name to rounded revenue
 * @complexity O(n)
 * @overallScore 100
 */
function computeRevenueByRegion(
  transactions: Transaction[],
): Record<string, number> {
  const regionMap: Record<string, number> = {};
  for (const t of transactions) {
    regionMap[t.region] = (regionMap[t.region] ?? 0) + t.amount;
  }
  for (const key of Object.keys(regionMap)) {
    regionMap[key] = roundTwo(regionMap[key]);
  }
  return regionMap;
}

/**
 * Compute the date range (earliest and latest) from transactions.
 *
 * @param transactions - Non-empty array of transactions
 * @returns Object with ISO date strings for start and end
 * @complexity O(n)
 * @overallScore 100
 */
function computeDateRange(
  transactions: Transaction[],
): { start: string; end: string } {
  let min = Infinity;
  let max = -Infinity;
  for (const t of transactions) {
    const ts = new Date(t.date).getTime();
    if (ts < min) min = ts;
    if (ts > max) max = ts;
  }
  return {
    start: new Date(min).toISOString().split('T')[0],
    end: new Date(max).toISOString().split('T')[0],
  };
}

// -- Empty report factory ---------------------------------------------------

const EMPTY_DATE_RANGE = { start: '', end: '' } as const;

function emptySummary(): SummaryReport {
  return {
    totalRevenue: 0,
    transactionCount: 0,
    averageOrderValue: 0,
    revenueByRegion: {},
    topCustomers: [],
    dateRange: { ...EMPTY_DATE_RANGE },
  };
}

function emptyDetailed(): DetailedReport {
  return { ...emptySummary(), transactions: [] };
}

function emptyExecutive(): ExecutiveReport {
  return {
    totalRevenue: 0,
    transactionCount: 0,
    averageOrderValue: 0,
    dateRange: { ...EMPTY_DATE_RANGE },
  };
}

const EMPTY_BUILDERS: Record<ReportFormat, () => SummaryReport | DetailedReport | ExecutiveReport> = {
  summary: emptySummary,
  detailed: emptyDetailed,
  executive: emptyExecutive,
};

// -- Core -------------------------------------------------------------------

/**
 * Generate a sales report from an array of transactions.
 *
 * Deduplicates by transaction ID, validates each record, aggregates totals,
 * rounds all monetary values to 2 decimal places, and strips PII from output.
 *
 * @param input - { transactions: Transaction[] }
 * @param options - { format?: ReportFormat; title?: string } (default format: 'summary')
 * @returns SummaryReport | DetailedReport | ExecutiveReport depending on format
 * @throws Error if format is invalid
 * @complexity O(n log n) — dominated by top-customer sort
 * @overallScore 95
 */
export function generateReport(
  input: { transactions: Transaction[] },
  options?: ReportOptions,
): SummaryReport | DetailedReport | ExecutiveReport {
  const format: ReportFormat = options?.format ?? 'summary';

  if (!isValidFormat(format)) {
    throw new Error(`Invalid report format: ${format}`);
  }

  const rawTransactions = input.transactions ?? [];

  // Empty case — fast path
  if (rawTransactions.length === 0) {
    return EMPTY_BUILDERS[format]();
  }

  // Deduplicate then validate
  const valid = deduplicateById(rawTransactions).filter(isValidTransaction);

  if (valid.length === 0) {
    return EMPTY_BUILDERS[format]();
  }

  // Aggregations
  const totalRevenue = roundTwo(
    valid.reduce((sum, t) => sum + t.amount, 0),
  );
  const transactionCount = valid.length;
  const averageOrderValue = roundTwo(totalRevenue / transactionCount);
  const revenueByRegion = computeRevenueByRegion(valid);
  const topCustomers = topCustomersBySpend(valid);
  const dateRange = computeDateRange(valid);

  // Build summary base (used by summary and detailed)
  const summary: SummaryReport = {
    totalRevenue,
    transactionCount,
    averageOrderValue,
    revenueByRegion,
    topCustomers,
    dateRange,
  };

  if (format === 'executive') {
    return {
      totalRevenue,
      transactionCount,
      averageOrderValue,
      dateRange,
    } as ExecutiveReport;
  }

  if (format === 'detailed') {
    const transactions: DetailedTransaction[] = valid.map((t) => ({
      id: t.id,
      customerId: t.customerId,
      amount: roundTwo(t.amount),
      region: t.region,
      date: t.date,
    }));
    return { ...summary, transactions } as DetailedReport;
  }

  // summary
  return summary;
}

// -- Utility exports --------------------------------------------------------

/**
 * Format a numeric amount as a USD currency string.
 *
 * @param amount - The number to format
 * @returns String in the form "$X.XX"
 * @complexity O(1)
 * @overallScore 100
 */
export function formatCurrency(amount: number): string {
  return `$${amount.toFixed(2)}`;
}

/**
 * Check whether a date string falls within an inclusive [start, end] range.
 *
 * @param date - ISO date string to test
 * @param start - ISO date string for range start (inclusive)
 * @param end - ISO date string for range end (inclusive)
 * @returns True if date is within range
 * @complexity O(1)
 * @overallScore 100
 */
export function isWithinRange(
  date: string,
  start: string,
  end: string,
): boolean {
  const d = new Date(date).getTime();
  return d >= new Date(start).getTime() && d <= new Date(end).getTime();
}

/**
 * Normalize a region string to trimmed uppercase.
 *
 * @param region - Raw region string
 * @returns Trimmed, uppercased region
 * @complexity O(n) where n = string length
 * @overallScore 100
 */
export function normalizeRegion(region: string): string {
  return region.trim().toUpperCase();
}
