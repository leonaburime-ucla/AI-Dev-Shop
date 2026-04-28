# Seed Ledger — cr-eval-3-inventory-tracker (CR-Hard)

**Eval ID**: benchmark-suite / cr-eval-3-inventory-tracker
**Purpose**: Test Code Review agent independently on pre-staged code with subtle bugs and a professional-looking handoff.
**Difficulty**: Hard — bugs are subtle, the handoff looks credible, and several seeds require cross-referencing multiple parts of the code/spec/handoff.

---

## Seeds

```
ID:                  SEED-CR-13
Category:            Spec alignment / aggregate invariant
Seeded issue:        Transfers are implemented as two separate setStock calls (remove from source,
                     add to destination) with no atomicity guarantee. If the destination setStock
                     fails (e.g., capacity check on destination), the source stock is already reduced
                     but the destination was never increased — stock vanishes. Additionally, a
                     concurrent getTotalStock call between the two setStock calls would see an
                     incorrect total. The spec says "transfers should not double-count" and "total
                     inventory must remain constant after a transfer."
CR Dimension:        1. Spec Alignment (AC-4: transfer atomicity)
Expected severity:   Required
Expected signal:     CR identifies the non-atomic transfer pattern and flags that the aggregate
                     invariant (constant total) cannot be guaranteed without a transaction or
                     compensating action. The handoff has a skepticism pass that mentions this
                     ("Could use transaction wrapper") but classifies it as Low, not Required.
Evidence path:       src/inventory_tracker.py — transferStock(), two separate setStock calls
Handoff deception:   Handoff claims "AC-4: Transfers don't double-count — Done" and the function
                     quality assessment says "Low: Could use transaction wrapper." The severity is
                     underclassified — this is a correctness bug, not a minor improvement.
False positive risk: Medium — if CR focuses on the happy path (which works), it might miss the
                     failure-between-operations scenario.
```

```
ID:                  SEED-CR-14
Category:            Code quality / error handling
Seeded issue:        bulkAdjust wraps adjustStock in a try/catch that treats ALL errors as
                     validation failures. A TypeError, ReferenceError, store connectivity error,
                     or any unexpected error is silently caught, its message recorded in the
                     failed array, and processing continues. This violates the principle of
                     separating expected domain failures from unexpected programmer/system failures.
                     The spec says "Errors must be collected and returned" — but this also means
                     unexpected errors should not be silently swallowed.
CR Dimension:        4. Code Quality and Maintainability (error handling)
Expected severity:   Required
Expected signal:     CR flags the catch-all try/catch as swallowing unexpected errors. Should
                     recommend distinguishing validation errors (continue) from system errors
                     (abort or surface separately).
Evidence path:       src/inventory_tracker.py — bulkAdjust(), the try/catch block
Handoff deception:   Handoff mentions "Error handling wraps adjustStock in try/catch" as a
                     quality finding but frames it as "Could use Result type" — a code style
                     concern rather than a correctness concern.
False positive risk: Low — catch-all error handling is a well-known anti-pattern.
```

```
ID:                  SEED-CR-15
Category:            Function quality / fake debt-band fix
Seeded issue:        adjustStock is scored 88/100 (debt band). The handoff claims "attempted local
                     fix" but the "fix" was just adding comments — no actual refactoring. The
                     function-quality-assessment skill says debt-band fixes should be real code
                     changes (extraction, restructuring), not just documentation.
CR Dimension:        7. Function Quality Assessment
Expected severity:   Required (debt-band fix is not genuine)
Expected signal:     CR checks whether the claimed debt-band fix for adjustStock actually changed
                     the code structure. Finding: the "fix" is comments only, not extraction or
                     restructuring. CR should flag that the debt-band obligation was not met.
Evidence path:       src/inventory_tracker.py — adjustStock() comments;
                     seed-state/eval-results/eval-results-run.md — debt band fix claim
Handoff deception:   Handoff explicitly claims "Added inline comments as local fix" and
                     "Added clarifying comments to the capacity check logic." This is honest
                     about WHAT was done but dishonest about whether it meets the debt-band
                     fix requirement.
False positive risk: Medium — if CR doesn't have strong opinions about what constitutes a
                     "real" debt-band fix, it may accept the comments.
```

```
ID:                  SEED-CR-16
Category:            Spec alignment / capacity boundary
Seeded issue:        The capacity check uses >= which rejects when newStock >= maxCapacity. This
                     means max allowed stock is maxCapacity - 1. The spec says "Stock additions
                     that would cause the warehouse stock to reach capacity must be rejected" AND
                     "The warehouse must always have room for at least one more unit."

                     The >= check is ACTUALLY CORRECT for the spec requirement "always have room
                     for at least one more unit" (max stock = capacity - 1). BUT the tests don't
                     verify the exact boundary case (newStock == maxCapacity). The real seed is
                     the MISSING BOUNDARY TEST, not the operator itself.

                     However, the spec language "reach capacity" is ambiguous — does "reach" mean
                     "equal" or "meet or exceed"? A good CR should note this ambiguity and recommend
                     a boundary test that nails down the behavior.
CR Dimension:        1. Spec Alignment + 3. Test Quality
Expected severity:   Recommended (spec ambiguity) + Required (missing boundary test)
Expected signal:     CR identifies the spec ambiguity around "reach capacity" and flags the
                     missing boundary test for newStock == maxCapacity.
Evidence path:       src/inventory_tracker.py — adjustStock() capacity check;
                     tests/test_inventory_tracker.py — no exact-boundary test
Handoff deception:   Handoff claims "AC-5: Capacity enforced at maxCapacity — Done." No mention
                     of the boundary ambiguity.
False positive risk: Medium — the code may be correct, but the ambiguity and missing test are real.
```

```
ID:                  SEED-CR-17
Category:            Test quality / timer state pollution
Seeded issue:        All async tests use a module-level `patch` on the clock (top of file)
                     with no proper fixture cleanup. Timer/clock state leaks between tests and
                     the order of test execution can affect results. This is a subtle test
                     anti-pattern that can cause intermittent failures.
CR Dimension:        3. Test Quality
Expected severity:   Required
Expected signal:     CR identifies the module-level `patch` without cleanup as a test
                     pollution risk. Should recommend per-test setup/teardown via a proper
                     pytest fixture that restores the real clock in its cleanup phase.
Evidence path:       tests/test_inventory_tracker.py — top-level module `patch` without cleanup
Handoff deception:   Handoff claims "AC-7: Async tests clean up timers — Done" and "Fake timers
                     used consistently." Consistent use is not the same as proper cleanup.
False positive risk: Low — global fake timers without cleanup is a well-known anti-pattern.
```

```
ID:                  SEED-CR-18
Category:            Security / audit trail
Seeded issue:        When bulkAdjust is called with an admin override, the code replaces
                     adjustment.adjustedBy with override.adminId before calling adjustStock.
                     This means the history log records the ADMIN who approved the override,
                     not the ORIGINAL REQUESTER who initiated the adjustment. The spec says
                     "admin overrides should still record the original requester in audit logs."
CR Dimension:        5. Security Surface (audit trail integrity)
Expected severity:   Required
Expected signal:     CR identifies that the admin override replaces adjustedBy and the history
                     therefore records the wrong user ID. Should recommend recording both the
                     original requester and the admin approver.
Evidence path:       src/inventory_tracker.py — bulkAdjust(), the effectiveAdjustment
                     construction with override.adminId
Handoff deception:   Handoff claims "AC-6: History records original requester — Done" and
                     "adjustedBy from the adjustment, not overridden." This is factually false —
                     the code explicitly overrides adjustedBy.
False positive risk: Low — but requires reading the code carefully rather than trusting the handoff.
```

```
ID:                  SEED-CR-19
Category:            Spec alignment / capacity bypass on transfer
Seeded issue:        transferStock bypasses the destination warehouse's capacity check entirely.
                     It calls store.set_stock directly on the destination without checking whether
                     the resulting stock would reach or exceed maxCapacity. The adjustStock function
                     enforces capacity (line 139), but transferStock never calls adjustStock — it
                     manipulates stock directly via store.set_stock.
CR Dimension:        1. Spec Alignment (AC-5: capacity enforcement)
Expected severity:   Required
Expected signal:     CR identifies that transfer_stock can push a destination warehouse over its
                     maxCapacity. Should recommend either routing through adjust_stock for both
                     sides or adding an explicit capacity check before the destination write.
Evidence path:       src/inventory_tracker.py — transferStock(), destination set_stock call
Handoff deception:   Handoff claims "AC-5: Capacity enforced at maxCapacity — Done" but capacity
                     enforcement only exists in adjustStock, not in transferStock.
False positive risk: Low — the spec says capacity must be enforced for all stock additions.
Origin:              Discovered during eval run (not originally planted). Promoted to seeded bug.
```

---

## Scoring Guide

| Score | Criteria |
|-------|----------|
| CAUGHT | CR identifies the issue and classifies it at the correct severity |
| PARTIAL | CR identifies a related concern but misses the specific seeded issue |
| MISSED | CR does not flag the issue at all |
| FALSE POSITIVE | CR flags something that is not actually a problem |

## Expected Difficulty

This is the **hard** eval. The seeds require:
- SEED-CR-13: Cross-referencing transfer implementation against aggregate invariant (two separate code locations + spec)
- SEED-CR-14: Recognizing that catch-all error handling is a correctness issue, not just a style issue
- SEED-CR-15: Comparing the claimed debt-band fix against the framework's definition of a valid fix
- SEED-CR-16: Analyzing spec ambiguity and identifying a missing boundary test
- SEED-CR-17: Recognizing module-level `patch` without cleanup as test pollution
- SEED-CR-18: Reading the code carefully enough to see that admin override replaces adjustedBy, contradicting the handoff claim
- SEED-CR-19: Noticing that transferStock bypasses capacity checks on the destination warehouse

A competent CR should catch 4-5/7. The most likely misses are SEED-CR-15 (fake
debt-band fix — requires framework knowledge) and SEED-CR-16 (spec ambiguity —
requires careful reading of both spec and code).

## Dimension Coverage

| Seed | CR Dimension | Difficulty |
|------|-------------|------------|
| SEED-CR-13 | 1. Spec Alignment | Hard (cross-reference invariant) |
| SEED-CR-14 | 4. Code Quality | Medium (well-known anti-pattern) |
| SEED-CR-15 | 7. Function Quality | Hard (framework-specific knowledge) |
| SEED-CR-16 | 1. Spec + 3. Test Quality | Hard (ambiguity analysis) |
| SEED-CR-17 | 3. Test Quality | Medium (well-known anti-pattern) |
| SEED-CR-18 | 5. Security | Medium (careful code reading) |
| SEED-CR-19 | 1. Spec Alignment | Medium (cross-reference capacity rule against transfer path) |
