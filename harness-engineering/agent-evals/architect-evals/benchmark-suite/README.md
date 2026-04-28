# Architect Scorecard Suite

Suite kind: `benchmark`

Status: `pilot`

Purpose:

- test whether the Architect applies the new architecture scorecard behavior
  consistently
- seed traps around optional-axis activation, separate `modularity` scoring,
  confidence discipline, mitigations, blocking rules, and tradeoff synthesis
- verify that the Blueprint handoff and ADR scorecard changes produce visible,
  auditable downstream behavior

## Coverage

- `35` seeds
- `4` eval projects
- all `Easy`, `Medium`, and `Hard` tiers
- non-trivial seed structures included:
  - `combined`
  - `layered`
  - `distributed`
  - `camouflaged`
  - `interference`

Eval map:

- `eval-1-team-chat-saas`
  - `SEED-AR-01` through `SEED-AR-07`
  - `SEED-AR-22` through `SEED-AR-24`
  - `SEED-AR-33`
  - `SEED-AR-35`
- `eval-2-analytics-export-platform`
  - `SEED-AR-08` through `SEED-AR-14`
  - `SEED-AR-25` through `SEED-AR-27`
  - `SEED-AR-31`
- `eval-3-payments-ledger-modernization`
  - `SEED-AR-15` through `SEED-AR-21`
  - `SEED-AR-28` through `SEED-AR-30`
  - `SEED-AR-32`
- `eval-4-thin-evidence-concept`
  - `SEED-AR-34`

## Target Behavior

This suite is designed to verify that the Architect:

- scores all core axes
- activates optional axes only when the trigger exists
- keeps `modularity` separate from `modifiability`
- includes `confidence`, `strengths`, `weaknesses`, `rationale`,
  `assumptions`, `review_trigger`, and weak-axis `mitigation`
- does not use weighted-sum theater
- names a real `Tradeoff Tension`
- explains `Why This Won`
- compares against the runner-up
- blocks unsafe winners when critical axes collapse

## How To Prepare A Run

```bash
python3 harness-engineering/quality/scripts/prepare_eval_run.py \
  harness-engineering/agent-evals/architect-evals/benchmark-suite \
  run-001
```

The executing LLM should read the fresh `runs/run-001/` copy, produce the
normal ADR output in the eval project run directory, and append exact
model/CLI provenance plus scored seed rows to the suite TSVs.

## Notes

- This suite is benchmark-shaped but not benchmark-certified yet because it has
  not been run and persisted across 3 benchmark passes.
- It intentionally contains traps, tricks, and false-positive bait so the new
  scorecard behavior has to prove itself under pressure.
- The original 30-seed pilot run was archived after external audit feedback in:
  - `reports/history/2026-04-28-pre-revision-30-seed-pilot/`
- The canonical `run-results.tsv` was reset after the suite changed. A fresh Architect run is required before using this revision's
  scores.
- `run-results.tsv` convention: negative-control seeds that are correctly not
  activated may still be recorded as `MISSED` until a distinct
  `CORRECT_SKIP`-style label is introduced.
