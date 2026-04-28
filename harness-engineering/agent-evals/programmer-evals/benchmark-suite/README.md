# Programmer Benchmark Suite

This is the canonical benchmark suite root for Programmer evals.

## Scope

- includes evals `1-9`
- combines the former function-quality and checklist/trick-seed corpora into
  one retained benchmark suite
- holds the suite-scoped TSV files used for future validation and scoring

## Canonical Suite Files

The suite-level source of truth lives here:

- `coverage-matrix.tsv`
- `seed-catalog.tsv`
- `seed-ledger.md`
- `controls.md`
- `run-results.tsv`

## Migration Status

- the eval directories have been normalized to `seed-state/` so
  `prepare_eval_run.py` can discover them
- the suite-level TSVs are seeded here as the canonical home for future
  structured benchmark data
- `coverage-matrix.tsv` and `seed-catalog.tsv` are backfilled
