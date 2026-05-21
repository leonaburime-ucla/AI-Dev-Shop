# Seed Ledger — Code Review Benchmark Suite

## Included Evals

- `cr-eval-1-order-processor` (easy — 6 seeds)
- `cr-eval-2-notification-service` (medium — 6 seeds)
- `cr-eval-3-inventory-tracker` (hard — 7 seeds)

## Total Seeds

21 seeds across 3 difficulty tiers testing Code Review agent in isolation
with seeded code, fake Programmer handoffs, and suite-level controls.

## Current Backfill Rule

The suite-level TSV files in this directory are canonical but detailed seed
narratives still live in the per-eval `seed-ledger.md` files until a full
catalog backfill is completed.

## Suite-Level Negative Controls

- `SEED-CR-NC-01`: parameterized customer lookup in
  `cr-eval-1-order-processor/seed-state/src/order_processor.py` should not be
  misflagged as SQL injection.
- `SEED-CR-NC-02`: injected clock fallback in
  `cr-eval-3-inventory-tracker/seed-state/src/inventory_tracker.py` should not
  be misflagged as a hidden dependency.

## Unresolved Seeds

Previously unresolved seeds (SEED-CR-13 through SEED-CR-16 from
cr-eval-3-inventory-tracker) should be re-evaluated through
`prepare_eval_run.py` targeting that eval, not through a separate rerun suite.
