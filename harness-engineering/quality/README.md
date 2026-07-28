# Quality

Quality doctrine, evaluator loops, scorecards, and test-quality references.

Committed seeded eval suites live in `../agent-evals/`. This directory keeps the shared framework and tooling.

## Files

- `evaluation-loops.md` - independent evaluator / judge loops and retained evaluator artifacts
- `eval-coverage-model.md` - shared coverage matrix model for seeded evals: bug nature taxonomy, seed structure taxonomy, difficulty calibration, and control requirements
- `failure-promotion-policy.md` - when recurring failures must become durable harness improvements
- `load-bearing-harness-audit.md` - when to re-test and simplify older harness assumptions
- `model-upgrade-program.md` - formal program for evaluating new models/hosts: triggers, baselines, benchmark packs, ablation modes, retained report fields
- `quality-score.md` - current repo-level harness quality snapshot
- `function-quality-seeded-evals.md` - seeded eval protocol for testing Programmer, Code Inspection, and Refactor against function-quality traps
- `agent-isolation-eval-framework.md` - repeatable harness for testing any agent in isolation with seeded defects, hidden ledgers, and post-hoc scoring; includes agent-specific eval designs for Spec, Security, Refactor, Architect, TDD, and Red Team agents
- `templates/` - TSV starter templates for new eval suites (`coverage-matrix`, `seed-catalog`, `run-manifest`, and `run-results`)
- `scripts/prepare_eval_run.py` - creates fresh `runs/<run-id>/` working copies from immutable `seed-state/` fixtures, and warns when the selected scope should be user-confirmed before dispatch
- `scripts/record_run_manifest.py` - appends or updates `run-manifest.tsv` rows while computing artifact and transcript SHA-256 hashes
- `scripts/score_eval_suite.py` - computes all required suite-level metrics from `seed-catalog.tsv` + artifact-backed `run-results.tsv`: per-seed catch rate, per-dimension/bug-nature/structure/difficulty breakdowns, false-positive rate, severity accuracy, cross-dimension stability (attention-budget regression detection), negative-control calibration, dimension density, and computed status label
- `spec-definition-of-done.md`
- `agent-performance-scorecard.md`
- `test-first-design-policy.md` — design-stage checklist for making code naturally testable before implementation starts
- `testability-antipatterns.md` — catalog of coding anti-patterns that reduce testability, with required human reporting rule
- `coverage-integrity-policy.md` — canonical anti-metric-gaming rule for coverage, test seams, refactoring, and narrow approved exceptions
- `gate-validation-status.md` — which mechanical gates may block and which may not, plus the closed set of canonical integrity findings (`INT-1`…`INT-9`) that block regardless. Each gate's status is recorded there; promotion requires passing the ablation canary specified in that file
- `react-component-testing-policy.md` - mandatory component-test expectations when React surfaces are present
- `debug-playbook.md` - debugging workflow support for quality and testability work

## Drift Sensors

Recurring codebase-health signals that feed into Observer maintenance passes. See `harness-engineering/sensors/README.md` for the full catalog.

Phase 1 sensors:
- `../sensors/code-structure-quality.md` — per-function cognitive complexity, nesting depth, and size on changed code, delta-gated against the merge base
- `../sensors/dependency-structure.md` — dependency cycles and mechanical architecture-boundary checks on changed modules, delta-gated against the merge base
- `../sensors/changed-code-coverage.md` — what fraction of the branches a diff added or modified is exercised; the one gate evaluated absolutely on the diff rather than delta-gated. Distinct from `coverage-quality.md` (trends) and from `test-design`'s suite-level gates
- `../sensors/type-safety.md` — countable unsafe TypeScript operations on changed code, delta-gated; compiler-strictness weakening blocks regardless of the count
- `../sensors/duplication.md` — Type-1/Type-2 clone detection on changed code; gates only when a diff pushes a clone group past three sites (`head > base && head >= 3`), and documents its tension with the complexity gates
- `../sensors/change-history.md` — churn, change frequency, revert/fix frequency, and complexity-joined hotspot tiers; scheduled only, never a PR gate
- `../sensors/dead-code.md` — unused exports, unreachable code, orphaned files
- `../sensors/dependency-drift.md` — outdated deps, vulnerabilities, license issues
- `../sensors/coverage-quality.md` — test coverage **trends** and critical-path gaps. Not a changed-code gate — see `changed-code-coverage.md` for that
