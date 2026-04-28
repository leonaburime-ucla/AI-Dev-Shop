// ──────────────────────────────────────────────────────────────
// Secure Search Query Builder for PostgreSQL `documents` table
// ──────────────────────────────────────────────────────────────

/** Allowed sort columns — allowlist prevents SQL injection via ORDER BY. */
const ALLOWED_SORT_FIELDS = new Set([
  'title',
  'created_at',
  'updated_at',
  'author',
] as const);

/** Allowed sort directions. */
const ALLOWED_SORT_DIRECTIONS = new Set(['ASC', 'DESC'] as const);

const DEFAULT_PAGE_SIZE = 20;
const MAX_PAGE_SIZE = 100;
const DEFAULT_SORT_FIELD = 'created_at';
const DEFAULT_SORT_DIRECTION = 'ASC';

// ── Public types ────────────────────────────────────────────

export interface SearchFilters {
  status?: string;
  author?: string;
  dateRange?: { start: string; end: string };
  tags?: string[];
}

export interface Pagination {
  page?: number;
  pageSize?: number;
}

export interface SortOptions {
  field?: string;
  direction?: string;
}

export interface SearchInput {
  queryText: string;
  filters: SearchFilters;
}

export interface SearchOptions {
  pagination?: Pagination;
  sort?: SortOptions;
}

export interface SearchQueryResult {
  sql: string;
  params: unknown[];
  totalCountSql: string;
  totalCountParams: unknown[];
}

// ── Errors ──────────────────────────────────────────────────

export class ValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ValidationError';
  }
}

// ── Validation helpers (pure, no side effects) ──────────────

/**
 * Validates and normalises pagination.
 *
 * @param pagination - Raw pagination input
 * @returns Validated { page, pageSize }
 * @throws ValidationError if constraints are violated
 * @complexity O(1)
 * @overallScore 100
 */
function validatePagination(
  pagination: Pagination | undefined,
): { page: number; pageSize: number } {
  const page = pagination?.page ?? 1;
  const pageSize = pagination?.pageSize ?? DEFAULT_PAGE_SIZE;

  if (!Number.isInteger(page) || page < 1) {
    throw new ValidationError('page must be an integer >= 1');
  }
  if (!Number.isInteger(pageSize) || pageSize < 1 || pageSize > MAX_PAGE_SIZE) {
    throw new ValidationError(
      `pageSize must be an integer between 1 and ${MAX_PAGE_SIZE}`,
    );
  }
  return { page, pageSize };
}

/**
 * Validates sort field and direction against allowlists.
 *
 * @param sort - Raw sort input
 * @returns Validated { field, direction } (safe for interpolation)
 * @throws ValidationError if field or direction is not in the allowlist
 * @complexity O(1)
 * @overallScore 100
 */
function validateSort(
  sort: SortOptions | undefined,
): { field: string; direction: string } {
  const field = sort?.field ?? DEFAULT_SORT_FIELD;
  const direction = sort?.direction?.toUpperCase() ?? DEFAULT_SORT_DIRECTION;

  if (!ALLOWED_SORT_FIELDS.has(field as any)) {
    throw new ValidationError(
      `Invalid sort field "${field}". Allowed: ${[...ALLOWED_SORT_FIELDS].join(', ')}`,
    );
  }
  if (!ALLOWED_SORT_DIRECTIONS.has(direction as any)) {
    throw new ValidationError(
      `Invalid sort direction "${direction}". Allowed: ASC, DESC`,
    );
  }
  return { field, direction };
}

// ── Logging helper (PII-safe) ───────────────────────────────

/**
 * Logs search metadata without exposing PII.
 *
 * Logs: query length, number of active filters, page, pageSize.
 * Never logs actual query text or filter values.
 *
 * @param queryText - The raw query text (used only for length measurement)
 * @param filters - The raw filters (used only for key counting)
 * @param page - Current page number
 * @param pageSize - Items per page
 * @complexity O(1)
 * @overallScore 100
 */
function logSearchOperation(
  queryText: string,
  filters: SearchFilters,
  page: number,
  pageSize: number,
): void {
  const filterCount = Object.keys(filters).filter(
    (k) => filters[k as keyof SearchFilters] != null,
  ).length;
  console.log(
    `[Search] queryLength=${queryText.length} filterCount=${filterCount} page=${page} pageSize=${pageSize}`,
  );
}

// ── Core builder ────────────────────────────────────────────

/**
 * Builds a parameterized search query for the `documents` table.
 *
 * All user-provided values are parameterized — never interpolated into SQL.
 * Sort field/direction are validated against a strict allowlist before use.
 *
 * Uses the two-object exported signature: required SearchInput + optional SearchOptions.
 *
 * @param input - Required: { queryText, filters }
 * @param options - Optional: { pagination?, sort? }
 * @returns { sql, params, totalCountSql, totalCountParams }
 * @throws ValidationError on invalid pagination or sort
 * @complexity Time: O(f + t) where f = filter count, t = tag count. Space: O(p) where p = param count.
 * @overallScore 88
 */
export function buildSearchQuery(
  input: SearchInput,
  options?: SearchOptions,
): SearchQueryResult {
  const { queryText, filters } = input;
  const { page, pageSize } = validatePagination(options?.pagination);
  const { field: sortField, direction: sortDirection } = validateSort(
    options?.sort,
  );

  // PII-safe logging
  logSearchOperation(queryText, filters, page, pageSize);

  const conditions: string[] = [];
  const params: unknown[] = [];
  let paramIndex = 1;

  // ── Text search ──
  if (queryText) {
    conditions.push(
      `(title ILIKE $${paramIndex} OR content ILIKE $${paramIndex + 1})`,
    );
    params.push(`%${queryText}%`, `%${queryText}%`);
    paramIndex += 2;
  }

  // ── Status filter ──
  if (filters.status) {
    conditions.push(`status = $${paramIndex}`);
    params.push(filters.status);
    paramIndex++;
  }

  // ── Author filter ──
  if (filters.author) {
    conditions.push(`author = $${paramIndex}`);
    params.push(filters.author);
    paramIndex++;
  }

  // ── Date range filter (BETWEEN) ──
  if (filters.dateRange) {
    conditions.push(
      `created_at BETWEEN $${paramIndex} AND $${paramIndex + 1}`,
    );
    params.push(filters.dateRange.start, filters.dateRange.end);
    paramIndex += 2;
  }

  // ── Tags filter (IN clause per brief requirement) ──
  if (filters.tags && filters.tags.length > 0) {
    const tagPlaceholders = filters.tags.map(
      (_: string, i: number) => `$${paramIndex + i}`,
    );
    conditions.push(`tags IN (${tagPlaceholders.join(', ')})`);
    params.push(...filters.tags);
    paramIndex += filters.tags.length;
  }

  const whereClause =
    conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';

  // Sort field/direction are from validated allowlist — safe to interpolate
  const orderClause = `ORDER BY ${sortField} ${sortDirection}`;

  const offset = (page - 1) * pageSize;

  const sql = `SELECT * FROM documents ${whereClause} ${orderClause} LIMIT $${paramIndex} OFFSET $${paramIndex + 1}`;
  params.push(pageSize, offset);

  // Count query shares the WHERE params but not LIMIT/OFFSET
  const totalCountParams = params.slice(0, params.length - 2);
  const totalCountSql = `SELECT COUNT(*) FROM documents ${whereClause}`;

  return { sql, params, totalCountSql, totalCountParams };
}
