# Code Review Report — Inventory Tracker (v1.2.0 Re-run)

**Spec:** spec-inv-tracker-v4-ghi789
**Reviewer:** Code Review Agent v1.2.0
**Date:** 2026-04-26
**Purpose:** Re-run of CR-Hard eval after applying 3 guard promotions (2a, 3a, 3b)

---

## Summary

5 Required findings, 6 Recommended findings. Key improvements over v1.1.1:
- Non-atomic transfer elevated from Recommended to Required (Rule 3a)
- Fake debt-band fix elevated from Recommended to Required (Rule 2a)
- Capacity boundary ambiguity flagged with pin test requirement (Rule 3b)

---

## Required Findings

### R1. AC-6 Violation: admin override records admin ID, not original requester
- **Dimension:** Spec Alignment
- **Seed:** CR-18 — CAUGHT (same as v1.1.1)

### R2. Non-Atomic Transfer Violates Aggregate Invariant
- **Dimension:** Architecture / Spec Alignment
- **Rule applied:** 3a (aggregate invariant severity)
- **Seed:** CR-13 — **CAUGHT** (was PARTIAL in v1.1.1, Recommended → Required)

### R3. Transfer Does Not Enforce Destination Capacity
- **Dimension:** Spec Alignment
- **Seed:** Additional finding (beyond seeds, also related to CR-13)

### R4. Debt-Band Fix Is Cosmetic, Not Structural
- **Dimension:** Function Quality Assessment
- **Rule applied:** 2a (debt-band fix verification)
- **Seed:** CR-15 — **CAUGHT** (was PARTIAL in v1.1.1, Recommended → Required)

### R5. Capacity Boundary Ambiguity — Missing Boundary Pin Test
- **Dimension:** Test Quality
- **Rule applied:** 3b (spec ambiguity probing)
- **Seed:** CR-16 — **CAUGHT** (was PARTIAL in v1.1.1, not flagged → Required)

---

## Seed Scoring

| Seed | v1.1.1 Result | v1.2.0 Result | Change | Notes |
|------|--------------|--------------|--------|-------|
| CR-13 (non-atomic transfer) | PARTIAL (Recommended) | **CAUGHT** (Required, Rule 3a) | +0.5 | Guard promotion worked |
| CR-14 (catch-all error handling) | PARTIAL (Recommended) | **PARTIAL** (tangential mention only) | 0 | Still not elevated to Required |
| CR-15 (fake debt-band fix) | PARTIAL (Recommended) | **CAUGHT** (Required, Rule 2a) | +0.5 | Guard promotion worked |
| CR-16 (capacity boundary) | PARTIAL (no flag) | **CAUGHT** (Required, Rule 3b) | +0.5 | Guard promotion worked |
| CR-17 (timer pollution) | CAUGHT (Required) | **MISSED** (AC-7 marked Pass) | -1.0 | Regression — non-determinism |
| CR-18 (admin override) | CAUGHT (Required) | **CAUGHT** (Required) | 0 | Stable |

| Metric | v1.1.1 | v1.2.0 |
|--------|--------|--------|
| CAUGHT | 2 | 4 |
| PARTIAL | 4 | 1 |
| MISSED | 0 | 1 |
| Score | 4/6 (67%) | 4.5/6 (75%) |

---

## Analysis

### What the guard promotions fixed
- **Rule 3a** (aggregate invariant severity): CR-13 correctly elevated from Recommended to Required. The rule worked as designed — CR identified the non-atomic transfer as a spec invariant violation.
- **Rule 2a** (debt-band fix verification): CR-15 correctly elevated from Recommended to Required. CR explicitly checked whether the claimed fix was structural vs cosmetic.
- **Rule 3b** (spec ambiguity probing): CR-16 correctly flagged the "reach capacity" ambiguity and required a boundary pin test.

### What remained unfixed
- **CR-14** (catch-all error handling): The catch-all in `bulkAdjust` was only tangentially mentioned (non-Error throw branch). The rule 3a doesn't directly cover this — it targets spec-defined invariants, not error handling quality. This may need its own guard: "Catch-all error handling that swallows unexpected errors (TypeError, ReferenceError, connectivity) alongside expected domain errors is Required when the spec says errors must be surfaced."

### What regressed
- **CR-17** (timer pollution): `jest.useFakeTimers()` at module scope without cleanup was CAUGHT in v1.1.1 but MISSED in v1.2.0. AC-7 was marked "Pass" in this run. This is LLM non-determinism — the same code, same spec, different run. The guard promotions may have shifted CR's attention budget toward the new rules, crowding out a finding it previously caught. This is a known evaluation challenge: adding rules can redistribute attention.

### Recommendation
- The 3 guard promotions are validated for CR-13, CR-15, CR-16 — keep them.
- CR-14 needs a separate guard if it repeats in future evals (one occurrence is not enough for promotion per policy).
- CR-17 regression should be retested — if it fails again, the timer cleanup check needs reinforcement in the Test Quality dimension.
- Consider running 3-5 iterations of CR-Hard to get statistical significance on catch rates, per the agent-evaluation skill guidance on non-determinism.
