# Performance and Operations

Use this reference when diagnosing slow queries, planning for very large tables, counting at scale, making manual data changes, or selecting transaction behavior.

## Partitioning

Partitioning divides a large table into smaller physical partitions while keeping a single logical table interface.

```sql
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
```

Other partition types:

- `LIST` for discrete categories
- `HASH` for even distribution by key

When to partition:

- tables above roughly 50 to 100 million rows
- queries consistently filter on the partition key
- the partition key aligns with operational lifecycle, such as time-based retention

Do not partition small tables. The operational overhead is real.

Partition pruning only works when the `WHERE` clause filters on the partition key with a constant or parameter.

## EXPLAIN ANALYZE

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

Key nodes to identify:

| Node | Description | Performance Signal |
|---|---|---|
| `Seq Scan` | Full table scan | Fine on small tables, suspicious on large ones |
| `Index Scan` | Uses an index and fetches heap rows | Good, but high heap fetches may suggest a covering index |
| `Index Only Scan` | All needed columns come from the index | Best for read-heavy queries |
| `Bitmap Heap Scan` | Batch-fetches heap rows from index matches | Efficient for moderate selectivity |
| `Hash Join` | Hashes one side and probes with the other | Good for large unsorted inputs |
| `Nested Loop` | Repeats inner lookup for each outer row | Good when outer is small and inner is indexed |
| `Sort` | In-memory or disk sort | Disk sorts indicate avoidable cost |

Red flags:

- estimated rows far from actual rows
- `Seq Scan` on a large table inside a loop
- `Sort Method: external merge Disk`
- very large `Rows Removed by Filter`

Useful follow-up:

```sql
ANALYZE orders;
SET work_mem = '256MB';
```

## Performance Patterns

- **Connection pooling**: use PgBouncer or the managed-host pooler for high-concurrency apps.
- **Batch inserts**: prefer one multi-row insert over loops.
- **Partial indexes**: use them when queries almost always filter on a stable predicate.
- **COPY**: use it for bulk loads instead of row-by-row inserts.

## Performance Anti-Patterns

- `SELECT *` in production queries
- `OFFSET` pagination on large tables
- `NOT IN` with nullable subqueries
- functions on indexed columns in `WHERE`
- implicit type coercions in joins

Examples:

```sql
SELECT * FROM orders ORDER BY created_at DESC OFFSET 10000 LIMIT 20;

SELECT * FROM orders
WHERE created_at < $last_seen_created_at
   OR (created_at = $last_seen_created_at AND id < $last_seen_id)
ORDER BY created_at DESC, id DESC
LIMIT 20;

SELECT * FROM orders WHERE user_id NOT IN (SELECT id FROM banned_users);

SELECT * FROM orders o
WHERE NOT EXISTS (SELECT 1 FROM banned_users b WHERE b.id = o.user_id);
```

## Counting and Aggregating

Aggregate in SQL (`count(*)`, `sum()`, `GROUP BY`). Never fetch rows into application code to count or total them.

Exact `count(*)` is not cheap on large tables: under MVCC, PostgreSQL must check visibility for every counted row. An unfiltered exact count scans the whole table or a covering index; a selective filter can restrict the scan. An index-only scan skips heap visits only on pages marked all-visible.

```sql
-- existence: stops at the first match
SELECT EXISTS (SELECT 1 FROM orders WHERE user_id = $1);

-- whole-table estimate; updated by VACUUM, ANALYZE, and some DDL (e.g. CREATE INDEX).
-- On PG14+, -1 means unknown; NULLIF maps it to NULL.
SELECT NULLIF(reltuples, -1)::bigint AS estimate FROM pg_class WHERE oid = 'orders'::regclass;

-- capped filtered count: render "1000+" past the cap
SELECT count(*) FROM (SELECT 1 FROM orders WHERE status = 'pending' LIMIT 1001) s;
```

- Use `EXISTS`, not `count(*) > 0`.
- For UI totals on huge tables, show an estimate or a maintained counter:
  - `reltuples` is relation-wide and ignores tenant filters and RLS. Use it only for whole-table totals the caller is authorized to see.
  - For a filtered estimate, run `EXPLAIN SELECT 1 FROM … WHERE …` (no aggregate, no `LIMIT`) under the caller's effective role and read the row estimate. `EXPLAIN SELECT count(*)` reports one output row, not the match count.
  - Maintain counters by trigger or scheduled job, scoped to the same authorization boundary as the rows. A single hot counter row becomes a write-contention point.

## Safe Manual Data Changes

Never run an ad-hoc `UPDATE` or `DELETE` against production outside an explicit transaction. Lock and review the exact rows first, then change only those rows:

```sql
BEGIN;

-- 1. Preview and lock the matching rows; review this output
SELECT id, status, created_at
FROM orders
WHERE status = 'pending' AND created_at < now() - interval '30 days'
FOR UPDATE;

-- 2. Change only the reviewed ids, not the original predicate
UPDATE orders
SET status = 'cancelled'
WHERE id = ANY('{101,102,103}'::bigint[])   -- ids from step 1
RETURNING id;

-- 3. Returned ids identical to the reviewed ids?
ROLLBACK;   -- if anything is off
-- COMMIT;  -- only when the result is exactly what you expected
```

- Preview inside the transaction. Under `READ COMMITTED` each statement takes a fresh snapshot, so a preview run separately (or rerunning the predicate in the `UPDATE`) can match different rows; a matching row count does not prove the same rows changed.
- Decide quickly: locked rows block concurrent writers until `COMMIT` or `ROLLBACK`. See `skills/supabase-postgres-best-practices/references/lock-short-transactions.md`.
- In `psql`, `\set AUTOCOMMIT off` starts an implicit transaction before eligible commands (not e.g. `VACUUM`) when none is open; end it with `COMMIT` or `ROLLBACK`. `\set ON_ERROR_ROLLBACK interactive` uses savepoints so a failed statement in an open transaction does not abort it, for interactive input only (not scripts).

## Transaction Isolation Levels

PostgreSQL defaults to `READ COMMITTED`.

| Level | Dirty Reads | Non-Repeatable Reads | Phantom Reads | Use Case |
|---|---|---|---|---|
| `READ COMMITTED` | No | Possible | Possible | Default OLTP behavior |
| `REPEATABLE READ` | No | No | No in PostgreSQL | Consistent snapshots for calculations or reports |
| `SERIALIZABLE` | No | No | No | Strongest isolation for complex invariants |

PostgreSQL accepts `READ UNCOMMITTED` as a syntax alias for `READ COMMITTED`.

```sql
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ;
COMMIT;
```

`SERIALIZABLE` transactions may fail with serialization errors. Applications must be prepared to retry them.

For application-level coordination, prefer advisory locks over table-level locks:

```sql
SELECT pg_advisory_lock(12345);
SELECT pg_advisory_xact_lock(12345);
SELECT pg_try_advisory_lock(12345);
```
