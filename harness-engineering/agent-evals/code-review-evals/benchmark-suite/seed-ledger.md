# Seed Ledger — Code Review Benchmark Suite

## Included Evals

- `cr-eval-1-order-processor` (easy — 6 seeds)
- `cr-eval-2-notification-service` (medium — 6 seeds)
- `cr-eval-3-inventory-tracker` (hard — 6 seeds)

## Total Seeds

18 seeds across 3 difficulty tiers testing Code Review agent in isolation
with seeded code and fake Programmer handoffs.

## Current Backfill Rule

The suite-level TSV files in this directory are canonical but detailed seed
narratives still live in the per-eval `seed-ledger.md` files until a full
catalog backfill is completed.

## Unresolved Seeds

Previously unresolved seeds (SEED-CR-13 through SEED-CR-16 from
cr-eval-3-inventory-tracker) should be re-evaluated through
`prepare_eval_run.py` targeting that eval, not through a separate rerun suite.
