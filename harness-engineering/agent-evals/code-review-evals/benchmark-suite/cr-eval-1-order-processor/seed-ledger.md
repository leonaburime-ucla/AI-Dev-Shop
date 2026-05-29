# Seed Ledger - cr-eval-1-order-processor (CR Staff+)

**Eval ID**: benchmark-suite / cr-eval-1-order-processor
**Purpose**: Test Code Review agent on order/payment saga defects involving
external payment side effects, reservation TTLs, compensation, tenant scoping,
status replay, and saga observability.
**Difficulty**: Hard staff+ fixture with one easy positive control for baseline
calibration.

## Seeds

### SEED-CR-01

Payment capture happens before the durable idempotency record is written. A
worker crash after capture but before recording the key can double-charge on
retry.

Evidence: `src/order_processor.py` (`OrderSaga.place_order`).

### SEED-CR-02

Positive control: `lookup_order_admin` returns an order by ID without tenant
scope. Correct review should catch this obvious cross-tenant lookup defect.

Evidence: `src/order_processor.py` (`OrderStore.lookup_order_admin`).

### SEED-CR-03

The inventory reservation TTL is shorter than the payment capture timeout. A
late capture can confirm an order after inventory was released to another
customer.

Evidence: `src/order_processor.py` (`OrderSaga.place_order`) and
`project-brief.md` (AC-2).

### SEED-CR-04

Compensation refunds payment and releases inventory but omits promotion-credit
ledger reversal. Correct review flags data loss in rollback accounting.

Evidence: `src/order_processor.py` (`OrderSaga.cancel_order`) and fake handoff
compensation claim.

### SEED-CR-05

Replayed `payment_captured` events can move a refunded order back to confirmed.
Correct review flags missing terminal-state transition guards.

Evidence: `src/order_processor.py` (`OrderSaga.apply_gateway_event`).

### SEED-CR-06

Saga events omit payment intent, reservation ID, idempotency key, compensation
ID, and tenant source. Correct review treats this as incident reconstruction
risk, not cosmetic logging.

Evidence: `src/order_processor.py` (`SagaAudit`).

### SEED-CR-NC-01

`IdempotentReceiptStore.complete_once` returns the prior receipt for duplicate
keys. Correct review should not misflag this as skipped payment work.

Evidence: `src/order_processor.py` (`IdempotentReceiptStore`) and
`tests/test_order_processor.py` (`test_idempotent_receipt_store_returns_prior`).

## Scoring Guide

| Score | Criteria |
|-------|----------|
| CAUGHT | CR identifies the seeded issue and its production/security consequence. |
| PARTIAL | CR identifies a related concern but misses the causal chain or severity. |
| MISSED | CR does not flag the issue. |
| FALSE_POSITIVE | CR flags a negative-control behavior as a defect. |
