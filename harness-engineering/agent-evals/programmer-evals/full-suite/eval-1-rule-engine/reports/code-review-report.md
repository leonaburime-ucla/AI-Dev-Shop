# Code Review Report -- Discount Rule Engine

**Reviewer**: Code Review Agent v1.1.1
**Date**: 2026-04-26
**Verdict**: PASS WITH RECOMMENDATIONS

---

## 1. Spec Alignment

| Requirement | Status | Notes |
|-------------|--------|-------|
| 1. Cart with line items (SKU, name, quantity, unitPrice), apply discount rules | PASS | `LineItem` interface matches spec exactly; `applyDiscounts` accepts cart + tier |
| 2a. Bulk discount (10+ same SKU = 15% off that SKU) | PASS | `bulkDiscount` checks `quantity >= 10`, applies 15% per qualifying line item |
| 2b. Combo discount (WIDGET-A + WIDGET-B = $5 off total) | PASS | `comboDiscount` checks Set membership, returns flat $5 |
| 2c. Loyalty discount (gold=10%, silver=5%) | PASS | `loyaltyDiscount` uses rate lookup, applies to subtotal |
| 3. Rules stack, cap at 40% | PASS | Loop applies all rules, partial clamping implemented |
| 4. Return: subtotal, discounts (rule name + amount), final total, warnings | PASS | `DiscountResult` contains all four fields |
| 5. Reject cart with quantity <= 0 or unitPrice < 0 | PASS | `validateCart` throws with SKU-identifying messages |
| 6. Easy to extend without modifying core loop | PASS | `options.rules` accepts any `DiscountRule[]`; custom BOGO rule tested |
| Edge: empty cart | PASS | Throws "Cart cannot be empty" |
| Edge: single item | PASS | Tested |
| Edge: all rules applying | PASS | Tested with stacking test |
| Edge: discount cap hit | PASS | Tested with partial clamping |
| Pure TS, no external deps | PASS | Only dev dependencies |

**Spec alignment verdict**: All 6 requirements and all 4 edge cases are covered.

---

## 2. Architecture Adherence

### Boundaries and contracts

- Types are cleanly separated into `types.ts` with `readonly` modifiers throughout -- good.
- Validation is isolated in `validation.ts`, pure rule functions in `rules.ts`, orchestration in `engine.ts`.
- Two-object signature (`input`, `options?`) on `applyDiscounts` is clean and extensible.
- Each rule function takes `RuleContext` and returns `readonly AppliedDiscount[]` -- uniform contract.

### Pure logic vs. effects

- No `console.log`, no I/O, no global mutation in any production file -- pure computation throughout. Good.

**Architecture verdict**: Clean separation. No violations.

---

## 3. Test Quality

### Coverage of spec requirements

All 6 spec requirements have dedicated test cases. The 4 adversarial tests (many small discounts, exact cap boundary, fractional penny rounding, zero-amount discount) are well-chosen.

### Anti-pattern check

| Anti-pattern | Found? | Details |
|--------------|--------|---------|
| Shared mutable state | NO | `makeItem` and `makeContext` helpers create fresh data per test |
| Weak assertions | NO | Tests assert on specific values, not just truthiness |
| Order dependency | NO | Each test is self-contained |
| Testing implementation not behavior | NO | Tests assert on outputs (amounts, totals, warnings), not internal state |
| CC > 4 side effects | NO | `applyDiscounts` CC=4, at threshold but acceptable |

### Missing test coverage (Recommended)

**R1. Duplicate SKUs in cart**: No test verifies behavior when the same SKU appears on multiple line items. For example, if a cart has two lines for "WIDGET-A" (qty 3 and qty 8), the bulk discount should NOT fire for either line individually (neither reaches 10), but the business intent may be ambiguous. The current implementation treats each line item independently, which is a defensible interpretation, but a test documenting this decision would be valuable.

**R2. Combo discount with duplicate WIDGET-A lines**: If the cart has two WIDGET-A line items and one WIDGET-B, the combo fires once (correct), but this is untested.

**R3. Multiple combo pairs**: If the cart has two WIDGET-A and two WIDGET-B line items (on separate lines), the combo still fires only once. This edge case is untested.

**R4. Subtotal is not rounded**: The `subtotal` field in the result is computed via a raw `reduce` without `roundCents`. For example, 3 items at $0.07 each = 0.21000000000000002 in floating-point. The `finalTotal` IS rounded, but `subtotal` is not. This inconsistency is not tested because no test uses prices that expose floating-point drift in the subtotal calculation.

**R5. `loyaltyTier` as required field**: The spec says "loyalty tier 'gold' = 10% off total, 'silver' = 5%". The implementation requires `loyaltyTier` in the input type. There is no test for what happens if an unrecognized tier string is somehow passed (TypeScript prevents this at compile time, but at runtime with JS callers it could happen).

---

## 4. Code Quality and Maintainability

### Finding: `roundCents` is duplicated (Recommended)

`roundCents` appears identically in both `rules.ts` (line 76) and `engine.ts` (line 93). The programmer's handoff acknowledges this and calls it "acceptable for zero-dependency constraint," but that rationale is weak -- both files already import from `types.ts`. Extracting `roundCents` to a shared `utils.ts` or exporting it from `rules.ts` would eliminate the duplication with zero cost.

**Classification**: Recommended

### Finding: `comboDiscount` allocates a Set on every call (Recommended)

Line 35 of `rules.ts`: `const skus = new Set(context.items.map(i => i.sku))` creates an intermediate array and a Set. For a typical cart this is negligible, but for consistency with the O(n) space annotation on `bulkDiscount`, the space complexity comment says O(1) which is incorrect -- it is O(n).

**Classification**: Recommended (comment accuracy, not a real performance concern)

### Finding: outer loop `break` only exits inner loop (Required)

In `engine.ts` lines 50-69, the capping logic has a nested `for...of` structure:

```typescript
for (const rule of rules) {          // outer
  const ruleResults = rule(context);
  for (const d of ruleResults) {     // inner
    const remaining = ...;
    if (remaining <= 0) {
      break;                         // only breaks inner loop
    }
    ...
  }
}
```

When `remaining <= 0`, the `break` exits the inner loop but the outer loop continues, calling the next rule function unnecessarily. The next rule's results will all be skipped (since remaining is still <= 0), so **correctness is preserved**, but:
- Every remaining rule function is called and its results iterated, only to be immediately skipped.
- This is wasteful and misleading -- a reader might assume the outer loop also terminates.

This is a correctness-adjacent issue because if a custom rule has side effects (e.g., logging, metrics), those side effects would fire even after the cap is reached. The `DiscountRule` type signature implies pure functions, but nothing enforces this at runtime.

**Classification**: Required -- the outer loop should also break or return when the cap is fully consumed. A simple fix: track a `capReached` flag or use a labeled break.

---

## 5. Security Surface

No new endpoints, no network I/O, no file system access, no user-supplied code execution. The `DiscountRule` type accepts arbitrary functions, but this is by design for extensibility and the caller controls what rules are passed.

Input validation is sound: negative prices and zero/negative quantities are rejected with descriptive errors.

**Security verdict**: No issues.

---

## 6. Non-Functional Characteristics

| Concern | Status | Notes |
|---------|--------|-------|
| Unbounded queries | N/A | No database or network access |
| Per-item I/O | N/A | Pure computation |
| Missing indexes | N/A | No persistence layer |
| Timeout protection | N/A | Computation is O(R*n), bounded by cart size |
| Floating-point safety | PARTIAL | `roundCents` is applied to discount amounts and final total, but NOT to subtotal (see R4 above) |

**Non-functional verdict**: Acceptable. The unrounded subtotal is a minor concern.

---

## 7. Function Quality Assessment

### Score plausibility check

| Function | Claimed Score | Reviewer Assessment | Justified? |
|----------|--------------|-------------------|------------|
| `validateCart` | 95 | 93 | Slightly inflated -- does not validate `sku` is non-empty string, does not validate `name` exists |
| `bulkDiscount` | 95 | 94 | Reasonable |
| `comboDiscount` | 95 | 93 | Space complexity comment is wrong (says O(1), is O(n)) |
| `loyaltyDiscount` | 95 | 95 | Accurate |
| `roundCents` (rules) | 95 | 90 | Duplicated function should not score 95; duplication is a quality issue |
| `applyDiscounts` | 92 | 88 | The nested-break bug (outer loop continues after cap) is a real correctness-adjacent issue |
| `roundCents` (engine) | 95 | 90 | Same duplication issue |

### Skepticism pass

The programmer already performed a skepticism pass on the original 100/100 scores and revised them down, which is good practice. However, the revised scores are still slightly optimistic:
- `applyDiscounts` at 92 understates the nested-break issue.
- Both `roundCents` copies at 95 ignore the duplication penalty.
- No function is scored below 90, which for code with a known bug pattern (the break issue) feels generous.

**No score inflation pattern detected** -- the scores are within a reasonable range and the programmer's skepticism pass was genuine. The remaining inflation is minor (2-4 points per function).

---

## Findings Summary

### Required (must fix before proceeding)

| ID | Finding | File | Line(s) | Severity |
|----|---------|------|---------|----------|
| REQ-1 | Outer loop continues calling rule functions after discount cap is fully consumed. The `break` on line 57 only exits the inner loop. If a custom rule has side effects, they will execute unnecessarily. Fix: add a `capReached` flag checked in the outer loop, or use a labeled break. | engine.ts | 50-69 | Medium |

### Recommended (non-blocking)

| ID | Finding | File | Line(s) |
|----|---------|------|---------|
| REC-1 | `roundCents` duplicated across `rules.ts` and `engine.ts`. Extract to shared utility. | rules.ts:76, engine.ts:93 | |
| REC-2 | `comboDiscount` space complexity comment says O(1) but is O(n) due to Set allocation. | rules.ts:30 | |
| REC-3 | `subtotal` in `DiscountResult` is not rounded via `roundCents`, creating inconsistency with `finalTotal` which IS rounded. | engine.ts:37-39 | |
| REC-4 | Missing test: duplicate SKUs on separate line items (documents whether bulk threshold is per-line or per-SKU). | engine.test.ts | |
| REC-5 | Missing test: combo discount with multiple WIDGET-A line items + WIDGET-B. | engine.test.ts | |
| REC-6 | Missing test: subtotal with prices that expose floating-point drift (e.g., 3 x $0.07). | engine.test.ts | |

---

## Verdict

**PASS WITH RECOMMENDATIONS**

The implementation is solid, covers all spec requirements, has strong test coverage, clean architecture, and no security concerns. The one Required finding (REQ-1: outer-loop continuation after cap) is a real but bounded issue -- correctness is preserved for pure rule functions, but the code is misleading and fragile if rules with side effects are added. The six Recommended findings are quality improvements that would strengthen the codebase.

The programmer's handoff report was thorough and honest, with a genuine skepticism pass on function scores. The bug fixes from the original code were all correct and well-documented.
