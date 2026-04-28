# Seed Ledger — Eval 1: Discount Rule Engine

## Seeds

```
ID: SEED-1A
Category: Adversarial aggregate behavior
Seeded issue: The starter code has a bulkDiscount function that checks quantity per line item but does NOT aggregate quantity across duplicate SKUs in the cart. A cart with two lines of "WIDGET-A" (qty 6 + qty 5 = 11) should trigger bulk discount but won't.
Expected owner: Programmer
Expected severity: High
Expected signal: Aggregate test or probe for repeated SKUs
Evidence path: project/src/rules.ts — bulkDiscount function
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-1B
Category: Hidden branching / Determinism
Seeded issue: The starter code applies rules using a Set iteration and object property order, making discount application order non-deterministic. Rule ordering affects the final amount when the 40% cap is reached.
Expected owner: Programmer (should expose), Code Review (required if missed)
Expected severity: High
Expected signal: Tests with all rules applying should assert deterministic ordering
Evidence path: project/src/engine.ts — applyDiscounts function
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-1C
Category: Extension point
Seeded issue: The starter code has all rules hardcoded in a switch statement inside the main engine loop. Adding a new rule requires editing the core function.
Expected owner: Programmer
Expected severity: Medium
Expected signal: Programmer should use a rule table/strategy pattern
Evidence path: project/src/engine.ts — switch block
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-1D
Category: Function scoring / Score inflation
Seeded issue: The starter code has JSDoc with @overallScore 100/100 on every function, including the clearly flawed engine function with CC > 4 and hidden aggregate bug. No skepticism pass documented.
Expected owner: Code Review
Expected severity: Required (score inflation)
Expected signal: Code Review flags inflated scores and missing skepticism pass
Evidence path: project/src/engine.ts, project/src/rules.ts — all JSDoc blocks
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-1E
Category: Predictable errors
Seeded issue: The validation function returns `false` for invalid items but throws an Error for empty cart. Mixed error signaling for the same failure category (invalid cart input).
Expected owner: Programmer
Expected severity: Medium
Expected signal: Programmer should normalize error handling
Evidence path: project/src/validation.ts
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-1F
Category: Stable boundaries / Typed contract
Seeded issue: The applyDiscounts function takes positional arguments (items, loyaltyTier, rules) instead of a required input object. Return type is `any`.
Expected owner: Programmer
Expected severity: Medium
Expected signal: Programmer should use two-object parameter convention and typed return
Evidence path: project/src/engine.ts — function signature
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-1G
Category: Single responsibility
Seeded issue: The main engine function validates, calculates subtotals, applies rules, caps discounts, formats output, AND logs to console. 6 responsibilities in one function.
Expected owner: Programmer
Expected severity: High
Expected signal: Should extract into focused functions
Evidence path: project/src/engine.ts — applyDiscounts (CC ~8)
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-1H
Category: Pure logic vs effects
Seeded issue: The discount calculation functions call console.log inside pure math logic.
Expected owner: Programmer
Expected severity: Medium
Expected signal: Programmer should split logging from calculation
Evidence path: project/src/rules.ts — all discount functions
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-1I
Category: Test anti-patterns
Seeded issue: Tests use `toMatchObject` with partial assertions that would pass even if discount amounts are wrong, and one test depends on execution order of previous test (shared mutable cart object).
Expected owner: Code Review
Expected severity: High
Expected signal: Weak assertions and order-dependent shared state
Evidence path: project/src/__tests__/engine.test.ts
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No
```
