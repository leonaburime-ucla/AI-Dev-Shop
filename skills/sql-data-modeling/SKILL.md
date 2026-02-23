---
name: sql-data-modeling
version: 1.0.0
last_updated: 2026-02-23
description: Use when designing relational schemas, producing ERDs, planning migrations, selecting data types, defining constraints, or reasoning about normalization and indexing strategy. Platform-agnostic — applies to any SQL database.
---

# Skill: SQL Data Modeling

A schema is a contract. Every downstream agent — Programmer, TDD, Code Review — works against the schema as a stable interface. Get it right before writing any application code. Changing a schema after application code is written is expensive; changing it after data is in production is a risk.

The goal is not the most normalized schema. The goal is a schema that correctly represents the domain, enforces its invariants at the database level, and supports the query patterns the spec requires — with the minimum structural complexity needed to do that.

## ERD Design Principles

An Entity-Relationship Diagram describes what the data is, not how it is stored. Model at this level first, then translate to DDL.

**Entities** are things with an independent existence that the system needs to remember. Each entity becomes a table. Name tables in **plural snake_case** (`users`, `invoice_items`, `audit_logs`).

**Attributes** are facts about an entity. Each attribute becomes a column. Name columns in **singular snake_case** (`first_name`, `created_at`, `is_active`). Do not prefix column names with the table name (`user_id` in the `users` table is redundant; use `id`).

**Relationships** describe how entities relate to each other. Three types:

| Type | Description | Implementation |
|---|---|---|
| One-to-One (1:1) | Each row in A relates to at most one row in B | FK on either side with UNIQUE constraint |
| One-to-Many (1:N) | One row in A relates to many rows in B | FK on the "many" side (B references A) |
| Many-to-Many (M:N) | Many rows in A relate to many rows in B | Junction table with two FKs |

**Cardinality** must be explicit: is the relationship optional (0..1, 0..N) or required (1..1, 1..N)? Optional relationships use nullable FKs. Required relationships use NOT NULL FKs.

## Normalization

Normalization reduces data redundancy and update anomalies. Apply by default; denormalize only with documented justification.

### First Normal Form (1NF)
- Each column holds atomic (indivisible) values — no comma-separated lists, no arrays of values in a single column (use a child table instead)
- Each row is uniquely identifiable (has a primary key)
- No repeating groups of columns (e.g. `phone_1`, `phone_2`, `phone_3` → separate `phone_numbers` table)

### Second Normal Form (2NF)
- Must be in 1NF
- Every non-key column depends on the entire primary key, not just part of it
- Applies when using composite primary keys — if a column depends on only one part of the composite key, it belongs in a separate table

### Third Normal Form (3NF)
- Must be in 2NF
- No transitive dependencies: non-key columns must not depend on other non-key columns
- Example violation: storing both `zip_code` and `city` in `users` — `city` depends on `zip_code`, not on the user's identity. Extract to a `zip_codes` table or accept the redundancy with documented justification.

### When to Denormalize
Denormalization trades write anomaly risk for read performance. Accept it only when:
- A query joins many tables and the join cost is measured and significant
- A derived value is expensive to recompute on every read and the source data changes infrequently
- A reporting table is populated by a controlled process (ETL, trigger) rather than ad-hoc writes

Always document denormalization decisions: what was denormalized, why, which process keeps the derived value in sync, and what breaks if it drifts.

## Primary and Foreign Key Design

**Primary keys**: Use `uuid` (v4 or v7) as the default for any table that will be exposed externally or referenced across services. Use `bigserial` / `bigint GENERATED ALWAYS AS IDENTITY` for internal high-volume tables where sequential IDs are safe and join performance matters. Never use natural keys (emails, usernames, phone numbers) as primary keys — they change.

```sql
-- Preferred for externally visible entities
id uuid PRIMARY KEY DEFAULT gen_random_uuid()

-- Preferred for internal high-volume tables
id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY
```

**Foreign keys**: Always define FK constraints explicitly — do not rely on application code to maintain referential integrity.

```sql
-- Define cascade behavior explicitly on every FK
user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE
order_id uuid NOT NULL REFERENCES orders(id) ON DELETE RESTRICT
```

**Cascade rules**:

| Rule | Behavior | Use When |
|---|---|---|
| `ON DELETE CASCADE` | Child rows deleted when parent is deleted | Child cannot exist without parent (e.g. order items without an order) |
| `ON DELETE RESTRICT` | Delete blocked if children exist | Child can exist independently or deletion requires explicit cleanup |
| `ON DELETE SET NULL` | FK set to NULL when parent is deleted | Child is optional; losing the parent is valid |
| `ON DELETE SET DEFAULT` | FK set to default value when parent is deleted | Reassignment to a default entity is valid (e.g. reassign to a generic owner) |

## Constraint Types

Define constraints at the database level. Application-level validation is a second line of defense — the schema is the first.

```sql
-- NOT NULL: column must always have a value
email text NOT NULL

-- UNIQUE: no two rows can share the same value
email text NOT NULL UNIQUE

-- CHECK: arbitrary condition must be true
amount numeric NOT NULL CHECK (amount > 0)
status text NOT NULL CHECK (status IN ('draft', 'published', 'archived'))

-- Table-level UNIQUE across multiple columns
UNIQUE (user_id, organization_id)

-- Table-level CHECK
CHECK (end_date IS NULL OR end_date > start_date)
```

Prefer table-level constraints over application-level validation for invariants that must hold regardless of which code path writes the data.

## Index Strategy

Indexes speed up reads and slow down writes. Add indexes for the queries the spec actually requires. Do not pre-emptively index every FK or text column.

**When to index**:
- Columns used in `WHERE` clauses with high selectivity (many distinct values)
- Columns used in `JOIN` conditions (FK columns)
- Columns used in `ORDER BY` on large tables
- Columns used in range queries

**When not to index**:
- Low-cardinality columns (boolean flags, small enums) — the planner will prefer a sequential scan
- Columns only used in `SELECT` — covering indexes (see below) handle this as a secondary concern
- Tables with very high write volume where index maintenance cost exceeds read benefit

**Index types**:

| Type | Use Case |
|---|---|
| B-tree (default) | Equality and range queries on any ordered type |
| GIN | Full-text search (`tsvector`), JSONB containment, array operations |
| GiST | Geometric/geographic data, range type containment |
| BRIN | Monotonically increasing columns on very large tables (timestamps, sequential IDs) |
| Hash | Equality-only lookups (rare — B-tree is usually better) |

**Composite indexes**: Column order matters. Put the most selective column first, then the next, etc. A composite index on `(a, b)` supports queries filtering on `a` alone or `a` AND `b`, but not `b` alone.

```sql
-- Supports: WHERE user_id = ? AND created_at > ?
-- Also supports: WHERE user_id = ?
-- Does NOT efficiently support: WHERE created_at > ?
CREATE INDEX idx_events_user_created ON events (user_id, created_at DESC);
```

**Covering indexes**: Include non-filtered columns in the index to enable index-only scans.

```sql
-- Query: SELECT status FROM orders WHERE user_id = ? AND created_at > ?
-- Including status avoids a heap fetch
CREATE INDEX idx_orders_user_created_status ON orders (user_id, created_at DESC) INCLUDE (status);
```

**Partial indexes**: Index only the rows that match a condition. Smaller, faster, and more useful than a full index when most rows will never be queried.

```sql
-- Only index active users — deleted users are never queried by application
CREATE INDEX idx_users_email_active ON users (email) WHERE deleted_at IS NULL;
```

## Migration Planning

A migration is a schema change applied to a running database. The risk is proportional to how much data exists and whether the change blocks writes.

**Classify every change before writing the SQL**:

| Class | Examples | Risk |
|---|---|---|
| Additive | Add column (nullable), add table, add index CONCURRENTLY | Low — does not break existing queries or application code |
| Restrictive | Add NOT NULL to existing column, add FK to existing column | Medium — requires backfilling data before constraint can be enforced |
| Destructive | Drop column, drop table, rename column | High — breaks application code that references the old name; requires coordinated deploy |
| Data-transforming | Change column type, split one column into two | High — requires data migration script, potential for data loss |

**Additive-first principle**: Prefer additive changes. Add the new column, deploy application code that writes to both old and new, backfill, then drop the old column in a follow-up migration.

**Rollback strategy**: For every destructive or data-transforming change, define the rollback before the migration is approved:
- What SQL undoes the change?
- Is data recovery possible, or is this a one-way door?
- What is the point of no return (e.g. after application code that depended on the old column is deleted)?

**Lock awareness**: `ALTER TABLE` on a large table acquires a full table lock by default in PostgreSQL. For high-traffic tables:
- Use `CREATE INDEX CONCURRENTLY` instead of `CREATE INDEX`
- Add nullable columns first, then backfill, then add NOT NULL constraint
- Use `ALTER TABLE ... SET NOT NULL` only after a CHECK constraint has validated existing rows

## Naming Conventions

| Object | Convention | Example |
|---|---|---|
| Tables | plural snake_case | `users`, `invoice_items`, `audit_log_entries` |
| Columns | singular snake_case | `first_name`, `created_at`, `is_published` |
| Primary key | `id` | `id uuid PRIMARY KEY` |
| Foreign key | `<referenced_table_singular>_id` | `user_id`, `organization_id` |
| Boolean columns | `is_` or `has_` prefix | `is_active`, `has_verified_email` |
| Timestamp columns | `_at` suffix | `created_at`, `updated_at`, `deleted_at` |
| Indexes | `idx_<table>_<columns>` | `idx_orders_user_id`, `idx_users_email_active` |
| Unique constraints | `uq_<table>_<columns>` | `uq_users_email` |
| Check constraints | `chk_<table>_<description>` | `chk_orders_amount_positive` |
| FK constraints | `fk_<table>_<referenced_table>` | `fk_orders_users` |

## Junction Tables for Many-to-Many

A many-to-many relationship requires a junction (associative) table. The junction table holds the two FKs as a composite primary key, and may carry attributes of the relationship itself.

```sql
-- Users can belong to many organizations; organizations have many users
CREATE TABLE organization_members (
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id         uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role            text NOT NULL DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member')),
    joined_at       timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (organization_id, user_id)
);

-- Index the reverse lookup (find all organizations for a user)
CREATE INDEX idx_org_members_user ON organization_members (user_id);
```

Name junction tables after the relationship, not a concatenation of the two tables: `organization_members`, not `organizations_users`.

## Soft Delete vs Hard Delete

**Hard delete**: `DELETE FROM table WHERE id = ?` — row is gone.

**Soft delete**: Add a `deleted_at timestamptz` column. Mark as deleted with `UPDATE table SET deleted_at = now() WHERE id = ?`. Row persists.

| Factor | Hard Delete | Soft Delete |
|---|---|---|
| Storage | Reclaimed | Grows indefinitely |
| Audit trail | Lost | Preserved |
| Query complexity | Simple (no filter needed) | Every query must filter `WHERE deleted_at IS NULL` |
| FK referential integrity | Clean | Must decide: cascade soft-delete to children, or allow orphaned children |
| GDPR / right to erasure | Requires true deletion | Soft-deleted rows still contain PII — must hard-delete on erasure request |

Use soft delete when: audit trails are required, data recovery is needed, or related entities reference this one and cascading hard deletes are unsafe.

Use hard delete when: data has no audit value, storage is a concern, or regulatory requirements mandate true erasure.

If using soft delete, create a partial index to keep active-row queries fast:

```sql
CREATE INDEX idx_orders_user_active ON orders (user_id) WHERE deleted_at IS NULL;
```

## Timestamp Conventions

Include these three columns on every table that represents a business entity (not junction tables or lookup tables):

```sql
created_at  timestamptz NOT NULL DEFAULT now()
updated_at  timestamptz NOT NULL DEFAULT now()
deleted_at  timestamptz          -- NULL means active; non-NULL means soft-deleted
```

Always use `timestamptz` (timestamp with time zone), never `timestamp` (without time zone). `timestamp` stores local time with no zone context — values become ambiguous across DST transitions and deployments in different timezones.

Keep `updated_at` current via a trigger or an ORM hook. A stale `updated_at` is worse than no `updated_at` — it creates false confidence about when data was last changed.

```sql
-- Trigger to auto-update updated_at on any row change
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

## Data Type Selection

Choose the most precise type that correctly represents the domain. Overly permissive types (storing a price as `text`, storing an enum as `varchar(255)`) allow invalid data in and force application code to validate what the database could guarantee.

| Domain | Recommended Type | Notes |
|---|---|---|
| Primary keys (external) | `uuid` | Use `gen_random_uuid()` default |
| Primary keys (internal) | `bigint GENERATED ALWAYS AS IDENTITY` | Sequential, compact |
| Short text (< 255 chars) | `text` with CHECK constraint | PostgreSQL `text` and `varchar` are equivalent; prefer `text` |
| Long text | `text` | No length limit; use CHECK only if a domain maximum exists |
| Fixed-length codes | `char(n)` | Only for truly fixed-length values (ISO country codes, etc.) |
| Money / prices | `numeric(19, 4)` | Never use `float` or `real` for money — floating-point rounding errors |
| Whole counts | `integer` or `bigint` | Use `bigint` for anything that could grow large (event counts, sequence numbers) |
| Decimal ratios | `numeric(p, s)` | Specify precision and scale explicitly |
| Boolean flags | `boolean` | Not `integer` 0/1 or `char` Y/N |
| Datetimes | `timestamptz` | Always with time zone |
| Dates only | `date` | When time component is irrelevant (birth dates, due dates) |
| Durations | `interval` | Not an integer count of seconds |
| Enumerations | `text` with CHECK constraint | Prefer over `CREATE TYPE ... AS ENUM` — adding enum values requires DDL; CHECK constraint is altered with a simple migration |
| Semi-structured data | `jsonb` | Not `json` (jsonb is binary-indexed, json is stored as text) |
| IP addresses | `inet` | Not `text` — `inet` validates format and enables subnet queries |
| UUIDs stored as text | Avoid | Use the native `uuid` type |
