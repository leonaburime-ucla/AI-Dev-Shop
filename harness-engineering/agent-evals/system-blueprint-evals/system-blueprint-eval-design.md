# System Blueprint Eval Seed Design

## Metadata

- Design date: 2026-05-11
- Source cowork run: `20260511T003333Z`
- Status: generated pilot benchmark suite design
- Scope: System Blueprint agent only
- Suite path: `harness-engineering/agent-evals/system-blueprint-evals/benchmark-suite`
- Fixture status: created

## Model Provenance

- Primary design and implementation: Codex, `gpt-5.5`
- Independent design critique: Gemini, `gemini-3.1-pro-preview`
- Independent design critique: Claude, `us.anthropic.claude-opus-4-6-v1[1m]`; first dispatch failed before inference because the local default selected an invalid newer model id, then retry succeeded with the saved model id.
- Raw cowork artifacts: `ADS-project-knowledge/.local-artifacts/cowork/runs/20260511T003333Z/`

## Suite Shape

- Seeds: 30
- Dimensions: 3
- Standard flaw seeds: 18
- Positive controls: 3
- Regression seeds: 3
- Negative controls: 6
- Scoring target: 24 flaw-catching seeds and 6 false-positive controls
- Status expectation: pilot until 36+ seeds and retained benchmark runs exist

## Dimensions

- `1. Scope, Domain Boundaries & Ownership`
- `2. Topology, Constraints & Quality Attributes`
- `3. P0 Foundation, Dependency Sequencing & Handoff`

## Design Notes

- This suite tests macro blueprint behavior before Spec dispatch, not feature specification or ADR production.
- The mandatory tradeoff discussion is evaluated as checkpoint/restraint behavior: if no human preference has been collected, the correct output is to present options and pause rather than finalize a blueprint.
- Seed traps are grounded in `agents/system-blueprint/skills.md`, `skills/system-blueprint/SKILL.md`, and `framework/templates/system-blueprint-template.md`.
- The suite scores visible output obligations instead of internal conditional-skill activation.
- Negative controls test restraint against over-decomposition, forced quality counts, and invented ownership uncertainty.

## Seed Outline

| Seed | Eval | Dimension | Control | Final trap |
|---|---|---|---|---|
| SBP-SEED-01 | system-blueprint-eval-1-scope-boundaries | 1 | positive_control | Contradictory scope blocks stable decomposition. |
| SBP-SEED-02 | system-blueprint-eval-1-scope-boundaries | 1 | standard | Blueprint omits non-goals and exclusions. |
| SBP-SEED-03 | system-blueprint-eval-1-scope-boundaries | 1 | standard | Deferred marketplace/chatbot is pulled into MVP. |
| SBP-SEED-04 | system-blueprint-eval-1-scope-boundaries | 1 | standard | Subscription ownership conflict is not marked. |
| SBP-SEED-05 | system-blueprint-eval-1-scope-boundaries | 1 | standard | CRM integration boundary is omitted. |
| SBP-SEED-06 | system-blueprint-eval-1-scope-boundaries | 1 | standard | Blueprint writes feature-level acceptance criteria. |
| SBP-SEED-07 | system-blueprint-eval-1-scope-boundaries | 1 | standard | Offline-only conflicts with real-time centralized sync. |
| SBP-SEED-08 | system-blueprint-eval-1-scope-boundaries | 1 | regression | Blueprint imports prior-project domains. |
| SBP-SEED-09 | system-blueprint-eval-1-scope-boundaries | 1 | negative_control | User-mandated monolith should not be over-decomposed. |
| SBP-SEED-10 | system-blueprint-eval-1-scope-boundaries | 1 | negative_control | Deferred admin/reporting should not enter MVP. |
| SBP-SEED-11 | system-blueprint-eval-2-topology-tradeoffs | 2 | positive_control | Agent commits stack before human tradeoff checkpoint. |
| SBP-SEED-12 | system-blueprint-eval-2-topology-tradeoffs | 2 | standard | More than three or scored quality attributes are emitted. |
| SBP-SEED-13 | system-blueprint-eval-2-topology-tradeoffs | 2 | standard | Background worker topology is missing. |
| SBP-SEED-14 | system-blueprint-eval-2-topology-tradeoffs | 2 | standard | Data ownership uncertainty is not surfaced. |
| SBP-SEED-15 | system-blueprint-eval-2-topology-tradeoffs | 2 | standard | Event/API boundary is absent or mislabeled. |
| SBP-SEED-16 | system-blueprint-eval-2-topology-tradeoffs | 2 | standard | Blueprint produces binding ADR language. |
| SBP-SEED-17 | system-blueprint-eval-2-topology-tradeoffs | 2 | standard | Hard no-SaaS constraint is violated. |
| SBP-SEED-18 | system-blueprint-eval-2-topology-tradeoffs | 2 | regression | Quality attributes are scored in a matrix. |
| SBP-SEED-19 | system-blueprint-eval-2-topology-tradeoffs | 2 | negative_control | Naming only two quality attributes is valid. |
| SBP-SEED-20 | system-blueprint-eval-2-topology-tradeoffs | 2 | negative_control | Clear ownership should not get invented uncertainty markers. |
| SBP-SEED-21 | system-blueprint-eval-3-decomposition-handoff | 3 | positive_control | Spec decomposition lacks P0 Core/Foundation. |
| SBP-SEED-22 | system-blueprint-eval-3-decomposition-handoff | 3 | standard | P0 includes feature-owned schema/business logic. |
| SBP-SEED-23 | system-blueprint-eval-3-decomposition-handoff | 3 | standard | Reporting races ahead of Billing-owned foreign key. |
| SBP-SEED-24 | system-blueprint-eval-3-decomposition-handoff | 3 | standard | Depends on is empty despite API/event/schema dependency. |
| SBP-SEED-25 | system-blueprint-eval-3-decomposition-handoff | 3 | standard | Cross-domain critical journeys are omitted. |
| SBP-SEED-26 | system-blueprint-eval-3-decomposition-handoff | 3 | standard | Horizontal slices are used without justification. |
| SBP-SEED-27 | system-blueprint-eval-3-decomposition-handoff | 3 | standard | Spec handoff lacks approved boundaries/open decisions. |
| SBP-SEED-28 | system-blueprint-eval-3-decomposition-handoff | 3 | regression | Agent writes detailed feature specs. |
| SBP-SEED-29 | system-blueprint-eval-3-decomposition-handoff | 3 | negative_control | Justified foundation/platform slice is acceptable. |
| SBP-SEED-30 | system-blueprint-eval-3-decomposition-handoff | 3 | negative_control | Valid thin P0 should not trigger invented business-logic findings. |

## Acceptance Checks For Suite Generation

- `validate_eval_suite.py` must pass for `benchmark-suite`.
- Every seed must map to an explicit persona, skill, template, or governance requirement.
- Every negative control must be genuine false-positive bait.
- `run-manifest.tsv` and `run-results.tsv` stay header-only until real isolated eval runs are recorded.
- The agent under test must not see `seed-catalog.tsv`, `seed-ledger.md`, or `controls.md` during a run.
