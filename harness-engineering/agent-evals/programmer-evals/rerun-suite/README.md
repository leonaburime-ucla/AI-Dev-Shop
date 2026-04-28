# Programmer Rerun Suite

Suite kind: `targeted_regression`

Purpose:

- re-test only the Programmer-owned seeds that were previously `MISSED` or
  `PARTIAL`
- preserve an immutable `seed-state/` fixture for each eval
- save future runs with exact LLM/model/CLI provenance in `run-manifest.tsv`

## Coverage

- `7` unresolved Programmer seeds
- `5` eval projects

Eval map:

- `eval-1-rule-engine`
  - `SEED-1A`
- `eval-2-batch-processor`
  - `SEED-2A`
  - `SEED-2C`
  - `SEED-2D`
- `eval-4-stateful-cache`
  - `SEED-4C`
- `eval-6-task-scheduler`
  - `SEED-CL-TRICK-02`
- `eval-8-access-control`
  - `SEED-CL-14`

## Layout

- `coverage-matrix.tsv`
- `seed-catalog.tsv`
- `seed-ledger.md`
- `controls.md`
- `run-manifest.tsv`
- `run-results.tsv`
- `<eval>/seed-state/`
  - immutable starter fixture
- `<eval>/runs/run-00N/`
  - fresh per-run working copy created from `seed-state/`

## How To Prepare A Run

```bash
python3 harness-engineering/quality/scripts/prepare_eval_run.py \
  harness-engineering/agent-evals/programmer-evals/rerun-suite \
  run-001
```

This creates fresh run workdirs under:

- `<eval>/runs/run-001/project/`
- `<eval>/runs/run-001/project-brief.md`
- `<eval>/runs/run-001/prompts/`
- `<eval>/runs/run-001/reports/`

## What The Executing LLM Should Save

For each eval in the run:

1. Run the Programmer against the fresh `runs/run-001/` copy, not `seed-state/`.
2. Save the Programmer output to `runs/run-001/reports/programmer-handoff.md`.
3. Append one row to `run-manifest.tsv` with:
   - exact `model_id`
   - human-readable `model_label`
   - `cli_name`
   - `cli_version`
   - `selection_source`
   - `run_scope = targeted_regression`
   - the exact `target_seed_ids`
4. Append scored seed rows to `run-results.tsv`.

## Validation

```bash
python3 harness-engineering/validators/validate_eval_suite.py \
  harness-engineering/agent-evals/programmer-evals/rerun-suite \
  --suite-kind targeted_regression
```
