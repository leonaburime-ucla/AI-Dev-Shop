# Distributed Inventory Allocation - Project Brief

## Overview

The inventory tracker coordinates stock records across tenant-scoped
warehouses, reservation holds, transfer operations, reconciliation snapshots,
idempotent adjustments, and audit trails. The implementation was refactored to
support read-model based allocation and deterministic time handling.

This eval is intentionally focused on Code Review depth. Happy-path tests pass,
but production failures emerge when stale read models, concurrent reservations,
partial transfer failures, reconciliation, idempotency keys, admin overrides,
and shared runtime context interact.

## Requirements

### Functional Requirements

1. Reservation decisions must use a consistency boundary that prevents two
   workers from allocating the same available units.
2. Reconciliation must surface negative stock and oversell incidents instead
   of silently normalizing them away.
3. Transfers must debit the source and credit the destination atomically, or
   compensate the source if the destination write fails.
4. Adjustment idempotency must include tenant, warehouse, SKU, adjustment ID,
   and reason code.
5. Admin overrides must preserve the original requester and approver in audit
   evidence.
6. Tenant and time context must be scoped to each tracker instance so
   reservation expiry and tenant behavior remain deterministic.
7. Tests must cover concurrent reservation, stale read-model allocation,
   transfer failure compensation, reconciliation observability, idempotency
   collisions, override audit identity, and injected-clock behavior.

### Acceptance Criteria

- AC-1: Concurrent reservation attempts cannot oversell a warehouse.
- AC-2: Negative inventory reconciliation produces an explicit oversell signal.
- AC-3: Transfer failure cannot make stock vanish from the source warehouse.
- AC-4: Two adjustments with the same external ID but different warehouse or
  reason code do not collide.
- AC-5: Override audit records include both original requester and approver.
- AC-6: Reservation expiry and audit timestamps are deterministic per tracker
  instance.
- AC-7: The test suite covers the interaction cases above.

## Spec Hash

`spec-inventory-allocation-v6-f340e`
