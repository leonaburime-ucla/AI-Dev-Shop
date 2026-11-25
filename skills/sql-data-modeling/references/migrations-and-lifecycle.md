# SQL Data Modeling Reference: Migrations and Lifecycle

## Schema Change Discipline

- Every schema change is a version-controlled migration file committed with the code that depends on it. No ad-hoc DDL against production: out-of-band changes drift from the migration history and break later deploys.
- Migrations must apply cleanly, in order, to an empty database. Verify clean replay (migrations plus seed data) in disposable local and CI databases. Apply migrations forward to persistent staging and verify the upgrade path there; rebuild staging only when it is designated disposable.
- Never copy production data into dev or test environments. Use synthetic seed data or a properly anonymized subset; production rows carry PII and compliance obligations.
- Supabase CLI workflow: `skills/supabase-upstream/SKILL.md` (Making and Committing Schema Changes).

## Migration Planning

Classify the change before writing SQL.

| Class | Examples | Risk |
|---|---|---|
| Additive | add table, add nullable column, add compatible index | low |
| Restrictive | add NOT NULL, add FK to existing data | medium |
| Destructive | drop or rename schema objects | high |
| Data-Transforming | change type, split or merge columns | high |

Prefer additive-first rollout:

1. add new structure
2. deploy compatible application behavior
3. backfill or dual-write if needed
4. remove old structure later

For destructive or transforming changes, define rollback thinking before approval.

## Lock Awareness

On large live tables:

- prefer `CREATE INDEX CONCURRENTLY` where supported
- add nullable columns first
- backfill before enforcing NOT NULL
- validate before tightening constraints

## Soft Delete vs Hard Delete

Soft delete adds lifecycle complexity and storage growth in exchange for recovery and audit value.

```sql
CREATE INDEX idx_orders_user_active ON orders (user_id) WHERE deleted_at IS NULL;
```

Use soft delete when recovery, auditability, or relationship safety matters.

Use hard delete when true erasure or simplicity matters. "Never delete data" is wrong when legal erasure (e.g. GDPR right to erasure) or retention limits apply: those require a hard delete or irreversible anonymization. Soft delete, or moving a row to an archive, does not itself satisfy them: define how identifiable retained copies (archives, backups, derived tables) are handled, and account for lawful retention exceptions. Append-only records: see the ledger/audit rule in `../SKILL.md` (Implementation Defaults).

When using soft delete:

- Use `deleted_at timestamptz`, not an `is_deleted` boolean; it records when, and `NULL` means live.
- An active-rows view is a read convenience: the filter applies only to queries through the view, and a security-invoker view still requires base-table privileges, and direct queries are subject only to base-table RLS. If callers may read live rows but not deleted ones, enforce that with a base-table RLS policy (grants cannot hide individual rows). On PG15+, create the view with `security_invoker = true` to preserve the caller's RLS; on older versions, do not expose an owner-checked view as a substitute for those policies (see Views and Materialized Views in `skills/postgresql/references/querying-and-data-shapes.md`).
- For active-only uniqueness (deleted rows do not block re-use), use a partial unique index. It permits reuse only after the overlapping full `UNIQUE` is removed, and a partial index cannot back an FK, so check FK dependencies first. On a large live table, build it with `CREATE UNIQUE INDEX CONCURRENTLY` outside a transaction block, then drop the old uniqueness once the new index is valid.
- Keep soft-deleted rows in place; move them to archive tables only when volume or a retention policy demands it.

```sql
-- PG15+ (security_invoker)
CREATE VIEW active_users WITH (security_invoker = true) AS
SELECT id, email, created_at FROM users WHERE deleted_at IS NULL;

CREATE UNIQUE INDEX CONCURRENTLY uq_users_email_active ON users (email) WHERE deleted_at IS NULL;
```

## Timestamp Conventions

Common lifecycle columns:

```sql
created_at timestamptz NOT NULL DEFAULT now()
updated_at timestamptz NOT NULL DEFAULT now()
deleted_at timestamptz
```

Use `timestamptz`, not timezone-less timestamps.

If `updated_at` exists, maintain it reliably; append-only tables are exempt from the `updated_at` convention (see `../SKILL.md`, Implementation Defaults):

```sql
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_set_updated_at
BEFORE UPDATE ON orders
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```
