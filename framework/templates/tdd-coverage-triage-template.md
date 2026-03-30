# TDD Coverage Triage Report

- Feature: FEAT-<NNN> — <feature name>
- Spec ID: <SPEC-id>
- Spec Hash: <sha256 — must match active spec>
- TestRunner Report: `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/test-runs/TESTRUN-<feature-id>-<YYYY-MM-DD-HHmm>.md`
- Triaged At: <ISO-8601 UTC>
- Triaged By: TDD Agent

---

## Triage Results

One row per file in the Coverage Gap List. Every file must be classified — no blanks.

| File | Module Class | Current % | Target % | Gap Type | Spec Refs | Recommended Route | Notes |
|------|--------------|-----------|----------|----------|-----------|-------------------|-------|
| `src/services/invoice.ts` | Core business logic | 61% | 95% | spec-traceable | AC-03, INV-01 | TDD gap fill | Missing negative path for zero-quantity line items |
| `src/utils/legacy-calculator.ts` | Core business logic | 22% | 95% | no-spec-mapping | — | Refactor Agent | Tightly coupled, no injectable seams; candidate for seam extraction |
| `src/config/constants.ts` | Configuration | — | Exempt | exempt | — | No action | No runtime logic |

**Gap types:**
- `spec-traceable` — uncovered path maps to a known requirement, invariant, or edge case in the spec; TDD writes missing tests
- `no-spec-mapping` — uncovered path cannot be traced to any spec item; may be dead code, untestable coupling, or out-of-scope implementation; route to Coordinator for Refactor dispatch
- `exempt` — file is configuration, type-only, or otherwise exempt per the risk-weighted threshold table

---

## Summary

- Total files below threshold: <N>
- spec-traceable gaps: <N> (TDD will write tests — listed below)
- no-spec-mapping gaps: <N> (routing to Coordinator for Refactor dispatch — listed below)
- exempt files: <N>

### spec-traceable — TDD will write tests

| File | Missing Coverage | Spec Ref | Priority |
|------|-----------------|----------|----------|
| | | | |

### no-spec-mapping — Coordinator decision needed

| File | Why No Spec Mapping | Suspected Cause | Priority |
|------|---------------------|-----------------|----------|
| | | | |

---

## Updated Certification Record

After gap fill tests are written, update the certification record at:
`<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/pipeline/<NNN>-<feature-name>/test-certification.md`

- Do not change the original certified spec hash
- Add new tests to the Covered Requirements table
- Revise the Known Gaps section
- Update the certified timestamp

---

## Handoff

- Suggested next: Coordinator
- Coordinator routes spec-traceable items back to TDD for test writing (if not already written in this session)
- Coordinator routes no-spec-mapping items to Refactor Agent with this triage report as context
