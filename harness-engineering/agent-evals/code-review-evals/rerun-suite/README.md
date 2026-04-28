# Code Review Rerun Suite

Suite kind: `targeted_regression`

Purpose:

- re-test only the Code Review seeds that remained unresolved in persisted
  source-of-truth artifacts
- freeze the exact buggy code plus fake Programmer handoff in immutable
  `seed-state/`
- save future runs with exact LLM/model/CLI provenance in `run-manifest.tsv`

## Coverage

- `4` unresolved Code Review seeds
- `1` eval project

Eval map:

- `eval-3-inventory-tracker`
  - `SEED-CR-13`
  - `SEED-CR-14`
  - `SEED-CR-15`
  - `SEED-CR-16`

## Why Only These Seeds

This rerun suite uses only persisted unresolved seeds from the saved CR
artifacts. Later chat-only rerun claims were not treated as canonical because
they were not fully saved as suite artifacts.

## How To Prepare A Run

```bash
python3 harness-engineering/quality/scripts/prepare_eval_run.py \
  harness-engineering/agent-evals/code-review-evals/rerun-suite \
  run-001
```

The executing LLM should review the fresh `runs/run-001/` copy, save its
report to `runs/run-001/reports/code-review-report.md`, and append model/CLI
provenance plus scored seed rows to the suite TSVs.
