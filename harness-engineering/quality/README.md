# Quality

Quality doctrine, evaluator loops, scorecards, and test-quality references.

## Files

- `evaluation-loops.md` - independent evaluator / judge loops and retained evaluator artifacts
- `eval-coverage-model.md` - shared coverage matrix model for seeded evals: bug nature taxonomy, seed structure taxonomy, difficulty calibration, and control requirements
- `failure-promotion-policy.md` - when recurring failures must become durable harness improvements
- `load-bearing-harness-audit.md` - when to re-test and simplify older harness assumptions
- `quality-score.md` - current repo-level harness quality snapshot
- `function-quality-seeded-evals.md` - seeded eval protocol for testing Programmer, Code Review, and Refactor against function-quality traps
- `agent-isolation-eval-framework.md` - repeatable harness for testing any agent in isolation with seeded defects, hidden ledgers, and post-hoc scoring; includes agent-specific eval designs for Spec, Security, Refactor, Architect, TDD, and Red Team agents
- `templates/` - TSV starter templates for new eval suites (`coverage-matrix`, `seed-catalog`, `run-manifest`, and `run-results`)
- `scripts/prepare_eval_run.py` - creates fresh `runs/<run-id>/` working copies from immutable `seed-state/` fixtures so reruns never overwrite the benchmark inputs
- `scripts/score_eval_suite.py` - computes all required suite-level metrics from `seed-catalog.tsv` + `run-results.tsv`: per-seed catch rate, per-dimension/bug-nature/structure/difficulty breakdowns, false-positive rate, severity accuracy, cross-dimension stability (attention-budget regression detection), negative-control calibration, dimension density, and computed status label
- `spec-definition-of-done.md`
- `agent-performance-scorecard.md`
- `test-first-design-policy.md` — design-stage checklist for making code naturally testable before implementation starts
- `testability-antipatterns.md` — catalog of coding anti-patterns that reduce testability, with required human reporting rule
- `react-component-testing-policy.md` - mandatory component-test expectations when React surfaces are present
- `debug-playbook.md` - debugging workflow support for quality and testability work
