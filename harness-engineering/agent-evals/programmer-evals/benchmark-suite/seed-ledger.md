# Seed Ledger — Programmer Benchmark Suite

This suite combines the retained Programmer benchmark material that previously
lived in two separate legacy corpora.

## Included Evals

- `eval-1-rule-engine`
- `eval-2-batch-processor`
- `eval-3-adapter-boundary`
- `eval-4-stateful-cache`
- `eval-5-security-query-builder`
- `eval-6-task-scheduler`
- `eval-7-data-pipeline`
- `eval-8-access-control`
- `eval-9-report-generator`

## Data Sources

The suite-level TSVs (`seed-catalog.tsv`, `coverage-matrix.tsv`) are
backfilled and canonical. Per-eval `seed-ledger.md` files remain the
detailed seed narrative source.

## Unresolved Programmer-Owned Seeds

Unresolved or partial Programmer-owned seeds should drive derived re-run
subsets after prompt, guard, or skill changes. They do not require a
separate committed rerun suite.
