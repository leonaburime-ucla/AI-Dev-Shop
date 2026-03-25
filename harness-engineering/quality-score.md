# Harness Quality Score

Updated baseline for this repository after the follow-up harness slice landed on 2026-03-22.

Grades are evidence-based summaries, not aspirations. Re-score after meaningful harness changes.

| Area | Grade | Evidence | Why It Is Not Higher Yet |
|---|---|---|---|
| Knowledge Map And Progressive Disclosure | B+ | `AGENTS.md`, `project-knowledge/operations/pipeline-quickstart.md`, `project-knowledge/routing/agent-index.md`, `agents/*/skills.md`, `skills/`, `harness-engineering/references/` | The root map is now safer, but keeping it slim requires ongoing discipline as new framework rules land. |
| Mechanical Enforcement | B | `harness-engineering/validators/`, `.github/framework/workflows/harness-validators.yml`, `harness-engineering/ci-enforcement.md`, `harness-engineering/registry-integrity-policy.md` | More rules are enforced mechanically now, but most behavioral quality rules still depend on markdown gates rather than executable checks. |
| Evaluation And Benchmarking | B- | `framework/reports/benchmarks/README.md`, `framework/reports/benchmarks/spec-agent/`, `framework/reports/benchmarks/architect-agent/`, `framework/reports/benchmarks/tdd-agent/`, `framework/reports/benchmarks/programmer-agent/`, `framework/reports/benchmarks/testrunner-agent/`, `framework/reports/benchmarks/code-review-agent/`, `framework/reports/benchmarks/security-agent/`, `skills/evaluation/eval-rubrics.md` | Benchmarks now span implementation and verification roles, but they are still scenario-based seed fixtures rather than executable eval harnesses. |
| Closed-Loop Feedback | B+ | `project-knowledge/memory/learnings.md`, `agents/observer/skills.md`, `harness-engineering/failure-promotion-policy.md`, `harness-engineering/tripwires.md` | Repeated failures now have promotion and tripwire rules, but the loop is still mostly human-driven rather than automated. |
| Entropy Management | B | `agents/observer/skills.md`, `harness-engineering/observer-cadence.md`, `harness-engineering/validators/doc_garden_audit.py`, `.github/framework/workflows/harness-maintenance.yml`, `framework/reports/maintenance/harness-maintenance.md` | Cleanup is now scheduled and report-driven, but repair automation still opens reviewable PRs instead of silently fixing drift. |
| Self-Validation Loops | C+ | `harness-engineering/self-validation.md`, `framework/templates/self-validation/`, `framework/reports/self-validation/README.md`, `agents/programmer/skills.md`, `framework/workflows/job-lifecycle.md` | The templates and gates now exist, but real downstream repos still need project-specific commands and environment wiring. |
| Run-Level Observability | B- | `.pipeline-state.md`, `framework/templates/progress-ledger-template.md`, `harness-engineering/session-continuity.md`, `harness-engineering/context-offloading.md`, `framework/reports/offloads/README.md`, `framework/workflows/trace-schema.md`, Observer outputs | Resume quality and evidence hygiene are better, but there is still no consolidated dashboard or automatic artifact summarization layer. |

## Overall

Current repo harness maturity: **B**

This repo now has a credible repo-level harness layer: validators, CI wiring, benchmark seeds across upstream and downstream roles, article-local references, runtime self-validation templates, context-offload rules, and a scheduled cleanup cadence. The next leverage point is still the same: convert more recurring failure classes into mechanical checks and executable evals.
