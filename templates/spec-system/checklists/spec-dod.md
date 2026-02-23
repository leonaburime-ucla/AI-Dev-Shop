# Spec Definition of Done (DoD) Checklist: <feature-name>

<!-- SPEC PACKAGE FILE: templates/spec-system/checklists/spec-dod.md -->
<!-- Part of the spec-system package. See templates/spec-system/ for all required files. -->

---

## Header Metadata

| Field | Value |
|-------|-------|
| spec_id | SPEC-<NNN> |
| feature_name | FEAT-<NNN>-<short-feature-name> |
| version | <semver — must match feature.spec.md version> |
| filled_by | <Spec Agent ID> |
| filled_date | <ISO-8601 UTC> |
| reviewed_by | <Coordinator or human reviewer> |
| reviewed_date | <ISO-8601 UTC> |

---

## How to Use This Checklist

- Each item has a **Status** field: `PASS`, `FAIL`, or `NA`.
- `PASS` — the item is fully satisfied. No caveats.
- `FAIL` — the item is not satisfied. The spec must be updated before handoff. Record what is missing in the Notes column.
- `NA` — the item genuinely does not apply to this feature. Requires written justification in the Notes column. "Not applicable" alone is not a valid justification.
- **Every item must have a status.** A blank status is treated as FAIL.
- **The spec is NOT ready for Architect dispatch until all items are PASS or NA.**
- If an item cannot be brought to PASS after two revision attempts, escalate to human with the specific blocking item and the reason it cannot pass.

---

## Section A: Spec Package Completeness

*Verifies that all required files in the spec-system package are present and non-empty.*

| # | Item | Status | Notes |
|---|------|--------|-------|
| A-01 | `spec.md` (feature.spec.md template) is present in the feature folder | | |
| A-02 | `spec.md` is non-empty — all placeholder values have been replaced with real content | | |
| A-03 | `api.spec.ts` is present (or explicitly marked NA with justification if feature has no API) | | |
| A-04 | `state.spec.ts` is present (or explicitly marked NA with justification if feature has no state) | | |
| A-05 | `orchestrator.spec.ts` is present (or explicitly marked NA with justification if feature has no orchestrator) | | |
| A-06 | `ui.spec.ts` is present (or explicitly marked NA with justification if feature has no UI) | | |
| A-07 | `errors.spec.ts` is present (or explicitly marked NA with justification if feature defines no error codes) | | |
| A-08 | `behavior.spec.md` is present (or explicitly marked NA with justification if feature has no ordering/precedence/dedup rules) | | |
| A-09 | `traceability.spec.md` is present and all REQ-* and AC-* rows are populated (may be "pending implementation") | | |
| A-10 | `checklists/requirements.md` (legacy checklist) is present and filled | | |

---

## Section B: feature.spec.md Quality

*Verifies the primary spec document is complete and meets quality standards.*

| # | Item | Status | Notes |
|---|------|--------|-------|
| B-01 | `spec_id` is assigned and unique (verified against existing `AI-Dev-Shop/specs/` folders) | | |
| B-02 | `version` is set to correct semver (1.0.0 for new specs) | | |
| B-03 | `status` is APPROVED (not DRAFT or IN-REVIEW) | | |
| B-04 | `content_hash` is computed and recorded — matches sha256 of content below the header block | | |
| B-05 | `feature_name` matches the FEAT folder name exactly (case-sensitive) | | |
| B-06 | `last_edited` is a valid ISO-8601 UTC timestamp | | |
| B-07 | `owner` is set to a named human or team (not blank, not "TBD") | | |
| B-08 | Overview section is present and describes the feature in 1–3 sentences | | |
| B-09 | Problem Statement is present with Current state, Desired state, and Success signal | | |
| B-10 | Scope: In-scope list is present and non-empty | | |
| B-11 | Scope: Out-of-scope list is present and non-empty | | |
| B-12 | Zero `[NEEDS CLARIFICATION]` markers remain anywhere in spec.md | | |
| B-13 | All Open Questions have an owner AND a resolution target date | | |
| B-14 | Requirements section has at least one REQ-* item | | |
| B-15 | All REQ-* items are observable and testable — no vague qualifiers ("fast", "robust", "intuitive", "seamless", "easy") | | |
| B-16 | All REQ-* items are independently verifiable (can be tested without testing another REQ) | | |
| B-17 | Acceptance Criteria section has at least one AC-* item | | |
| B-18 | Every REQ-* has at least one corresponding AC-* | | |
| B-19 | All AC-* items follow Given/When/Then format | | |
| B-20 | All AC-* items have a [P1], [P2], or [P3] priority tag | | |
| B-21 | All P1 AC items are independently testable (can be verified without other stories complete) | | |
| B-22 | No AC item requires knowledge of the implementation to evaluate (no "the database contains…", "the Redux store has…") | | |
| B-23 | Invariants section has at least one INV-* item | | |
| B-24 | All INV-* items are written as absolute statements ("must always" / "must never") — not "should" | | |
| B-25 | Edge Cases section has at least one EC-* item | | |
| B-26 | All EC-* items are concrete scenarios ("What happens when X?") — not categories ("Handle edge cases") | | |
| B-27 | All EC-* items have an explicit Expected Behavior | | |
| B-28 | Dependencies table is complete — no blank Failure Mode or Fallback cells | | |
| B-29 | Constitution Compliance table is complete — all 8 articles marked COMPLIES / EXCEPTION / N/A | | |
| B-30 | Any EXCEPTION in the Constitution Compliance table has a note in this DoD or in the ADR | | |
| B-31 | Implementation Readiness Gate checklist in spec.md is complete and shows PASS | | |

---

## Section C: TypeScript Contract Quality (api.spec.ts, state.spec.ts, orchestrator.spec.ts, ui.spec.ts, errors.spec.ts)

*Verifies TypeScript spec files are properly typed and complete. Mark entire section NA if no TypeScript spec files were required.*

| # | Item | Status | Notes |
|---|------|--------|-------|
| C-01 | All TypeScript files use TypeScript interfaces/types — no behavior defined only in comments | | |
| C-02 | All public interfaces and types have JSDoc comments | | |
| C-03 | All optional fields are explicitly marked with `?` — no fields are implicitly optional | | |
| C-04 | Nullable fields are typed as `T \| null`, not `T \| undefined` (nullable intent is explicit) | | |
| C-05 | No `any` types — all types are specific | | |
| C-06 | Const objects that should not be mutated use `as const` | | |
| C-07 | api.spec.ts: All endpoints are in API_ENDPOINTS registry | | |
| C-08 | api.spec.ts: All error codes are in API_ERROR_HTTP_STATUS mapping | | |
| C-09 | api.spec.ts: All endpoints have auth requirements in API_AUTH_REQUIREMENTS | | |
| C-10 | state.spec.ts: INITIAL_FEATURE_STATE covers all fields in FeatureState | | |
| C-11 | state.spec.ts: STATE_TRANSITIONS covers all action types in the FeatureAction union | | |
| C-12 | state.spec.ts: STATE_INVARIANTS are falsifiable statements | | |
| C-13 | orchestrator.spec.ts: All async output functions return OrchestratorResult<T> — not void or naked Promise | | |
| C-14 | orchestrator.spec.ts: ORCHESTRATOR_INVARIANTS are falsifiable statements | | |
| C-15 | ui.spec.ts: All components in FeatureComponentRegistry have a corresponding Props interface | | |
| C-16 | ui.spec.ts: DISPLAY_CONDITIONS covers show/hide/disabled state for every interactive component | | |
| C-17 | ui.spec.ts: ACCESSIBILITY_REQUIREMENTS covers all components | | |
| C-18 | errors.spec.ts: All error codes in ERROR_CODES have entries in ERROR_HTTP_STATUS, ERROR_RETRY_ELIGIBILITY, ERROR_OWNERSHIP, ERROR_MESSAGE_GUIDANCE | | |
| C-19 | errors.spec.ts: No error code is missing from ERROR_COVERAGE_REQUIREMENTS | | |

---

## Section D: Behavior Rules Quality

*Verifies behavior.spec.md is complete and internally consistent. Mark entire section NA if behavior.spec.md was not required.*

| # | Item | Status | Notes |
|---|------|--------|-------|
| D-01 | Precedence rules cover every field that can receive a value from multiple sources | | |
| D-02 | Precedence rules are ordered — highest priority source is first | | |
| D-03 | Default Values table covers every field with a non-obvious default | | |
| D-04 | "Why" column in Default Values table contains a rationale — not just a restatement of the value | | |
| D-05 | Limits and Bounds table covers every numeric constraint that affects behavior | | |
| D-06 | Enforcement column in Limits table specifies where each constraint is checked | | |
| D-07 | Deduplication rules define "duplicate" precisely (not just "same content") | | |
| D-08 | Tie-break logic is deterministic — same inputs always produce same winner | | |
| D-09 | Edge Case Handling table covers all boundary values from the Limits table | | |
| D-10 | Every behavior rule in behavior.spec.md has a corresponding row in traceability.spec.md Section 5 | | |

---

## Section E: Traceability Quality

*Verifies the traceability matrix is present and appropriately populated.*

| # | Item | Status | Notes |
|---|------|--------|-------|
| E-01 | traceability.spec.md is present | | |
| E-02 | Every REQ-* from feature.spec.md appears in traceability.spec.md Section 1 | | |
| E-03 | Every AC-* from feature.spec.md appears in traceability.spec.md Section 1 | | |
| E-04 | Every INV-* from feature.spec.md appears in traceability.spec.md Section 2 | | |
| E-05 | Every EC-* from feature.spec.md appears in traceability.spec.md Section 3 | | |
| E-06 | Every error code from errors.spec.ts appears in traceability.spec.md Section 4 | | |
| E-07 | Rows with "pending" status are acceptable at spec stage (before TDD) — no FAIL for pending rows | | |
| E-08 | Section 7 (Untraced Requirements) is empty | | |

---

## Section F: Internal Consistency

*Verifies that the spec-system files are consistent with each other.*

| # | Item | Status | Notes |
|---|------|--------|-------|
| F-01 | Error codes in api.spec.ts match (are a subset of or equal to) error codes in errors.spec.ts | | |
| F-02 | Resource status types in api.spec.ts, state.spec.ts, orchestrator.spec.ts, and ui.spec.ts are consistent (same values, same spelling) | | |
| F-03 | OrchestratorItem fields in orchestrator.spec.ts are a valid projection of FeatureItem in state.spec.ts (no field contradiction) | | |
| F-04 | ItemSummary fields in ui.spec.ts are a valid projection of OrchestratorItem in orchestrator.spec.ts | | |
| F-05 | Default values in orchestrator.spec.ts InputProps match the Default Values table in behavior.spec.md | | |
| F-06 | Rate limit values in api.spec.ts match the Limits and Bounds table in behavior.spec.md | | |
| F-07 | All spec files reference the same spec_id and feature_name | | |
| F-08 | All spec files have consistent version numbers (all match, or minor differences are documented) | | |

---

## Section G: Constitution Compliance Verification

*Verifies that all Constitution articles have been properly addressed.*

| # | Item | Status | Notes |
|---|------|--------|-------|
| G-01 | Article I (Library-First): spec does not specify custom implementations where libraries exist | | |
| G-02 | Article II (Test-First): spec makes no assumptions about implementation order — TDD will run first | | |
| G-03 | Article III (Simplicity Gate): every module referenced in TypeScript specs traces to a requirement in feature.spec.md | | |
| G-04 | Article IV (Anti-Abstraction Gate): no speculative abstractions in TypeScript specs (no interfaces with only one current consumer unless it is a defined contract boundary) | | |
| G-05 | Article V (Integration-First Testing): every P1 AC has a corresponding integration test row in traceability.spec.md (or "pending" if TDD has not run) | | |
| G-06 | Article VI (Security-by-Default): api.spec.ts auth requirements are present for all endpoints; no endpoint is unauthenticated without explicit NA justification | | |
| G-07 | Article VII (Spec Integrity): spec_id and content_hash are present and correct in all spec files | | |
| G-08 | Article VIII (Observability): errors.spec.ts defines structured error payloads with correlationId for all server-side errors | | |

---

## Section H: Final Gate

*The single most important check. Must be PASS for any handoff.*

| # | Item | Status | Notes |
|---|------|--------|-------|
| H-01 | **Implementation Readiness Gate:** A new developer who has never worked on this codebase can read the spec-system package and implement the feature from these specs alone — without asking clarifying questions about scope, behavior, error handling, state, or UI contract. | | |

---

## Summary

| Section | Items | Passing | Failing | NA |
|---------|-------|---------|---------|-----|
| A: Package Completeness | 10 | | | |
| B: feature.spec.md Quality | 31 | | | |
| C: TypeScript Contract Quality | 19 | | | |
| D: Behavior Rules Quality | 10 | | | |
| E: Traceability Quality | 8 | | | |
| F: Internal Consistency | 8 | | | |
| G: Constitution Compliance | 8 | | | |
| H: Final Gate | 1 | | | |
| **TOTAL** | **95** | | | |

**Overall DoD Result:** PASS / FAIL

> PASS — All items are PASS or NA (with written justification for each NA). Spec is ready for Architect dispatch.
> FAIL — One or more items are FAIL or blank. Spec must be revised before handoff.

---

## Blocking Issues (if FAIL)

<!-- List each FAIL item with the specific issue and what must change to bring it to PASS. -->

| Item ID | Issue | Required Change | Owner | Target Date |
|---------|-------|----------------|-------|-------------|
| | | | | |

---

## Sign-Off Block

Both sign-offs are required before the spec can advance to Architect dispatch.

| Role | Name / Agent ID | Date (ISO-8601 UTC) | Signature |
|------|-----------------|---------------------|-----------|
| Spec Agent | | | |
| Coordinator | | | |

> By signing, the Coordinator confirms:
> 1. All items in this checklist are PASS or NA with written justification.
> 2. The spec-system package is internally consistent.
> 3. The Implementation Readiness Gate (H-01) is PASS.
> 4. The spec is authorized for dispatch to the Architect Agent.
