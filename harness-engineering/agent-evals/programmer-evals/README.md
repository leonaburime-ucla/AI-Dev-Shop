# Programmer Evals

This bucket keeps Programmer eval artifacts together.

## Layout

- `benchmark-suite/`
  Canonical benchmark suite containing evals 1-9 and suite-scoped TSVs.

## TSV Placement Rule

Keep suite-scoped TSVs at the root of the suite they describe:

- `coverage-matrix.tsv`
- `seed-catalog.tsv`
- `run-results.tsv`

Re-run subsets are derived from saved benchmark results, not committed as
separate suites.
