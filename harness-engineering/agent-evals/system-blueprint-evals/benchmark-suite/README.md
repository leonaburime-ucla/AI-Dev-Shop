# System Blueprint Benchmark Suite

Canonical seeded eval suite for the System Blueprint agent.

- Agent under test: `system-blueprint`
- Source design: `../system-blueprint-eval-design.md`
- Suite shape: 30 seeds across 3 flattened `seed-state/` mini-projects
- Seed-state status: initial fixtures created for all three evals
- Run history: none yet; `run-manifest.tsv` and `run-results.tsv` are header-only
- Default execution mode: `repo_persona_subagent`

## Evals

- `system-blueprint-eval-1-scope-boundaries` tests scope normalization, MVP/non-goal boundaries, domain ownership, integration unknowns, macro-level restraint, and contradiction or ownership escalation.
- `system-blueprint-eval-2-topology-tradeoffs` tests the mandatory human tradeoff checkpoint, high-level runtime/data topology, max-three unscored quality attributes, constraint adherence, API/event boundary mapping, and non-binding ADR restraint.
- `system-blueprint-eval-3-decomposition-handoff` tests thin Core/Foundation, dependency-aware spec sequencing, foreign-key owner ordering, vertical-slice default, critical cross-domain journeys, and Spec handoff completeness.

## Suite Artifacts

- `coverage-matrix.tsv`
- `seed-catalog.tsv`
- `seed-ledger.md`
- `controls.md`
- `run-manifest.tsv`
- `run-results.tsv`

## Validation

```bash
python3 harness-engineering/validators/validate_eval_suite.py harness-engineering/agent-evals/system-blueprint-evals/benchmark-suite
```

## Prepare One Eval Run

```bash
python3 harness-engineering/quality/scripts/prepare_eval_run.py \
  harness-engineering/agent-evals/system-blueprint-evals/benchmark-suite \
  run-001 \
  --eval system-blueprint-eval-1-scope-boundaries
```

After a real agent run, persist run proof in `run-manifest.tsv` first, then score each seed in `run-results.tsv`.
