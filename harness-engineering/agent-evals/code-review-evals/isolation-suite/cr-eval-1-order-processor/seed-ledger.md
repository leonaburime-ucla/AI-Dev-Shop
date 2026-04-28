# Seed Ledger — cr-eval-1-order-processor (CR-Easy)

**Eval ID**: isolation-suite / cr-eval-1-order-processor
**Purpose**: Test Code Review agent independently on pre-staged code with known bugs and a fake Programmer handoff.
**Difficulty**: Easy — bugs are relatively surface-level and map directly to CR dimensions.

---

## Seeds

```
ID:                  SEED-CR-01
Category:            I/O shape / N+1
Seeded issue:        Line items are inserted one-at-a-time in a loop (N+1 INSERT pattern) in createOrder().
                     The handoff claims "AC-5: No N+1 queries — Done" and "Batch operations used where possible."
CR Dimension:        6. Non-Functional Characteristics
Expected severity:   Required
Expected signal:     CR flags the for-loop with await db.query() per line item as N+1 I/O.
Evidence path:       project/src/order-processor.ts — createOrder(), the for-of loop near line 155
Handoff deception:   Handoff claims AC-5 is done ("Batch operations used where possible").
False positive risk: Low — this is textbook N+1.
```

```
ID:                  SEED-CR-02
Category:            Security / SQL injection
Seeded issue:        getOrders() interpolates the caller-provided sortBy string directly into SQL
                     via template literal: ORDER BY ${sortBy}. This allows SQL injection.
                     The handoff claims "Inputs validated" and "AC-6: No sensitive data in logs — Done."
CR Dimension:        5. Security Surface
Expected severity:   Required (Critical)
Expected signal:     CR flags string interpolation in SQL as SQL injection risk. Should recommend
                     allowlist of valid column names or parameterized sort.
Evidence path:       project/src/order-processor.ts — getOrders(), the template literal query
Handoff deception:   Handoff claims inputs are validated. The sortBy parameter is NOT validated.
False positive risk: None — this is a textbook SQL injection.
```

```
ID:                  SEED-CR-03
Category:            Spec alignment / validation gap
Seeded issue:        Spec says "orders with 0 quantity should be rejected" (AC-2). The validateOrder()
                     function only checks `quantity < 0`, not `quantity <= 0`. Zero-quantity items pass.
                     The handoff claims "AC-2: Zero quantity rejected — Done."
CR Dimension:        1. Spec Alignment
Expected severity:   Required
Expected signal:     CR cross-references the spec AC-2 against validateOrder() and finds the
                     off-by-one: `< 0` should be `<= 0`.
Evidence path:       project/src/order-processor.ts — validateOrder(), the quantity check
Handoff deception:   Handoff explicitly claims AC-2 is met.
False positive risk: None.
```

```
ID:                  SEED-CR-04
Category:            Function quality / score inflation
Seeded issue:        All 6 functions scored 100/100 with "None" findings. createOrder() has CC=6,
                     mixes validation orchestration with persistence and discount resolution.
                     The "skepticism pass" is perfunctory (one sentence).
CR Dimension:        7. Function Quality Assessment
Expected severity:   Required (missing genuine skepticism pass for all-100 non-trivial change)
Expected signal:     CR flags that a 6-function change with every score at 100/100 needs a real
                     skepticism pass. createOrder() at CC=6 should not be 100/100.
Evidence path:       reports/programmer-handoff.md — Function Quality Assessment table
Handoff deception:   Claims skepticism pass was done but it's one sentence.
False positive risk: Low.
```

```
ID:                  SEED-CR-05
Category:            Test quality / shared mutable state + weak assertions
Seeded issue:        Tests use a module-level `testOrderCount` counter that makes test execution
                     order-dependent. Multiple assertions use `toBeTruthy()` on arrays/objects
                     which passes even when the value is wrong (e.g., array with errors is truthy).
CR Dimension:        3. Test Quality
Expected severity:   Required (shared mutable state) + Recommended (weak assertions)
Expected signal:     CR flags the module-level counter as order-dependent shared state.
                     CR flags toBeTruthy() on arrays as non-specific assertion.
Evidence path:       project/src/__tests__/order-processor.test.ts — testOrderCount, toBeTruthy calls
Handoff deception:   Handoff claims "12 tests covering validation, creation, retrieval, errors."
False positive risk: Low.
```

```
ID:                  SEED-CR-06
Category:            Security / PII in logs
Seeded issue:        logOrderError() includes customer.cardLast4 in the console.log output.
                     While "last 4" is less sensitive than a full card number, it is still payment
                     card data that should not appear in application logs per AC-6.
CR Dimension:        5. Security Surface
Expected severity:   Required
Expected signal:     CR flags cardLast4 in log output as sensitive payment data leak.
Evidence path:       project/src/order-processor.ts — logOrderError(), context.cardLast4
Handoff deception:   Handoff claims "No sensitive data in logs — Done."
False positive risk: Medium — some reviewers may consider last4 acceptable. The spec says "no sensitive
                     customer data (credit card numbers)" — last4 is arguably within scope.
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

This is the **easy** eval. All 6 seeds are relatively surface-level and map
directly to well-known CR dimensions. A competent Code Review agent should catch
at least 5/6. The most likely miss is SEED-CR-06 (card last4 as PII) because
it requires judgment about what counts as "sensitive."
