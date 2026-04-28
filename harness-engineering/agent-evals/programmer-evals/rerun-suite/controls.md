# Controls — Programmer Rerun Suite

Suite kind: `targeted_regression`

This suite derives from previously scored benchmark candidates:

- `harness-engineering/agent-evals/programmer-evals/full-suite/`
- `harness-engineering/agent-evals/programmer-evals/checklist-suite/`

Why only these seeds:

- The user asked for multi-run reruns only on seeds the agent did not catch
  cleanly.
- Re-running stable passes would add cost without answering whether the misses
  improved.

Control pack:

- Regression seeds: `SEED-1A`, `SEED-2A`, `SEED-2C`, `SEED-2D`, `SEED-4C`,
  `SEED-CL-TRICK-02`, `SEED-CL-14`

This rerun suite is not a full benchmark recertification. It is a focused
follow-up instrument for unresolved Programmer behavior only.
