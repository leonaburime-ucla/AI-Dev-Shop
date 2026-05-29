# Seed Ledger - cr-eval-3-inventory-tracker (CR Staff+)

**Eval ID**: benchmark-suite / cr-eval-3-inventory-tracker
**Purpose**: Test Code Review agent on distributed inventory allocation defects
involving stale read models, reservation oversell, transfer compensation,
reconciliation, idempotency, audit identity, clock context, and test design.
**Difficulty**: Hard staff+ fixture.

## Seeds

### SEED-CR-13

Reservation decisions use the published read model instead of an atomic
store-side compare/update. Two workers can both pass the stale availability
check and oversell the same units.

Evidence: `src/inventory_tracker.py` (`InventoryTracker.reserve` and
`InventoryReadModel`).

### SEED-CR-14

Reconciliation clamps negative stock to zero and records a generic event. This
hides oversell incidents instead of emitting an explicit invariant violation.

Evidence: `src/inventory_tracker.py` (`InventoryTracker.reconcile_non_negative`).

### SEED-CR-15

Transfer debits the source before crediting the destination and has no
compensation path if the destination write fails. Stock can vanish under partial
failure.

Evidence: `src/inventory_tracker.py` (`InventoryTracker.transfer`).

### SEED-CR-16

Tests cover simple reservation, transfer, reconciliation, override adjustment,
and injected-clock behavior, but omit concurrent reservation, stale read-model
allocation, destination failure compensation, idempotency collision, and audit
identity assertions.

Evidence: `tests/test_inventory_tracker.py` and fake handoff coverage claim.

### SEED-CR-17

The tracker falls back to module-level tenant and clock state. Instances that
do not inject both dependencies can leak reservation expiry and tenant context
between tests or workers.

Evidence: `src/inventory_tracker.py` (`DEFAULT_CLOCK`, `CURRENT_TENANT`, and
`InventoryTracker.__init__`).

### SEED-CR-18

Admin override writes the approver into the audit actor field, replacing the
original requester. Correct review should require both requester and approver
in audit evidence.

Evidence: `src/inventory_tracker.py` (`InventoryTracker.apply_adjustment`).

### SEED-CR-19

Adjustment idempotency keys omit warehouse and reason code. Two legitimate
adjustments with the same external ID and SKU can collide across warehouses or
business reasons.

Evidence: `src/inventory_tracker.py` (`InventoryTracker.adjustment_key`).

### SEED-CR-NC-02

An explicitly injected `ManualClock` produces deterministic reservation expiry
for that tracker instance. Correct review should not misflag this injected
dependency as hidden time state.

Evidence: `src/inventory_tracker.py` (`ManualClock`) and
`tests/test_inventory_tracker.py`
(`test_injected_clock_controls_reservation_expiry`).

## Scoring Guide

| Score | Criteria |
|-------|----------|
| CAUGHT | CR identifies the seeded issue and its production consequence. |
| PARTIAL | CR identifies a related concern but misses the causal chain or scope. |
| MISSED | CR does not flag the issue. |
| FALSE_POSITIVE | CR flags the injected-clock negative control as a hidden dependency. |
