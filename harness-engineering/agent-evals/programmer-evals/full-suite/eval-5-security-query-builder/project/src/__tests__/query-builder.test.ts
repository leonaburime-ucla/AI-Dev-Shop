import {
  buildSearchQuery,
  ValidationError,
  SearchInput,
  SearchOptions,
  SearchQueryResult,
} from '../query-builder';

// Suppress console.log during tests (except PII tests which manage their own spy)
let globalLogSpy: jest.SpyInstance;
beforeEach(() => {
  globalLogSpy = jest.spyOn(console, 'log').mockImplementation(() => {});
});
afterEach(() => {
  globalLogSpy.mockRestore();
});

// ── Helpers ─────────────────────────────────────────────────

function defaultInput(overrides?: Partial<SearchInput>): SearchInput {
  return { queryText: '', filters: {}, ...overrides };
}

function defaultOptions(overrides?: Partial<SearchOptions>): SearchOptions {
  return {
    pagination: { page: 1, pageSize: 20 },
    sort: { field: 'created_at', direction: 'ASC' },
    ...overrides,
  };
}

// ── Basic query building ────────────────────────────────────

describe('buildSearchQuery — basic', () => {
  it('returns well-formed result shape', () => {
    const result = buildSearchQuery(defaultInput(), defaultOptions());
    expect(result).toHaveProperty('sql');
    expect(result).toHaveProperty('params');
    expect(result).toHaveProperty('totalCountSql');
    expect(result).toHaveProperty('totalCountParams');
  });

  it('produces a SELECT from documents with ORDER BY, LIMIT, OFFSET', () => {
    const result = buildSearchQuery(defaultInput(), defaultOptions());
    expect(result.sql).toMatch(/^SELECT \* FROM documents\s+ORDER BY created_at ASC LIMIT \$1 OFFSET \$2$/);
    expect(result.params).toEqual([20, 0]);
  });

  it('produces a COUNT query without LIMIT/OFFSET', () => {
    const result = buildSearchQuery(defaultInput(), defaultOptions());
    expect(result.totalCountSql).toBe('SELECT COUNT(*) FROM documents ');
    expect(result.totalCountParams).toEqual([]);
  });
});

// ── Text search ─────────────────────────────────────────────

describe('buildSearchQuery — text search', () => {
  it('adds ILIKE conditions for queryText', () => {
    const result = buildSearchQuery(
      defaultInput({ queryText: 'hello' }),
      defaultOptions(),
    );
    expect(result.sql).toContain('title ILIKE $1');
    expect(result.sql).toContain('content ILIKE $2');
    expect(result.params[0]).toBe('%hello%');
    expect(result.params[1]).toBe('%hello%');
  });

  it('uses separate param indices for title and content ILIKE', () => {
    const result = buildSearchQuery(
      defaultInput({ queryText: 'test' }),
      defaultOptions(),
    );
    // title ILIKE $1 OR content ILIKE $2 — two distinct indices
    expect(result.sql).toContain('$1');
    expect(result.sql).toContain('$2');
  });

  it('skips text search when queryText is empty', () => {
    const result = buildSearchQuery(defaultInput(), defaultOptions());
    expect(result.sql).not.toContain('ILIKE');
  });
});

// ── Filters ─────────────────────────────────────────────────

describe('buildSearchQuery — filters', () => {
  it('adds status filter', () => {
    const result = buildSearchQuery(
      defaultInput({ filters: { status: 'published' } }),
      defaultOptions(),
    );
    expect(result.sql).toContain('status = $1');
    expect(result.params).toContain('published');
  });

  it('adds author filter', () => {
    const result = buildSearchQuery(
      defaultInput({ filters: { author: 'alice' } }),
      defaultOptions(),
    );
    expect(result.sql).toContain('author = $1');
    expect(result.params).toContain('alice');
  });

  it('adds date range filter with BETWEEN', () => {
    const result = buildSearchQuery(
      defaultInput({
        filters: { dateRange: { start: '2026-01-01', end: '2026-12-31' } },
      }),
      defaultOptions(),
    );
    expect(result.sql).toContain('BETWEEN $1 AND $2');
    expect(result.params).toContain('2026-01-01');
    expect(result.params).toContain('2026-12-31');
  });

  it('adds tags filter with IN clause', () => {
    const result = buildSearchQuery(
      defaultInput({ filters: { tags: ['finance', 'legal'] } }),
      defaultOptions(),
    );
    expect(result.sql).toContain('tags IN ($1, $2)');
    expect(result.params).toContain('finance');
    expect(result.params).toContain('legal');
  });

  it('skips tags filter when tags array is empty', () => {
    const result = buildSearchQuery(
      defaultInput({ filters: { tags: [] } }),
      defaultOptions(),
    );
    expect(result.sql).not.toContain('tags');
  });

  it('combines all filters correctly', () => {
    const result = buildSearchQuery(
      defaultInput({
        queryText: 'report',
        filters: {
          status: 'draft',
          author: 'bob',
          dateRange: { start: '2026-01-01', end: '2026-06-30' },
          tags: ['hr'],
        },
      }),
      defaultOptions(),
    );
    expect(result.sql).toContain('ILIKE');
    expect(result.sql).toContain('status =');
    expect(result.sql).toContain('author =');
    expect(result.sql).toContain('BETWEEN');
    expect(result.sql).toContain('tags IN');
    // All conditions joined with AND
    const whereMatch = result.sql.match(/WHERE (.+?) ORDER/);
    expect(whereMatch).not.toBeNull();
    const andCount = (whereMatch![1].match(/ AND /g) || []).length;
    // 5 conditions = 4 ANDs, plus 1 AND inside BETWEEN clause = 5 total
    expect(andCount).toBe(5);
  });
});

// ── Pagination ──────────────────────────────────────────────

describe('buildSearchQuery — pagination', () => {
  it('applies default pagination when omitted', () => {
    const result = buildSearchQuery(defaultInput());
    expect(result.params).toContain(20); // default pageSize
    expect(result.params).toContain(0); // offset for page 1
  });

  it('calculates offset correctly for page 3, pageSize 10', () => {
    const result = buildSearchQuery(defaultInput(), {
      pagination: { page: 3, pageSize: 10 },
    });
    expect(result.params).toContain(10);
    expect(result.params).toContain(20); // (3-1) * 10
  });

  it('rejects page < 1', () => {
    expect(() =>
      buildSearchQuery(defaultInput(), { pagination: { page: 0, pageSize: 20 } }),
    ).toThrow(ValidationError);
  });

  it('rejects negative page', () => {
    expect(() =>
      buildSearchQuery(defaultInput(), { pagination: { page: -5, pageSize: 20 } }),
    ).toThrow(ValidationError);
  });

  it('rejects pageSize > 100', () => {
    expect(() =>
      buildSearchQuery(defaultInput(), { pagination: { page: 1, pageSize: 101 } }),
    ).toThrow(ValidationError);
  });

  it('rejects pageSize = 0', () => {
    expect(() =>
      buildSearchQuery(defaultInput(), { pagination: { page: 1, pageSize: 0 } }),
    ).toThrow(ValidationError);
  });

  it('rejects non-integer page', () => {
    expect(() =>
      buildSearchQuery(defaultInput(), { pagination: { page: 1.5, pageSize: 20 } }),
    ).toThrow(ValidationError);
  });

  it('rejects non-integer pageSize', () => {
    expect(() =>
      buildSearchQuery(defaultInput(), { pagination: { page: 1, pageSize: 20.5 } }),
    ).toThrow(ValidationError);
  });

  it('allows pageSize = 100 (boundary)', () => {
    const result = buildSearchQuery(defaultInput(), {
      pagination: { page: 1, pageSize: 100 },
    });
    expect(result.params).toContain(100);
  });

  it('allows pageSize = 1 (boundary)', () => {
    const result = buildSearchQuery(defaultInput(), {
      pagination: { page: 1, pageSize: 1 },
    });
    expect(result.params).toContain(1);
  });
});

// ── Sort validation ─────────────────────────────────────────

describe('buildSearchQuery — sort', () => {
  it.each(['title', 'created_at', 'updated_at', 'author'])(
    'allows sort field "%s"',
    (field) => {
      const result = buildSearchQuery(defaultInput(), {
        sort: { field, direction: 'ASC' },
      });
      expect(result.sql).toContain(`ORDER BY ${field} ASC`);
    },
  );

  it('allows DESC direction', () => {
    const result = buildSearchQuery(defaultInput(), {
      sort: { field: 'title', direction: 'DESC' },
    });
    expect(result.sql).toContain('ORDER BY title DESC');
  });

  it('normalises direction case (lowercase input)', () => {
    const result = buildSearchQuery(defaultInput(), {
      sort: { field: 'title', direction: 'desc' },
    });
    expect(result.sql).toContain('ORDER BY title DESC');
  });

  it('rejects invalid sort field', () => {
    expect(() =>
      buildSearchQuery(defaultInput(), {
        sort: { field: 'DROP TABLE documents;--', direction: 'ASC' },
      }),
    ).toThrow(ValidationError);
  });

  it('rejects invalid sort direction', () => {
    expect(() =>
      buildSearchQuery(defaultInput(), {
        sort: { field: 'title', direction: 'SIDEWAYS' },
      }),
    ).toThrow(ValidationError);
  });

  it('applies defaults when sort is omitted', () => {
    const result = buildSearchQuery(defaultInput());
    expect(result.sql).toContain('ORDER BY created_at ASC');
  });
});

// ── SQL injection prevention (adversarial) ──────────────────

describe('buildSearchQuery — SQL injection prevention', () => {
  it('parameterizes queryText — never interpolated', () => {
    const malicious = "'; DROP TABLE documents; --";
    const result = buildSearchQuery(
      defaultInput({ queryText: malicious }),
      defaultOptions(),
    );
    // The malicious string should be in params, not in the SQL
    expect(result.sql).not.toContain(malicious);
    expect(result.params).toContain(`%${malicious}%`);
  });

  it('parameterizes status filter', () => {
    const malicious = "' OR 1=1; --";
    const result = buildSearchQuery(
      defaultInput({ filters: { status: malicious } }),
      defaultOptions(),
    );
    expect(result.sql).not.toContain(malicious);
    expect(result.params).toContain(malicious);
  });

  it('parameterizes author filter', () => {
    const malicious = "admin'--";
    const result = buildSearchQuery(
      defaultInput({ filters: { author: malicious } }),
      defaultOptions(),
    );
    expect(result.sql).not.toContain(malicious);
    expect(result.params).toContain(malicious);
  });

  it('parameterizes tags', () => {
    const malicious = ["'; DELETE FROM documents; --", 'normal'];
    const result = buildSearchQuery(
      defaultInput({ filters: { tags: malicious } }),
      defaultOptions(),
    );
    expect(result.sql).not.toContain(malicious[0]);
    expect(result.params).toContain(malicious[0]);
  });

  it('rejects sort field injection attempt', () => {
    expect(() =>
      buildSearchQuery(defaultInput(), {
        sort: { field: '1; DROP TABLE documents;--', direction: 'ASC' },
      }),
    ).toThrow(ValidationError);
  });

  it('rejects sort direction injection attempt', () => {
    expect(() =>
      buildSearchQuery(defaultInput(), {
        sort: { field: 'title', direction: 'ASC; DROP TABLE documents;--' },
      }),
    ).toThrow(ValidationError);
  });

  it('parameterizes dateRange values', () => {
    const malicious = "2026-01-01'; DROP TABLE documents;--";
    const result = buildSearchQuery(
      defaultInput({
        filters: { dateRange: { start: malicious, end: '2026-12-31' } },
      }),
      defaultOptions(),
    );
    expect(result.sql).not.toContain(malicious);
    expect(result.params).toContain(malicious);
  });
});

// ── PII logging safety ──────────────────────────────────────

describe('buildSearchQuery — PII-safe logging', () => {
  let logSpy: jest.SpyInstance;

  beforeEach(() => {
    logSpy = jest.spyOn(console, 'log').mockImplementation(() => {});
  });
  afterEach(() => {
    logSpy.mockRestore();
  });

  it('logs query length, not query text', () => {
    const secret = 'my-secret-medical-records';
    buildSearchQuery(
      defaultInput({ queryText: secret }),
      defaultOptions(),
    );
    const logOutput = logSpy.mock.calls[0][0] as string;
    expect(logOutput).not.toContain(secret);
    expect(logOutput).toContain(`queryLength=${secret.length}`);
  });

  it('logs filter count, not filter values', () => {
    buildSearchQuery(
      defaultInput({
        filters: { status: 'classified', author: 'secret-agent' },
      }),
      defaultOptions(),
    );
    const logOutput = logSpy.mock.calls[0][0] as string;
    expect(logOutput).not.toContain('classified');
    expect(logOutput).not.toContain('secret-agent');
    expect(logOutput).toContain('filterCount=2');
  });

  it('logs page and pageSize', () => {
    buildSearchQuery(defaultInput(), {
      pagination: { page: 5, pageSize: 25 },
    });
    const logOutput = logSpy.mock.calls[0][0] as string;
    expect(logOutput).toContain('page=5');
    expect(logOutput).toContain('pageSize=25');
  });
});

// ── Count query correctness ─────────────────────────────────

describe('buildSearchQuery — totalCount query', () => {
  it('shares WHERE params but not LIMIT/OFFSET params', () => {
    const result = buildSearchQuery(
      defaultInput({
        queryText: 'test',
        filters: { status: 'active' },
      }),
      defaultOptions(),
    );
    // totalCountParams should have text search params + status param
    // but NOT pageSize and offset
    expect(result.totalCountParams.length).toBe(result.params.length - 2);
    expect(result.totalCountSql).not.toContain('LIMIT');
    expect(result.totalCountSql).not.toContain('OFFSET');
    expect(result.totalCountSql).toContain('COUNT(*)');
    expect(result.totalCountSql).toContain('WHERE');
  });

  it('count query has no WHERE when no filters', () => {
    const result = buildSearchQuery(defaultInput(), defaultOptions());
    expect(result.totalCountSql).not.toContain('WHERE');
    expect(result.totalCountParams).toEqual([]);
  });
});

// ── Edge cases ──────────────────────────────────────────────

describe('buildSearchQuery — edge cases', () => {
  it('handles empty filters object', () => {
    const result = buildSearchQuery(
      { queryText: '', filters: {} },
      defaultOptions(),
    );
    expect(result.sql).not.toContain('WHERE');
  });

  it('works with no options argument at all', () => {
    const result = buildSearchQuery({ queryText: '', filters: {} });
    expect(result.sql).toContain('ORDER BY created_at ASC');
    expect(result.params).toContain(20); // default pageSize
  });

  it('single tag produces IN clause with one placeholder', () => {
    const result = buildSearchQuery(
      defaultInput({ filters: { tags: ['solo'] } }),
      defaultOptions(),
    );
    expect(result.sql).toContain('tags IN ($1)');
  });
});
