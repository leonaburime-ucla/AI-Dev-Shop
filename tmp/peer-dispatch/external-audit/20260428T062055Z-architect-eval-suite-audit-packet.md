# External Audit Packet

## Ask

- **User request:** Audit the Architect scorecard eval suite with other LLMs for thoroughness and quality of traps, tricks, negative controls, and overall benchmark usefulness.
- **Audit focus:** Judge whether the suite is a strong and fair test of the Architect agent's new architecture scorecard behavior, including whether the traps are aligned with the current skill and whether any seeds are weak, misleading, or missing.
- **Scope:** custom
- **Suggested changes mode:** notes
- **Audit target:** Explicit file set for the Architect eval suite, the current Architect scorecard skill/ADR contract, the three seeded eval inputs, and the first saved run results.
- **Authoring packet:** `.local-artifacts/external-audit/packets/20260428T062055Z-architect-eval-suite-audit-packet.md`
- **Dispatch packet:** `tmp/peer-dispatch/external-audit/20260428T062055Z-architect-eval-suite-audit-packet.md`

## Work Log

- Added a new architecture scorecard contract to the Architect workflow:
  - core axes always scored
  - optional axes with explicit activation rules
  - `1-5` scale
  - `confidence`
  - `strengths`
  - `weaknesses`
  - `rationale`
  - `assumptions`
  - mitigations for weak scores
  - blocking rules
  - tradeoff synthesis and runner-up comparison
- Built a new eval suite specifically to pressure-test that scorecard behavior rather than generic architecture selection.
- Suite shape:
  - `3` eval projects
  - `30` seeds
  - `Easy`, `Medium`, `Hard`
  - structures include `single`, `combined`, `layered`, `distributed`, `camouflaged`, and `interference`
  - controls include `2` positive controls, `4` negative controls, `1` regression control
- Initially the seeded Architect fixtures were too thin to satisfy the active Speckit provider contract. The suite was then repaired to valid Speckit packages before running the Architect persona.
- The eval was run once using repo-persona Architect subagents, not external peer models.
- Current saved result summary:
  - status `pilot`
  - `96.2%` mean catch rate on non-negative-control seeds
  - `24` caught
  - `2` partial
  - `3` correct negative-control skips
  - `1` false positive
- Main suspected weak point in the suite itself:
  - `SEED-AR-04` is currently marked as a false positive because the Architect activated `compliance_auditability`
  - there is concern that this seed may now be invalid or ambiguous under the broadened optional-axis trigger rule because the fixture includes admin audit logging / evidentiary signals

## Files And Artifacts

| Path | Why it matters |
|---|---|
| `skills/architecture-decisions/SKILL.md` | Source of truth for the new scorecard rules the suite is supposed to test |
| `agents/architect/skills.md` | Shows how the Architect is instructed to apply the scorecard in workflow |
| `framework/templates/adr-template.md` | Output contract the eval expects the Architect to produce |
| `.local-artifacts/agent-evals/architect-scorecard-suite-2026-04-27/README.md` | Suite purpose, coverage, and target behavior |
| `.local-artifacts/agent-evals/architect-scorecard-suite-2026-04-27/coverage-matrix.tsv` | Coverage model for dimensions, structures, and difficulty |
| `.local-artifacts/agent-evals/architect-scorecard-suite-2026-04-27/seed-catalog.tsv` | Canonical seed inventory with dimensions, bug natures, structures, and risk |
| `.local-artifacts/agent-evals/architect-scorecard-suite-2026-04-27/seed-ledger.md` | Human-readable explanation of planted traps |
| `.local-artifacts/agent-evals/architect-scorecard-suite-2026-04-27/controls.md` | Positive / negative / regression control design |
| `.local-artifacts/agent-evals/architect-scorecard-suite-2026-04-27/run-results.tsv` | Saved scoring rows from the first Architect run |
| `.local-artifacts/agent-evals/architect-scorecard-suite-2026-04-27/reports/coordinator-eval-summary.md` | Aggregated current results and obvious weak spots |
| `.local-artifacts/agent-evals/architect-scorecard-suite-2026-04-27/eval-1-team-chat-saas/project-brief.md` | High-level scenario and constraints for eval 1 |
| `.local-artifacts/agent-evals/architect-scorecard-suite-2026-04-27/eval-1-team-chat-saas/seed-state/project/reports/pipeline/201-team-chat-platform/feature.spec.md` | Seeded spec for eval 1 |
| `.local-artifacts/agent-evals/architect-scorecard-suite-2026-04-27/eval-1-team-chat-saas/seed-state/project/reports/pipeline/201-team-chat-platform/system-blueprint.md` | Seeded blueprint for eval 1 |
| `.local-artifacts/agent-evals/architect-scorecard-suite-2026-04-27/eval-1-team-chat-saas/runs/run-architect-001/project/reports/pipeline/201-team-chat-platform/adr.md` | Actual Architect output for eval 1 |
| `.local-artifacts/agent-evals/architect-scorecard-suite-2026-04-27/eval-2-analytics-export-platform/project-brief.md` | High-level scenario and constraints for eval 2 |
| `.local-artifacts/agent-evals/architect-scorecard-suite-2026-04-27/eval-2-analytics-export-platform/seed-state/project/reports/pipeline/202-analytics-export-platform/feature.spec.md` | Seeded spec for eval 2 |
| `.local-artifacts/agent-evals/architect-scorecard-suite-2026-04-27/eval-2-analytics-export-platform/seed-state/project/reports/pipeline/202-analytics-export-platform/system-blueprint.md` | Seeded blueprint for eval 2 |
| `.local-artifacts/agent-evals/architect-scorecard-suite-2026-04-27/eval-2-analytics-export-platform/runs/run-architect-001/project/reports/pipeline/202-analytics-export-platform/adr.md` | Actual Architect output for eval 2 |
| `.local-artifacts/agent-evals/architect-scorecard-suite-2026-04-27/eval-3-payments-ledger-modernization/project-brief.md` | High-level scenario and constraints for eval 3 |
| `.local-artifacts/agent-evals/architect-scorecard-suite-2026-04-27/eval-3-payments-ledger-modernization/seed-state/project/reports/pipeline/203-payments-ledger-modernization/feature.spec.md` | Seeded spec for eval 3 |
| `.local-artifacts/agent-evals/architect-scorecard-suite-2026-04-27/eval-3-payments-ledger-modernization/seed-state/project/reports/pipeline/203-payments-ledger-modernization/system-blueprint.md` | Seeded blueprint for eval 3 |
| `.local-artifacts/agent-evals/architect-scorecard-suite-2026-04-27/eval-3-payments-ledger-modernization/runs/run-architect-001/project/reports/pipeline/203-payments-ledger-modernization/adr.md` | Actual Architect output for eval 3 |

## Validation

- **Checks run:** Architect suite metadata validation; Speckit package validation on all 3 eval fixtures; one full repo-persona Architect subagent run; saved run-results scoring; suite summary generation
- **Checks not run:** No multi-run benchmark repetition yet; no external-peer audit of the suite yet; no second independent scorer pass yet
- **Known caveats:**
  - only `1` saved run, so the suite is `pilot`, not benchmark-certified
  - current cross-dimension stability metric is unavailable because there is no baseline suite for comparison
  - `SEED-AR-04` is the leading candidate for a now-invalid or ambiguous negative control

## Out-Of-Scope Local Changes

- Temporary audit transport files created under `.local-artifacts/external-audit/` and `tmp/peer-dispatch/external-audit/`
- Any unrelated local scratch files outside the Architect eval suite and current Architect scorecard skill surface

## Open Questions

- Is this suite genuinely thorough enough to evaluate the Architect agent's new scorecard behavior, or are major seed classes or traps still missing?
- Are the current traps and tricks fair, well-aligned with the skill, and likely to reveal real reasoning failures instead of baiting arbitrary formatting misses?
- Are the negative controls good negative controls, especially `SEED-AR-04`, `SEED-AR-12`, `SEED-AR-21`, and `SEED-AR-23`?
- Does the suite over-index on one bug nature or one dimension in a way that makes the score look stronger than it is?
- Are there any misleading seeds, weak seeds, duplicate seeds, or seeds that should be split into clearer successor seeds?
- Based on the current files and first run outputs, what would you change before treating this as benchmark-grade?

## Auditor Instructions

Please review this work independently. Use the Ask section's `Audit target` and `Dispatch packet` fields as the source of truth for what to inspect and which packet path was actually handed to you.

This is a review of the **eval suite quality**, not a request to re-architect the sample products.

Return:

1. Start with an `Auditor Scope Check` that restates what you believe you are auditing, the active scope and audit target, which files or artifacts you actually reviewed, and any ambiguity or mismatch you noticed
2. Findings ordered by severity
3. File references when possible
4. Which issues are blockers vs optional improvements
5. What looks solid and should probably stay unchanged
6. Include `Suggested Changes` with file-level edit guidance and concise replacement snippets when useful
7. Do **not** apply edits. Proposed changes are advisory only.
