# Inventory Tracker — Project Brief

## Overview

A warehouse inventory tracking system that manages stock levels across multiple
warehouses. Supports stock adjustments (add/remove), bulk operations, transfers
between warehouses, capacity enforcement, and stock history logging for audit.

## Requirements

### Functional Requirements

1. **Stock adjustment**: Add or remove stock for a product in a warehouse.
   Negative quantities (removal) must be validated against current stock.
2. **Bulk adjustment**: Apply multiple stock adjustments atomically. If any
   individual adjustment fails validation, skip it and continue with the rest
   (partial success). Errors must be collected and returned to the caller.
3. **Warehouse transfer**: Move stock from one warehouse to another. Transfers
   should not double-count — the total inventory across all warehouses must
   remain constant after a transfer.
4. **Capacity enforcement**: Each warehouse has a `maxCapacity`. Stock additions
   that would cause the warehouse stock to reach capacity must be rejected. The
   warehouse must always have room for at least one more unit.
5. **Aggregate reporting**: Compute total stock across all warehouses for a
   product. Transfers must not inflate totals.
6. **Stock history**: Every adjustment is logged with timestamp, product ID,
   warehouse ID, quantity change, resulting stock level, and the user ID of
   the requester.

### Non-Functional Requirements

1. All async operations should clean up timer state properly.
2. Admin overrides should still record the original requester in audit logs
   (not the admin who approved the override).
3. Bulk operations must surface individual item errors, not swallow them.

### Acceptance Criteria

- AC-1: Stock adjustments correctly increase/decrease warehouse stock.
- AC-2: Negative adjustments that would result in negative stock are rejected.
- AC-3: Bulk adjustments continue past individual failures and collect all errors.
- AC-4: Transfers do not double-count in aggregate totals.
- AC-5: Capacity is enforced: reject when adding would cause stock to reach maxCapacity.
- AC-6: History log records the original requester, even for admin-override operations.
- AC-7: Async tests clean up timer state between test runs.

## Spec Hash

`spec-inv-tracker-v4-ghi789`
