# Controls — Programmer Benchmark Suite

Suite kind: `benchmark`

This suite is the canonical retained benchmark root for Programmer evals.

## Control Status

- per-eval seeded fixtures exist for all evals
- `coverage-matrix.tsv` and `seed-catalog.tsv` are backfilled (74 seeds,
  32 coverage cells)
- per-eval `seed-ledger.md` files remain the detailed seed narrative source

## Current Rule

- use `seed-catalog.tsv` for structured seed lookups
- use `coverage-matrix.tsv` for dimension coverage analysis
- use the per-eval `seed-ledger.md` files for detailed seed narratives
- write future benchmark runs into this suite root, not into a separate suite

## Target Rule

Once backfill is complete, this suite should carry the full benchmark control
definition directly in:

- `coverage-matrix.tsv`
- `seed-catalog.tsv`
- `seed-ledger.md`
- `run-results.tsv`

## Execution Guard

One subagent per eval. See `../../README.md` Execution Guard for the full
rule. Do not batch multiple evals into a single subagent — each eval must
run in its own isolated context loaded with only that eval's brief, prompt,
and seed-state.
