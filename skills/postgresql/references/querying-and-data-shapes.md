# Querying and Data Shapes

Use this reference when the problem is primarily about SQL query structure, hierarchy traversal, JSON-heavy access patterns, or views and materialized views.

## Table Design Guardrails

Apply these defaults before advanced query tuning:

- **Primary keys**: prefer `BIGINT GENERATED ALWAYS AS IDENTITY` unless UUID is required for distributed uniqueness or external opacity.
- **Foreign keys**: PostgreSQL does not auto-index FK columns; add explicit indexes for FK access paths.
- **Type defaults**:
  - use `TIMESTAMPTZ` instead of `TIMESTAMP`
  - use `NUMERIC` for money
  - use `TEXT` by default for strings; add explicit length checks when needed
- **Constraints first**: enforce invariants in schema with `NOT NULL`, `CHECK`, and `UNIQUE` before relying on application validation.
- **Unique-null behavior**: when business rules require nulls to collide, use `UNIQUE ... NULLS NOT DISTINCT` in PG15+.
- **Identifier convention**: use unquoted `snake_case` identifiers.

## CTEs

CTEs give complex queries a readable structure. They are defined with `WITH` and referenced like temporary tables within the query.

```sql
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

In PostgreSQL 12+, CTEs are not materialized by default. Force materialization with `WITH ... AS MATERIALIZED (...)` when you want the CTE to execute exactly once regardless of how many times it is referenced.

## Self-Referencing Tables

Model trees (org charts, threaded comments, category hierarchies) as an adjacency list: a nullable `parent_id` referencing the same table. `NULL` marks a root.

```sql
CREATE TABLE departments (
    id        bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name      text NOT NULL,
    parent_id bigint REFERENCES departments (id),
    CHECK (parent_id <> id)   -- blocks self-parenting only
);
CREATE INDEX idx_departments_parent_id ON departments (parent_id);
```

Index `parent_id`: every traversal step joins on it. The FK guarantees the parent exists, not that the hierarchy is acyclic: longer cycles (A→B→A) remain possible, so traverse with the cycle-guarded recursive CTE below. When "everything under X" subtree queries dominate, consider the `ltree` extension (materialized path with GiST-indexed ancestor/descendant operators), at the cost of rewriting paths when nodes move.

## Recursive CTEs

Recursive CTEs traverse hierarchical or graph-shaped data. They consist of a base case and a recursive term connected with `UNION ALL`.

```sql
WITH RECURSIVE org_tree AS (
    SELECT id, name, parent_id, 0 AS depth
    FROM departments
    WHERE id = $1

    UNION ALL

    SELECT d.id, d.name, d.parent_id, t.depth + 1
    FROM departments d
    INNER JOIN org_tree t ON d.parent_id = t.id
) CYCLE id SET is_cycle USING path   -- PG14+
SELECT id, name, depth
FROM org_tree
WHERE NOT is_cycle
ORDER BY depth, name;
```

Unguarded `UNION ALL` recursion over a cycle runs until canceled or out of resources. Before PG14, carry a visited-id array (`ARRAY[id] AS path` in the base case, `t.path || d.id` plus `WHERE d.id <> ALL(t.path)` in the recursive term), or add a depth limit.

## Window Functions

Window functions compute a value for each row based on a set of related rows without collapsing rows the way `GROUP BY` does.

```sql
SELECT
    user_id,
    order_id,
    created_at,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS rn
FROM orders;

SELECT
    product_id,
    total_sold,
    RANK()       OVER (ORDER BY total_sold DESC) AS rank_with_gaps,
    DENSE_RANK() OVER (ORDER BY total_sold DESC) AS rank_no_gaps
FROM product_sales;

SELECT
    date,
    revenue,
    LAG(revenue, 1) OVER (ORDER BY date) AS prev_day_revenue,
    revenue - LAG(revenue, 1) OVER (ORDER BY date) AS day_over_day_change
FROM daily_revenue;

SELECT
    date,
    amount,
    SUM(amount) OVER (ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total,
    AVG(amount) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS rolling_7_day_avg
FROM transactions;
```

Useful frame clauses:

- `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` for running totals
- `ROWS BETWEEN 6 PRECEDING AND CURRENT ROW` for fixed rolling windows
- `RANGE BETWEEN INTERVAL '7 days' PRECEDING AND CURRENT ROW` for range-based windows on time columns

## JSONB

`jsonb` stores JSON as a parsed binary structure, enabling fast key access and indexing. Prefer `jsonb` over `json`.

### Operators

```sql
SELECT data -> 'address' -> 'city' FROM users;
SELECT data ->> 'email' FROM users;
SELECT data #> '{address, city}' FROM users;
SELECT data #>> '{address, city}' FROM users;
SELECT * FROM users WHERE data @> '{"role": "admin"}';
SELECT * FROM users WHERE data ? 'phone_number';

UPDATE users
SET data = jsonb_set(data, '{address, city}', '"Portland"')
WHERE id = $1;

UPDATE users SET data = data || '{"last_login": "2026-02-23"}' WHERE id = $1;
UPDATE users SET data = data - 'temp_token' WHERE id = $1;
```

### Indexing JSONB

```sql
CREATE INDEX idx_users_data_gin ON users USING GIN (data);
CREATE INDEX idx_users_data_path ON users USING GIN (data jsonb_path_ops);
CREATE INDEX idx_users_role ON users ((data ->> 'role'));
```

Use a GIN index when queries use `@>` or `?` on arbitrary keys. Use an expression B-tree index when queries always filter on the same known key with equality or range.

### Building JSON in SQL

Shape a nested API response in one query instead of N+1 round trips:

```sql
SELECT jsonb_build_object(
    'id', u.id,
    'email', u.email,
    'orders', COALESCE(
        jsonb_agg(jsonb_build_object('id', o.id, 'total', o.total) ORDER BY o.created_at DESC, o.id DESC)
            FILTER (WHERE o.id IS NOT NULL),
        '[]'::jsonb
    )
) AS user_json
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
WHERE u.id = $1
GROUP BY u.id;
```

- `jsonb_agg` over zero rows returns `NULL`, not `[]`; wrap it in `COALESCE(..., '[]'::jsonb)`.
- `FILTER (WHERE ...)` drops the all-`NULL` row a `LEFT JOIN` produces; `ORDER BY` inside the aggregate sets array order; add a unique tie-breaker (`o.id`) when the response order must be deterministic.
- For two or more child collections, use one correlated subquery per collection (`(SELECT jsonb_agg(...) FROM orders o WHERE o.user_id = u.id)`); joining several one-to-many tables multiplies rows.
- `to_jsonb(o)` serializes a whole row: convenient, but it exposes every column. Build explicit objects for API-facing shapes.

Defaults for preferences: store only the user's overrides and merge them over defaults at read time, so changing a default needs no backfill.

```sql
-- user_settings.prefs jsonb NOT NULL CHECK (jsonb_typeof(prefs) = 'object')
SELECT '{"theme": "dark", "locale": "en"}'::jsonb || COALESCE(s.prefs, '{}'::jsonb) AS effective_prefs
FROM users u
LEFT JOIN user_settings s ON s.user_id = u.id
WHERE u.id = $1;
```

- Constrain overrides to objects: with an array, scalar, or JSON `null` operand, `||` returns an array, and SQL `COALESCE` does not catch JSON `null`.
- For two JSON objects, `||` merges only top-level keys: right-hand keys win, and nested objects are replaced, not deep-merged.
- Starting from `users` with a `LEFT JOIN` returns the defaults for users with no settings row.

When stored JSON needs an enforced structure, add a `CHECK (jsonb_matches_schema(...))` constraint via `pg_jsonschema` (see the Extensions table in `database-programmability.md`).

## Views and Materialized Views

- **Views** name a join-heavy query once. Callers filter, sort, and paginate them like a table. Simple views can let caller predicates reach base-table indexes; view definitions (e.g. `LIMIT`, aggregates) and security barriers can prevent pushdown, so verify important queries with `EXPLAIN`.
- **Materialized views** store the result physically. Use them to cache expensive aggregates or report queries where some staleness is acceptable.

```sql
-- PG15+ (security_invoker)
CREATE VIEW order_summaries WITH (security_invoker = true) AS
SELECT o.id, o.created_at, o.total, u.email
FROM orders o
JOIN users u ON u.id = o.user_id;

-- Pin the reporting zone (UTC or the business zone): date_trunc on timestamptz
-- uses the refreshing session's TimeZone, so day boundaries can shift between sessions.
CREATE MATERIALIZED VIEW daily_revenue AS
SELECT (created_at AT TIME ZONE 'UTC')::date AS day, sum(total) AS revenue
FROM orders
GROUP BY 1;

CREATE UNIQUE INDEX uq_daily_revenue_day ON daily_revenue (day);
REFRESH MATERIALIZED VIEW CONCURRENTLY daily_revenue;
```

- Plain `REFRESH MATERIALIZED VIEW` takes an `ACCESS EXCLUSIVE` lock and blocks readers. `CONCURRENTLY` keeps the old contents readable, but requires a unique index on plain columns (no expression or `WHERE` clause) and an already-populated matview. Either way, refresh recomputes the whole query; it is not incremental.
- Schedule refreshes with `pg_cron` (see the Extensions table in `database-programmability.md`).
- Staleness is a product decision: state the acceptable lag in the spec and size the refresh schedule to it.

Security:

- By default, underlying relation privileges and RLS policies are evaluated as the view owner. If the owner bypasses RLS, the view can expose rows the caller could not query directly. On PG15+, `security_invoker = true` uses the caller's privileges and policies (the caller then also needs privileges on the underlying tables). On older versions, revoke untrusted access to views that would expose those rows.
- On Supabase, views are typically owned by `postgres`, which bypasses RLS: a default view can return rows that base-table RLS would hide from the caller, subject to the view's own definition and the caller's privileges on the view. Supabase specifics: the Security checklist in `skills/supabase-upstream/SKILL.md`.
- Materialized views do not apply the base tables' RLS at read time: anyone with `SELECT` sees every row. Grant `SELECT` only to roles authorized for the entire materialized result. Keeping a schema out of the Data API prevents direct API exposure but does not replace SQL grants.
