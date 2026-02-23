---
name: postgresql
version: 1.0.0
last_updated: 2026-02-23
description: Use when writing advanced PostgreSQL queries, implementing triggers, stored functions, full-text search, JSONB operations, partitioning, or diagnosing query performance. Applies to any PostgreSQL host (Supabase, RDS, Railway, Neon, self-hosted).
---

# Skill: PostgreSQL

PostgreSQL is not just a relational database — it is a programmable data platform. This skill covers the features that go beyond basic CRUD: the tools that let you push logic to the database when it belongs there, query complex data shapes efficiently, and diagnose performance problems with evidence.

Use these features when the problem calls for them. A simple `SELECT` does not need a CTE. A three-row lookup table does not need partitioning. Apply advanced features when they solve a real problem, and document why they were chosen.

## CTEs (Common Table Expressions)

CTEs give complex queries a readable structure. They are defined with `WITH` and referenced like temporary tables within the query.

```sql
-- Basic CTE: break a multi-step query into named stages
WITH active_users AS (
    SELECT id, email, created_at
    FROM users
    WHERE deleted_at IS NULL
),
recent_orders AS (
    SELECT user_id, COUNT(*) AS order_count
    FROM orders
    WHERE created_at > now() - interval '30 days'
    GROUP BY user_id
)
SELECT u.email, COALESCE(o.order_count, 0) AS orders_last_30_days
FROM active_users u
LEFT JOIN recent_orders o ON o.user_id = u.id
ORDER BY orders_last_30_days DESC;
```

**Materialization**: In PostgreSQL 12+, CTEs are not materialized by default (the planner can inline them). Force materialization with `WITH ... AS MATERIALIZED (...)` when you want the CTE to execute exactly once regardless of how many times it is referenced.

### Recursive CTEs

Recursive CTEs traverse hierarchical or graph-shaped data. They consist of a base case (non-recursive term) and a recursive term connected with `UNION ALL`.

```sql
-- Traverse an organization hierarchy to find all descendants of a given node
WITH RECURSIVE org_tree AS (
    -- Base case: start at the given node
    SELECT id, name, parent_id, 0 AS depth
    FROM departments
    WHERE id = $1

    UNION ALL

    -- Recursive term: join children to current frontier
    SELECT d.id, d.name, d.parent_id, t.depth + 1
    FROM departments d
    INNER JOIN org_tree t ON d.parent_id = t.id
)
SELECT id, name, depth
FROM org_tree
ORDER BY depth, name;
```

**Guard against infinite loops**: Add a depth limit (`WHERE depth < 50`) or a cycle detection check (`WHERE id <> ANY(path)`) when the graph may contain cycles.

## Window Functions

Window functions compute a value for each row based on a set of related rows (the "window") without collapsing rows the way `GROUP BY` does. They are evaluated after `WHERE`, `GROUP BY`, and `HAVING`.

```sql
-- ROW_NUMBER: assign sequential position within each partition
SELECT
    user_id,
    order_id,
    created_at,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS rn
FROM orders;

-- RANK / DENSE_RANK: rank with gaps / rank without gaps on ties
SELECT
    product_id,
    total_sold,
    RANK()       OVER (ORDER BY total_sold DESC) AS rank_with_gaps,
    DENSE_RANK() OVER (ORDER BY total_sold DESC) AS rank_no_gaps
FROM product_sales;

-- LAG / LEAD: access the previous or next row's value
SELECT
    date,
    revenue,
    LAG(revenue, 1) OVER (ORDER BY date) AS prev_day_revenue,
    revenue - LAG(revenue, 1) OVER (ORDER BY date) AS day_over_day_change
FROM daily_revenue;

-- SUM / AVG OVER: running totals and moving averages
SELECT
    date,
    amount,
    SUM(amount) OVER (ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total,
    AVG(amount) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS rolling_7_day_avg
FROM transactions;
```

**Frame clauses**: Control which rows are included in the window relative to the current row.
- `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` — all rows from start to current (running total)
- `ROWS BETWEEN 6 PRECEDING AND CURRENT ROW` — current row plus the 6 preceding (rolling window)
- `RANGE BETWEEN INTERVAL '7 days' PRECEDING AND CURRENT ROW` — range-based window on a date column

## JSONB

`jsonb` stores JSON as a parsed binary structure, enabling fast key-access and indexing. Prefer `jsonb` over `json` — `json` stores raw text and must re-parse on every access.

### Operators

```sql
-- -> returns a JSON value (preserves JSON type)
SELECT data -> 'address' -> 'city' FROM users;

-- ->> returns text (casts to text)
SELECT data ->> 'email' FROM users;

-- #> and #>> navigate nested paths
SELECT data #> '{address, city}' FROM users;
SELECT data #>> '{address, city}' FROM users;

-- @> containment: does the left value contain the right?
SELECT * FROM users WHERE data @> '{"role": "admin"}';

-- ? key existence
SELECT * FROM users WHERE data ? 'phone_number';

-- jsonb_set: update a nested value
UPDATE users
SET data = jsonb_set(data, '{address, city}', '"Portland"')
WHERE id = $1;

-- || merge two jsonb objects
UPDATE users SET data = data || '{"last_login": "2026-02-23"}' WHERE id = $1;

-- - remove a key
UPDATE users SET data = data - 'temp_token' WHERE id = $1;
```

### Indexing JSONB

```sql
-- GIN index for containment (@>) and key-existence (?) queries
CREATE INDEX idx_users_data_gin ON users USING GIN (data);

-- GIN with jsonb_path_ops operator class (smaller index, only supports @>)
CREATE INDEX idx_users_data_path ON users USING GIN (data jsonb_path_ops);

-- B-tree index on a specific extracted field (for equality and range on one key)
CREATE INDEX idx_users_role ON users ((data ->> 'role'));
```

Use a GIN index when queries use `@>` or `?` on arbitrary keys. Use an expression B-tree index when queries always filter on the same known key with equality or range.

## Triggers and Trigger Functions

Triggers execute a function before or after a row-level or statement-level event (INSERT, UPDATE, DELETE, TRUNCATE).

```sql
-- Step 1: Create the trigger function (must return TRIGGER)
CREATE OR REPLACE FUNCTION notify_order_created()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    PERFORM pg_notify('order_created', row_to_json(NEW)::text);
    RETURN NEW;  -- for BEFORE triggers; AFTER triggers can return NULL
END;
$$;

-- Step 2: Attach the trigger to the table
CREATE TRIGGER trg_order_created
AFTER INSERT ON orders
FOR EACH ROW EXECUTE FUNCTION notify_order_created();
```

**BEFORE vs AFTER**: Use `BEFORE` to modify `NEW` before the row is written (e.g. set `updated_at`, transform a value). Use `AFTER` for side effects that depend on the committed row state (e.g. notifications, audit log writes).

**FOR EACH ROW vs FOR EACH STATEMENT**: `FOR EACH ROW` fires once per affected row (can access `NEW` and `OLD`). `FOR EACH STATEMENT` fires once per SQL statement (cannot access individual rows — use for bulk audit logging).

**Common trigger use cases**:
- Auto-set `updated_at` on UPDATE
- Maintain a denormalized `count` column
- Write to an audit log table
- Send a `pg_notify` event for realtime consumers
- Enforce complex cross-table business rules that CHECK constraints cannot express

## Stored Functions and Procedures

PostgreSQL supports functions in multiple languages. PL/pgSQL is the standard procedural language.

```sql
-- Function: returns a value, usable in SELECT
CREATE OR REPLACE FUNCTION get_user_order_total(p_user_id uuid)
RETURNS numeric
LANGUAGE plpgsql
STABLE  -- result is stable within a transaction for the same inputs
AS $$
DECLARE
    v_total numeric;
BEGIN
    SELECT COALESCE(SUM(amount), 0)
    INTO v_total
    FROM orders
    WHERE user_id = p_user_id
      AND status = 'completed';

    RETURN v_total;
END;
$$;

-- Procedure: no return value, can manage its own transactions
CREATE OR REPLACE PROCEDURE archive_old_orders(p_cutoff_date date)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO orders_archive SELECT * FROM orders WHERE created_at < p_cutoff_date;
    DELETE FROM orders WHERE created_at < p_cutoff_date;
    COMMIT;
END;
$$;
```

**Volatility categories**:
- `VOLATILE` (default) — result can change between calls even with the same inputs; cannot be optimized away
- `STABLE` — result is constant within a single transaction for the same inputs; planner can optimize
- `IMMUTABLE` — result is constant for the same inputs across all transactions; can be indexed

**Security context**:
- `SECURITY INVOKER` (default) — function runs with the permissions of the calling user
- `SECURITY DEFINER` — function runs with the permissions of the function owner; use with care, equivalent to `sudo`

## Extensions

PostgreSQL extensions add data types, functions, and index types. Enable with `CREATE EXTENSION IF NOT EXISTS <name>`.

| Extension | Purpose | Key Functions/Types |
|---|---|---|
| `uuid-ossp` | UUID generation | `uuid_generate_v4()` (prefer `gen_random_uuid()` from pg_crypto in PG13+) |
| `pgcrypto` | Cryptographic functions | `gen_random_uuid()`, `crypt()`, `digest()` |
| `pg_trgm` | Trigram-based fuzzy text matching | `similarity()`, `%` operator, GIN/GiST trigram indexes |
| `unaccent` | Remove accents from text for search | `unaccent()` |
| `postgis` | Geographic/geometric data | `geometry`, `geography` types; spatial indexes |
| `hstore` | Key-value pairs in a column | Predates jsonb; prefer jsonb for new work |
| `pg_stat_statements` | Track execution stats for all queries | `pg_stat_statements` view |
| `btree_gin` | GIN indexes for B-tree types | Enables GIN on `integer`, `text`, etc. for multi-column GIN indexes |
| `pg_partman` | Automated partition management | Auto-creates and drops partitions by time or serial range |

Supabase enables `uuid-ossp`, `pgcrypto`, `pg_trgm`, and `unaccent` by default. Others must be enabled explicitly in the Supabase dashboard or via `CREATE EXTENSION`.

## Full-Text Search

PostgreSQL's built-in full-text search uses `tsvector` (a processed document) and `tsquery` (a search query). It supports stemming, stop words, and ranking.

```sql
-- Add a tsvector column for efficient search
ALTER TABLE articles ADD COLUMN search_vector tsvector;

-- Populate it with a weighted combination of fields
UPDATE articles
SET search_vector =
    setweight(to_tsvector('english', COALESCE(title, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(body, '')), 'B');

-- GIN index for fast tsvector queries
CREATE INDEX idx_articles_search ON articles USING GIN (search_vector);

-- Keep it current with a trigger
CREATE OR REPLACE FUNCTION update_article_search_vector()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.body, '')), 'B');
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_article_search_vector
BEFORE INSERT OR UPDATE ON articles
FOR EACH ROW EXECUTE FUNCTION update_article_search_vector();

-- Query: returns rows containing 'database' AND 'performance'
SELECT title, ts_rank(search_vector, query) AS rank
FROM articles, to_tsquery('english', 'database & performance') query
WHERE search_vector @@ query
ORDER BY rank DESC;
```

**Weight classes**: `A` (highest) through `D` (lowest). Use them to boost title matches over body matches in ranking.

**`pg_trgm` for fuzzy matching**: When users may misspell search terms, use trigram similarity instead of or in addition to full-text search.

```sql
CREATE INDEX idx_products_name_trgm ON products USING GIN (name gin_trgm_ops);

-- Find products with name similar to 'headphons' (misspelling)
SELECT name, similarity(name, 'headphons') AS sim
FROM products
WHERE name % 'headphons'
ORDER BY sim DESC;
```

## Partitioning

Partitioning divides a large table into smaller physical segments (partitions) while maintaining a single logical table interface. The planner routes queries to only the relevant partitions (partition pruning).

**Partition types**:

```sql
-- Range partitioning: by date range (most common for time-series data)
CREATE TABLE events (
    id          uuid NOT NULL DEFAULT gen_random_uuid(),
    user_id     uuid NOT NULL,
    event_type  text NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
) PARTITION BY RANGE (created_at);

CREATE TABLE events_2026_q1 PARTITION OF events
    FOR VALUES FROM ('2026-01-01') TO ('2026-04-01');

CREATE TABLE events_2026_q2 PARTITION OF events
    FOR VALUES FROM ('2026-04-01') TO ('2026-07-01');

-- List partitioning: by discrete values
CREATE TABLE orders (
    id     uuid NOT NULL DEFAULT gen_random_uuid(),
    region text NOT NULL,
    amount numeric NOT NULL
) PARTITION BY LIST (region);

CREATE TABLE orders_us PARTITION OF orders FOR VALUES IN ('us-east', 'us-west');
CREATE TABLE orders_eu PARTITION OF orders FOR VALUES IN ('eu-west', 'eu-central');

-- Hash partitioning: distribute rows evenly by hash
CREATE TABLE user_events (
    id      uuid NOT NULL DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL
) PARTITION BY HASH (user_id);

CREATE TABLE user_events_0 PARTITION OF user_events FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE user_events_1 PARTITION OF user_events FOR VALUES WITH (MODULUS 4, REMAINDER 1);
-- etc.
```

**When to partition**: Tables exceeding ~50-100 million rows where queries consistently filter on the partition key (usually a date or category column). Partitioning a small table adds overhead with no benefit.

**Partition pruning**: Only works when the `WHERE` clause filters on the partition key with a constant or parameter — not a subquery or non-immutable function call.

## EXPLAIN ANALYZE and Query Optimization

`EXPLAIN ANALYZE` executes the query and shows the actual execution plan with row counts and timings.

```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT u.email, COUNT(o.id) AS order_count
FROM users u
JOIN orders o ON o.user_id = u.id
WHERE u.created_at > '2025-01-01'
GROUP BY u.email
ORDER BY order_count DESC;
```

**Key nodes to identify**:

| Node | Description | Performance Signal |
|---|---|---|
| `Seq Scan` | Full table scan | Acceptable on small tables; expensive on large ones — check for missing index |
| `Index Scan` | Uses an index to find rows, then fetches from heap | Good — but high heap fetches may indicate a covering index opportunity |
| `Index Only Scan` | All needed columns in the index — no heap fetch | Best for read-heavy queries |
| `Bitmap Heap Scan` | Collects matching row locations from index, then batch-fetches heap | Efficient for moderate selectivity |
| `Hash Join` | Builds a hash table from one side, probes with the other | Good for large unsorted inputs |
| `Nested Loop` | For each row in outer, scans inner | Good when inner is indexed and outer is small |
| `Sort` | In-memory sort (fast) or disk sort (slow) | Disk sorts appear as `Sort Method: external merge Disk` — add an index to avoid |

**Red flags in EXPLAIN output**:
- Estimated rows vastly different from actual rows → stale statistics; run `ANALYZE <table>`
- `Seq Scan` on a large table inside a loop → missing index on the join or filter column
- `Sort Method: external merge Disk` → increase `work_mem` for this session or add an index
- `Rows Removed by Filter: N` is large → index exists but is not selective enough for this predicate

```sql
-- Update statistics for a specific table
ANALYZE orders;

-- Set work_mem for a single session (resets after session ends)
SET work_mem = '256MB';
```

## Performance Patterns and Anti-Patterns

### Patterns

**Connection pooling**: PostgreSQL has a fixed connection limit (`max_connections`). Use PgBouncer (or Supabase's built-in pooler) in transaction pooling mode for high-concurrency applications. Each application request reuses a connection from the pool rather than creating a new one.

**Batch inserts**: Insert multiple rows in a single statement instead of looping.

```sql
-- Good: single round trip
INSERT INTO events (user_id, event_type, created_at)
VALUES ($1, $2, $3), ($4, $5, $6), ($7, $8, $9);

-- Bad: one round trip per row
INSERT INTO events (user_id, event_type, created_at) VALUES ($1, $2, $3);
INSERT INTO events (user_id, event_type, created_at) VALUES ($4, $5, $6);
```

**Partial indexes for active subsets**: When application queries almost always filter on a condition (e.g. `deleted_at IS NULL`, `status = 'pending'`), a partial index is smaller and faster than a full index.

**COPY for bulk loads**: Use `COPY` instead of `INSERT` for loading large datasets. `COPY` bypasses the standard query path and is 10-100x faster for bulk data.

### Anti-Patterns

**`SELECT *` in production code**: Always list the columns you need. `SELECT *` fetches unnecessary data over the network, prevents index-only scans, and breaks when columns are added or reordered.

**`OFFSET` pagination on large tables**: `OFFSET 10000 LIMIT 20` scans and discards 10,000 rows. Use keyset pagination (cursor-based) instead.

```sql
-- Bad: scans 10,020 rows to return 20
SELECT * FROM orders ORDER BY created_at DESC OFFSET 10000 LIMIT 20;

-- Good: uses the index directly from the cursor position
SELECT * FROM orders
WHERE created_at < $last_seen_created_at
   OR (created_at = $last_seen_created_at AND id < $last_seen_id)
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

**`NOT IN` with a subquery**: If the subquery returns any NULL, `NOT IN` returns no rows at all (due to three-valued logic). Use `NOT EXISTS` instead.

```sql
-- Dangerous: returns empty if subquery has any NULL
SELECT * FROM orders WHERE user_id NOT IN (SELECT id FROM banned_users);

-- Correct
SELECT * FROM orders o
WHERE NOT EXISTS (SELECT 1 FROM banned_users b WHERE b.id = o.user_id);
```

**Functions on indexed columns in WHERE**: Wrapping a column in a function prevents index use.

```sql
-- Bad: index on created_at is not used
WHERE DATE(created_at) = '2026-01-01'

-- Good: index on created_at is used
WHERE created_at >= '2026-01-01' AND created_at < '2026-01-02'
```

**Implicit type coercions in joins**: Joining `text` to `uuid` forces a cast on every row. Keep FK and PK types identical.

## Transaction Isolation Levels

PostgreSQL supports four isolation levels. The default is `READ COMMITTED`.

| Level | Dirty Reads | Non-Repeatable Reads | Phantom Reads | Use Case |
|---|---|---|---|---|
| `READ COMMITTED` | No | Possible | Possible | Default; suitable for most OLTP workloads |
| `REPEATABLE READ` | No | No | No (in PG) | Financial calculations that must see a consistent snapshot; reporting queries |
| `SERIALIZABLE` | No | No | No | When transactions must behave as if executed one at a time; complex business invariants |

PostgreSQL does not implement `READ UNCOMMITTED` — it is accepted as a syntax alias for `READ COMMITTED`.

```sql
-- Set isolation level for the current transaction
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ;
-- ... your queries ...
COMMIT;
```

**Serialization failures**: `SERIALIZABLE` transactions may fail with `ERROR: could not serialize access due to concurrent update`. Applications using serializable isolation must be prepared to retry transactions on this error.

**Advisory locks**: For application-level coordination (e.g. ensuring only one process runs a job at a time), use advisory locks instead of table-level locks.

```sql
-- Session-level advisory lock (released when session ends)
SELECT pg_advisory_lock(12345);

-- Transaction-level advisory lock (released on COMMIT/ROLLBACK)
SELECT pg_advisory_xact_lock(12345);

-- Try to acquire without blocking
SELECT pg_try_advisory_lock(12345);  -- returns boolean
```
