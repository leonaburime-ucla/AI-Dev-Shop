# SQL Data Modeling Reference: Conventions and Data Types

## Naming Conventions

| Object | Convention | Example |
|---|---|---|
| Tables | plural snake_case | `users`, `invoice_items` |
| Columns | singular snake_case | `first_name`, `created_at` |
| Primary key | `id` | `id uuid PRIMARY KEY` |
| Foreign key | `<entity>_id` | `user_id`, `organization_id` |
| Boolean columns | `is_` or `has_` prefix | `is_active`, `has_verified_email` |
| Timestamp columns | `_at` suffix | `created_at`, `updated_at`, `deleted_at` |
| Indexes | `idx_<table>_<columns>` | `idx_orders_user_id` |
| Unique constraints | `uq_<table>_<columns>` | `uq_users_email` |
| Check constraints | `chk_<table>_<description>` | `chk_orders_amount_positive` |
| FK constraints | `fk_<table>_<referenced_table>` | `fk_orders_users` |

## Data Type Selection

Choose the most precise domain-correct type.

| Domain | Recommended Type | Notes |
|---|---|---|
| External PKs | `uuid` | Use a default generator |
| Internal PKs | `bigint GENERATED ALWAYS AS IDENTITY` | Compact and sequential |
| Short or long text | `text` | Add CHECK only when length is a business rule |
| Fixed-length codes | `char(n)` | Only for truly fixed-length values |
| Money | `numeric(19, 4)` | Never `float` or `real` |
| Counts | `integer` or `bigint` | Use `bigint` when growth is plausible |
| Decimal ratios | `numeric(p, s)` | Make precision explicit |
| Boolean flags | `boolean` | Avoid `0/1` or `Y/N` encodings |
| Datetimes | `timestamptz` | Prefer timezone-aware storage; see Time Zones below |
| Dates only | `date` | When time is irrelevant |
| Durations | `interval` | Supports arithmetic (`ended_at - started_at`, `starts_at + duration`) and `sum()`/`avg()`; not ad hoc integer seconds unless justified |
| Enumerations | `text` with CHECK | Easier to evolve than native enum types; see Enumerations below |
| Semi-structured data | `jsonb` | Prefer over `json` for most app cases |
| Small value lists | `text[]` / `bigint[]` (PostgreSQL) | Bounded, value-like lists only; see Array Columns in `postgresql-engine.md` |
| IP addresses | `inet` | Validates format and supports subnet queries |

Avoid storing UUIDs or structured domain values as plain text when a native type exists.

## Enumerations

Default: `text` plus a `CHECK` constraint.

```sql
status text NOT NULL DEFAULT 'pending'
    CONSTRAINT chk_orders_status CHECK (status IN ('pending', 'paid', 'shipped', 'cancelled'))
```

Adding an allowed value is a constraint swap. On large tables, add the replacement `NOT VALID` (skips the full-table check under the strong lock; new writes are still checked), then `VALIDATE CONSTRAINT` (scans under a lock that allows reads and writes) after the swap commits. Run the drop and add in one short transaction so there is no unconstrained window:

```sql
BEGIN;
ALTER TABLE orders DROP CONSTRAINT chk_orders_status;
ALTER TABLE orders ADD CONSTRAINT chk_orders_status
    CHECK (status IN ('pending', 'paid', 'shipped', 'cancelled', 'refunded')) NOT VALID;
COMMIT;
ALTER TABLE orders VALIDATE CONSTRAINT chk_orders_status;
```

Removing a value: `NOT VALID` leaves old rows in place but rejects any insert or update whose row violates the new check, so ordinary updates to unmigrated rows start failing. First stop writing the old value and migrate existing rows, then swap and validate as above.

When values carry metadata (display label, sort order, active flag) or change often, use a lookup table whose PK is the value itself:

```sql
CREATE TABLE order_statuses (
    status     text PRIMARY KEY,
    label      text NOT NULL,
    sort_order integer NOT NULL,
    is_active  boolean NOT NULL DEFAULT true
);

-- Seed every value present in orders.status (including the default 'pending') before adding the FK
INSERT INTO order_statuses (status, label, sort_order) VALUES
    ('pending', 'Pending', 1), ('paid', 'Paid', 2), ('shipped', 'Shipped', 3),
    ('cancelled', 'Cancelled', 4), ('refunded', 'Refunded', 5);

ALTER TABLE orders ADD CONSTRAINT fk_orders_order_statuses
    FOREIGN KEY (status) REFERENCES order_statuses (status) ON UPDATE CASCADE NOT VALID;
ALTER TABLE orders VALIDATE CONSTRAINT fk_orders_order_statuses;

-- The FK now enforces the domain; a retained CHECK would reject cascaded renames
ALTER TABLE orders DROP CONSTRAINT chk_orders_status;
```

- The referencing column holds the readable value, so reads need no join (a deliberate exception to the `<entity>_id` FK naming). Join only when you need the metadata.
- `ON UPDATE CASCADE` makes renames one statement, but it rewrites every referencing row; plan large renames like a backfill. When renaming the column's default value, change the column `DEFAULT` in the same transaction.
- Set `is_active = false` to mark a value retired while preserving historical references; never delete rows that existing data still references. The flag does not enforce retirement: the FK checks existence only. If new assignments must be rejected, enforce that on insert and on changes to `status` (e.g. a trigger), while permitting unchanged historical values.

Native `ENUM` types (PostgreSQL):

- `ALTER TYPE ... ADD VALUE` works. On an existing enum, `ADD VALUE` cannot run inside a transaction block before PG12. On PG12+ it can, but the new value cannot be used until the transaction commits. Exceptions when the type was created in the same transaction: before PG12 the add was allowed there, and on PG17+ the new value is usable immediately when both commands run at the outermost transaction level.
- `ALTER TYPE ... RENAME VALUE` works on PG10+.
- Values cannot be removed or reordered without creating a new type and migrating every column that uses it.
- Reserve native enums for truly fixed sets.

## Time Zones

- `timestamptz` stores an absolute instant (normalized to UTC internally), not the input's zone. PostgreSQL honors an explicit zone or offset in the input, assumes the session `TimeZone` only when none is supplied, and uses the session zone for display. No conversion trigger or application-side UTC juggling is needed.
- Never use `timestamp` (without time zone) for instants. It stores wall-clock digits with no zone, so the same value means different moments to readers in different zones.
- Keep the server and session `TimeZone` at `UTC` for predictable output; format for display in the application.
- When local wall-clock time is the business rule ("9:00 in the user's zone"), store the IANA zone name separately (`text`, e.g. `'America/New_York'`, never a fixed offset, which breaks across DST) and convert with `AT TIME ZONE` at query time:

```sql
-- the instant of today's 09:00 local time for each user
SELECT u.id,
       (date_trunc('day', now() AT TIME ZONE u.time_zone) + interval '9 hours')
           AT TIME ZONE u.time_zone AS today_9am_local
FROM users u;
```
