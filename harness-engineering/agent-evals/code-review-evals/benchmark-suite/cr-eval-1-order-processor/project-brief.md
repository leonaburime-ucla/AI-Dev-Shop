# Order Processor Saga - Project Brief

## Overview

The order processor coordinates a payment capture, inventory reservation,
promotion-credit ledger, fulfillment status machine, and tenant-scoped order
lookup. The implementation moved from a synchronous request handler to a
payment/order saga that must remain safe under retries, delayed gateway
callbacks, reservation expiry, and compensation.

This eval is intentionally focused on Code Review depth. The code looks like a
reasonable saga implementation and the tests cover normal placement, duplicate
receipt returns, and cancellation, but production failures emerge only when
payment idempotency, inventory TTLs, compensation ledgers, tenant scoping, and
status replay interact.

## Requirements

### Functional Requirements

1. Payment capture must be idempotent before external side effects can be
   retried.
2. Inventory reservation TTL must outlive every payment capture and callback
   path that can complete an order.
3. Compensation must refund payment, release inventory, and reverse promotion
   credits as one auditable saga step.
4. Status events must enforce legal state transitions and reject replayed
   callbacks for terminal states.
5. Order lookup and status mutation must always be scoped by tenant.
6. Saga telemetry must include order ID, tenant, payment intent, reservation
   ID, idempotency key, and compensation ID.
7. Tests must cover duplicate capture, reservation expiry, compensation
   failures, tenant collisions, terminal-state replay, and telemetry fields.

### Acceptance Criteria

- AC-1: A retried capture with the same idempotency key cannot double-charge.
- AC-2: Payment success cannot confirm an order after its inventory reservation
  expired and was released.
- AC-3: Compensation failures are surfaced and do not mark the saga rolled
  back.
- AC-4: Replayed status callbacks cannot move terminal orders back to active
  states.
- AC-5: Cross-tenant order IDs cannot read or mutate another tenant's order.
- AC-6: Saga logs and metrics expose enough fields to reconstruct failures.
- AC-7: The test suite covers the interaction cases above.
## Spec Hash

`spec-order-saga-v2-bcd890`
