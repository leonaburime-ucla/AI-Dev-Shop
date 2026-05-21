# Controls — Code Review Benchmark Suite

Suite kind: `benchmark`

This suite is the canonical benchmark root for Code Review evals.

## Control Status

- per-eval seeded fixtures exist for all 3 evals (easy, medium, hard)
- `coverage-matrix.tsv` and `seed-catalog.tsv` are normalized to the current
  validator taxonomy (`21` seeds, `21` coverage cells)
- suite-level controls now include `1` positive control, `2` negative
  controls, and a retained regression pack
- per-eval `seed-ledger.md` files remain the detailed seed narrative source

## Current Rule

- use `seed-catalog.tsv` for structured seed lookups
- use `coverage-matrix.tsv` for dimension coverage analysis
- use the per-eval `seed-ledger.md` files for detailed seed narratives
- write future benchmark runs into this suite root

## Target Rule

This suite now carries the benchmark control definition directly in:

- `coverage-matrix.tsv`
- `seed-catalog.tsv`
- `seed-ledger.md`
- `run-results.tsv`

## Execution Guard

One subagent per eval. See `../../README.md` Execution Guard for the full
rule. Do not batch multiple evals into a single subagent — each eval must
run in its own isolated context loaded with only that eval's brief, prompt,
and seed-state.
