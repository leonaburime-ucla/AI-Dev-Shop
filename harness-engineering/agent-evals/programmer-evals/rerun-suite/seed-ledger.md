# Seed Ledger — Programmer Rerun Suite

This suite is derived from the unresolved Programmer seeds in:

- `full-suite`
- `checklist-suite`

It intentionally reruns only the Programmer-owned seeds that were previously
`MISSED` or `PARTIAL`.

## Seeds

### eval-1-rule-engine

`SEED-1A`
- Source suite: `full-suite`
- Prior result: `MISSED`
- Seeded issue: Bulk discount still checks line-item quantity instead of
  aggregate quantity across duplicate SKUs. `6 + 5` of the same SKU should
  trigger the bulk rule.
- Expected signal: Programmer adds an aggregate probe or direct logic fix for
  repeated SKUs.

### eval-2-batch-processor

`SEED-2A`
- Prior result: `MISSED`
- Seeded issue: Per-item user lookups remain in the processing path.
- Expected signal: Programmer recognizes and fixes N+1 lookup shape.

`SEED-2C`
- Prior result: `MISSED`
- Seeded issue: Retry path can duplicate a send because no idempotency
  strategy is present.
- Expected signal: Programmer introduces idempotency keying or equivalent
  duplicate-send protection.

`SEED-2D`
- Prior result: `PARTIAL`
- Seeded issue: Randomness was handled, but direct time dependency remained.
- Expected signal: Programmer removes or injects the clock dependency.

### eval-4-stateful-cache

`SEED-4C`
- Prior result: `PARTIAL`
- Seeded issue: Cleanup only occurs on access; stale clients can accumulate
  without a cap or periodic pruning strategy.
- Expected signal: Programmer adds an explicit bounds strategy.

### eval-6-task-scheduler

`SEED-CL-TRICK-02`
- Prior result: `PARTIAL`
- Seeded issue: `remainingCapacity` sounds correct but hides a stale metric
  choice. The name/value mismatch is the point of the trap.
- Expected signal: Programmer questions the variable semantics during the
  skepticism pass or fixes the metric.

### eval-8-access-control

`SEED-CL-14`
- Prior result: `MISSED`
- Seeded issue: Role-service access path still has no explicit size cap and
  no timeout guard.
- Expected signal: Programmer adds bounded behavior for service-backed role
  collections.
