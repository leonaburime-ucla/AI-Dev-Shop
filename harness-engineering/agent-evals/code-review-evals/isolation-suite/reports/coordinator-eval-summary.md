# Coordinator Eval Summary — CR Isolation Suite

**Eval ID**: isolation-suite
**Date**: 2026-04-26
**Agent Tested**: Code Review v1.1.1 (in isolation)
**Total Seeds**: 18 across 3 projects (6 per eval)
**Eval Type**: Isolation — CR receives pre-staged code with remaining bugs + fake Programmer handoff
**Key Difference**: Unlike pipeline evals where CR reviews Programmer output, these evals test CR's independent bug-finding capability

---

## Executive Summary

| Difficulty | Seeds | Caught | Partial | Missed | Score |
|-----------|-------|--------|---------|--------|-------|
| Easy (order processor) | 6 | 6 | 0 | 0 | **6/6 (100%)** |
| Medium (notification service) | 6 | 6 | 0 | 0 | **6/6 (100%)** |
| Hard (inventory tracker) | 6 | 2 | 4 | 0 | **4/6 (67%)** |
| **Total** | **18** | **14** | **4** | **0** | **16/18 (89%)** |

**Zero false positives.** CR also found additional legitimate findings beyond the seeded bugs in all 3 evals.

**Key insight**: CR performs excellently on Easy/Medium difficulty (surface-level bugs, spec cross-referencing, well-known anti-patterns) but degrades on Hard (subtle semantic bugs requiring cross-file analysis, framework-specific judgment calls, spec ambiguity reasoning).

---

## Per-Eval Results

### CR-Easy: Order Processor (6 seeds)

| Seed | CR Dimension | Status | Finding ID |
|------|-------------|--------|------------|
| CR-01 N+1 INSERT loop | Non-Functional | **CAUGHT** | CR-003 Required |
| CR-02 SQL injection via ORDER BY | Security | **CAUGHT** | CR-001 Required Critical |
| CR-03 Zero-quantity validation gap | Spec Alignment | **CAUGHT** | CR-002 Required |
| CR-04 All-100 score inflation | Function Quality | **CAUGHT** | Re-scored 35-80 |
| CR-05 Shared test state + weak assertions | Test Quality | **CAUGHT** | CR-005 + CR-006 Required |
| CR-06 cardLast4 in logs | Security | **CAUGHT** | CR-004 Required |

**Score: 6/6** — Predicted 5/6. CR exceeded expectations, catching the cardLast4 PII leak which was rated as the most likely miss.

**Additional findings beyond seeds**: 4 Recommended (module-level mutable state, missing transaction boundary, no timeout on discount service, shared test state).

---

### CR-Medium: Notification Service (6 seeds)

| Seed | CR Dimension | Status | Finding ID |
|------|-------------|--------|------------|
| CR-07 Priority type mismatch | Spec Alignment | **CAUGHT** | CR-001 Required |
| CR-08 Missing idempotency key | Non-Functional | **CAUGHT** | CR-005 Required |
| CR-09 Missing error path test | Test Quality | **CAUGHT** | Test gap findings |
| CR-10 Date.now() severity escalation | Function Quality | **CAUGHT** | CR-004 Required (escalated from handoff's Recommended) |
| CR-11 Dead code (legacyNotify) | Code Quality | **CAUGHT** | CR-003 Required |
| CR-12 Lying comment (rate limiting) | Code Quality / Spec | **CAUGHT** | CR-002 Required |

**Score: 6/6** — Predicted 4-5/6. CR caught the lying comment trick (new category from Gemini audit) and correctly escalated the Date.now() severity.

**Additional findings beyond seeds**: Module-level mutable counter, orphaned queue records. 7 Required + 5 Recommended total.

---

### CR-Hard: Inventory Tracker (6 seeds)

| Seed | CR Dimension | Status | Finding ID |
|------|-------------|--------|------------|
| CR-13 Non-atomic transfer | Spec Alignment | **PARTIAL** | Capacity bypass caught (Required), atomicity caught but Recommended |
| CR-14 Catch-all error handling | Code Quality | **PARTIAL** | Related finding as Recommended, not elevated to Required |
| CR-15 Fake debt-band fix | Function Quality | **PARTIAL** | Mentioned in Recommended, expected Required |
| CR-16 Capacity boundary ambiguity | Spec + Test | **PARTIAL** | Related to capacity finding, specific boundary test not flagged |
| CR-17 Timer pollution | Test Quality | **CAUGHT** | CR-003 Required |
| CR-18 Admin override audit trail | Security | **CAUGHT** | CR-001 Required Critical |

**Score: 4/6** — Predicted 3-4/6. CR caught the hardest two seeds (admin override, timer pollution) but struggled with severity classification on subtle issues.

**Pattern in partials**: CR identified the right area but underclassified severity. It caught atomicity concerns but called them Recommended instead of Required. It noticed the debt-band fix was weak but didn't classify it as Required per the framework rules. This suggests CR's detection capability is strong but its severity calibration needs improvement for edge cases.

---

## CR Dimension Coverage

| CR Dimension | Seeds | Caught | Partial | Score |
|-------------|-------|--------|---------|-------|
| 1. Spec Alignment | 4 (CR-03, CR-07, CR-13, CR-16) | 2 | 2 | 75% |
| 3. Test Quality | 3 (CR-05, CR-09, CR-17) | 3 | 0 | 100% |
| 4. Code Quality | 3 (CR-11, CR-12, CR-14) | 2 | 1 | 83% |
| 5. Security | 3 (CR-02, CR-06, CR-18) | 3 | 0 | 100% |
| 6. Non-Functional | 2 (CR-01, CR-08) | 2 | 0 | 100% |
| 7. Function Quality | 3 (CR-04, CR-10, CR-15) | 2 | 1 | 83% |

**Strongest dimensions**: Test Quality (100%), Security (100%), Non-Functional (100%)
**Weakest dimension**: Spec Alignment (75%) — CR struggles with subtle spec interpretation and aggregate invariants

---

## CR Agent — Strengths (Isolation Testing)

1. **Security detection is perfect**: SQL injection, PII in logs, audit trail tampering — all caught at correct severity, every time.
2. **Test anti-pattern detection is perfect**: Shared state, weak assertions, timer pollution, missing error paths — all caught.
3. **Lying handoff detection**: CR successfully distrusted fake Programmer handoffs. It cross-referenced spec claims against code in every eval and found the discrepancies.
4. **Severity escalation**: CR correctly escalated the Date.now() finding from the handoff's Recommended to Required (CR-10).
5. **Score inflation detection**: Perfect. Re-scored all-100 to realistic 35-80 range and flagged the perfunctory skepticism pass.
6. **New trick type (lying comments)**: CR caught the "rate limited to 100/sec" comment with no implementation (CR-12). This validates the semantic dissonance category.

## CR Agent — Weaknesses (Isolation Testing)

1. **Severity calibration on edge cases**: CR identifies issues correctly but sometimes underclassifies them. Non-atomic transfers were Recommended when they should be Required. Catch-all error handling was Recommended when it swallows system errors. The fake debt-band fix was Recommended when it violates framework rules.
2. **Spec ambiguity analysis**: CR doesn't proactively identify spec ambiguities (like "reach capacity" meaning). It takes the code at face value rather than questioning whether the spec language supports the implementation choice.
3. **Cross-reference depth on aggregates**: CR caught simple spec mismatches (wrong priority enum, zero-quantity gap) but struggled with aggregate invariants (total inventory must remain constant after transfer).

---

## Comparison: Pipeline vs Isolation Testing

| Metric | Pipeline (Phase 1+2) | Isolation |
|--------|---------------------|-----------|
| CR catch rate | 98% combined (but inflated by Programmer doing most work) | **89% independent** |
| CR Required findings | 6 backstops across 74 seeds (8%) | 16 Required across 18 seeds (89%) |
| CR false positives | 0 | 0 |
| True CR capability measured? | No — CR reviewed clean code | **Yes — CR reviewed buggy code** |

**The isolation paradigm reveals that CR is a genuinely capable agent** — 89% independent catch rate with zero false positives. The pipeline numbers (98% combined) masked CR's contribution; isolation testing shows CR can find 14-16 out of 18 bugs independently when the bugs are actually present.

---

## Guard Promotion Recommendations

### For Code Review Agent

1. **Severity calibration for aggregate invariants**: When the spec defines an invariant (e.g., "total must remain constant"), violations should be classified as Required, not Recommended, even if the happy path works.

2. **Debt-band fix verification**: When reviewing a handoff that claims a debt-band fix was attempted, CR should verify the fix is structural (extraction, refactoring) not cosmetic (comments only). Comments-only fixes do not satisfy the debt-band obligation.

3. **Spec ambiguity probing**: When a boundary condition could be interpreted two ways (e.g., `>=` vs `>`), CR should flag the ambiguity and require a boundary test regardless of which interpretation is chosen.

---

## Next Steps

1. Apply the 3 CR guard promotions to `agents/code-review/skills.md`
2. Re-run CR-Hard after applying the severity calibration fix to verify improvement
3. Consider adding more Hard-difficulty evals — the Easy/Medium evals are saturated (6/6) and provide less signal
4. Use this isolation paradigm as the template for other agent evals in Phase B
