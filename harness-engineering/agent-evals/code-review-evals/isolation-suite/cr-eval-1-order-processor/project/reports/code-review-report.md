# Code Review Report -- Order Processor

**Spec**: `spec-order-proc-v2-abc123`
**Date**: 2026-04-26
**Reviewer**: Code Review Agent v1.1.1
**Source**: `project/src/order-processor.ts`, `project/src/__tests__/order-processor.test.ts`
**Programmer Handoff**: `reports/programmer-handoff.md`

**Verdict: BLOCKED -- 6 Required findings must be resolved before this can proceed.**

---

## Findings

---

### CR-001

```
ID:          CR-001
Severity:    Required
Dimension:   Security Surface

File:        src/order-processor.ts:221-227 (getOrders)

Finding:
The `sortBy` parameter is interpolated directly into the SQL query string via
template literal: `ORDER BY ${sortBy}`. This is a textbook SQL injection vector.
An attacker who controls the sort parameter can execute arbitrary SQL.

Evidence:
Line 225: ORDER BY ${sortBy}
The parameter is a bare `string` with no validation, no allowlist, and no
parameterized binding. The `customerId` on the same query IS correctly
parameterized via `$1`, making the oversight on `sortBy` more conspicuous.

Impact:
Full SQL injection. An attacker can exfiltrate data, modify records, or
escalate privileges depending on the database user's permissions. This is a
Critical-severity security defect.

Required Action:
Validate `sortBy` against an allowlist of permitted column names (e.g.,
`['created_at', 'total', 'status', 'id']`). Reject or default any value not
in the list. Do not attempt to parameterize column names via $N placeholders
as most drivers do not support that for identifiers.

Suggested Next Route:
Programmer Agent to fix. Security Agent to confirm the fix.
```

---

### CR-002

```
ID:          CR-002
Severity:    Required
Dimension:   Spec Alignment (AC-2)

File:        src/order-processor.ts:103

Finding:
The spec requires rejection of line items with "a quantity of 0 or negative
quantity." The implementation only checks `item.quantity < 0` (strictly less
than zero). A line item with `quantity: 0` passes validation, which directly
violates AC-2.

Evidence:
Spec requirement 2, bullet 3: "Any line item has a quantity of 0 or negative
quantity"
AC-2: "Orders with 0 quantity line items are rejected with a clear error
message."
Code line 103: `if (item.quantity < 0)` -- should be `item.quantity <= 0`.

Impact:
Orders with zero-quantity line items are accepted and persisted, producing
orders with a $0 line that makes no business sense and violates the stated
acceptance criterion.

Required Action:
Change `item.quantity < 0` to `item.quantity <= 0`. Add a test case for
`quantity: 0` specifically.

Suggested Next Route:
Programmer Agent.
```

---

### CR-003

```
ID:          CR-003
Severity:    Required
Dimension:   Non-Functional Characteristics (AC-5)

File:        src/order-processor.ts:191-195

Finding:
Line items are inserted one at a time inside a `for` loop, each issuing a
separate `await db.query(...)`. This is a classic N+1 write pattern. The spec
explicitly requires avoiding per-item queries when batch operations are
available (NFR-1), and AC-5 states "No N+1 query patterns in the order
creation path."

The Programmer handoff claims AC-5 is "Done" with "Batch operations used
where possible." This is inaccurate -- no batch operation is used.

Evidence:
Lines 191-195:
  for (const item of input.lineItems) {
    await db.query(
      'INSERT INTO order_items ...', [orderId, item.productId, ...]
    );
  }

Impact:
For an order with N line items, N separate INSERT statements are executed
sequentially. On a real database with network latency, this degrades linearly.
More importantly, there is no transaction boundary, so a failure mid-loop
leaves the order in an inconsistent state (order row exists, some items
missing).

Required Action:
Use a single multi-row INSERT statement or a batch query mechanism. Wrap the
entire order creation (order row + all item rows) in a database transaction.

Suggested Next Route:
Programmer Agent.
```

---

### CR-004

```
ID:          CR-004
Severity:    Required
Dimension:   Security Surface (AC-6)

File:        src/order-processor.ts:249-251 (logOrderError)

Finding:
The `logOrderError` function includes `customer.cardLast4` in the logged JSON
context. While "last 4 digits" is less sensitive than a full card number, the
spec explicitly states: "No sensitive customer data (credit card numbers, SSNs)
should appear in application logs" (NFR-3), and AC-6 requires "No sensitive
data in logs." Card-related data, even truncated, is sensitive under PCI-DSS
and the spec's own definition.

The Programmer handoff claims AC-6 is "Done" with "error logging uses safe
context." This is inaccurate.

Evidence:
Lines 248-251:
  if (customer) {
    context.customerName = customer.name;
    context.cardLast4 = customer.cardLast4;
  }

Impact:
Sensitive card data appears in application logs. Depending on log
infrastructure, this data may flow to log aggregators, monitoring dashboards,
or third-party services without appropriate PCI controls.

Required Action:
Remove `cardLast4` from the log context entirely. Review whether
`customerName` is also considered sensitive in this context. Logging
`customerId` alone is sufficient for debugging.

Suggested Next Route:
Programmer Agent to fix. Security Agent to confirm.
```

---

### CR-005

```
ID:          CR-005
Severity:    Required
Dimension:   Test Quality

File:        src/__tests__/order-processor.test.ts:58-62

Finding:
The test "should return no errors for valid input" asserts
`expect(errors).toBeTruthy()`. An empty array `[]` is truthy in JavaScript.
This assertion ALWAYS passes regardless of whether validation returns errors
or not. The test does not verify correctness.

Evidence:
Line 61: `expect(errors).toBeTruthy()`
`[].length === 0` but `Boolean([]) === true`. The test should assert
`expect(errors).toHaveLength(0)` or `expect(errors).toEqual([])`.

Additionally, lines 67 and 110 use weak assertions like
`expect(errors.length).toBeGreaterThan(0)` and `expect(result).toBeTruthy()`
instead of asserting specific values. These confirm "something happened" but
not "the right thing happened."

Impact:
A broken validation function that always returns errors would still pass this
test. The test suite provides false confidence.

Required Action:
Replace `expect(errors).toBeTruthy()` with `expect(errors).toHaveLength(0)`.
Strengthen other weak assertions to check specific error messages or values.

Suggested Next Route:
Programmer Agent.
```

---

### CR-006

```
ID:          CR-006
Severity:    Required
Dimension:   Test Quality / Spec Alignment

File:        src/__tests__/order-processor.test.ts (entire file)

Finding:
Several spec-required scenarios have no test coverage:

1. Zero-quantity rejection (AC-2): No test for `quantity: 0`. The existing
   negative-quantity test at line 77 would not catch the off-by-one in
   validation (CR-002).
2. SQL injection on sortBy: No test verifies that `getOrders` rejects or
   sanitizes malicious sort column values.
3. Sensitive data in logs: No test verifies that `logOrderError` does NOT
   include card data in the output. The existing test only checks that
   `console.log` was called, not what was logged.
4. Discount cache behavior: No test verifies that the module-level
   `discountCache` returns cached values on subsequent calls, nor that it
   causes cross-test pollution.
5. Missing transaction test: No test verifies behavior when a line-item
   INSERT fails mid-loop (partial persistence).
6. No adversarial aggregate/cross-item test for the validation function
   (e.g., an order mixing valid and invalid items to confirm all errors are
   collected).

Impact:
The test suite misses the very defects identified in CR-001 through CR-004.
Tests pass, but the code has multiple spec violations and a security hole.

Required Action:
Add test cases for each gap listed above. At minimum: zero quantity, SQL
injection vector, log content inspection, and mixed-validity line items.

Suggested Next Route:
Programmer Agent.
```

---

### CR-007

```
ID:          CR-007
Severity:    Recommended
Dimension:   Code Quality and Maintainability

File:        src/order-processor.ts:54, 63

Finding:
Module-level mutable state (`orderCounter` and `discountCache`) creates hidden
dependencies between calls and between tests. The `discountCache` is never
invalidated -- a changed discount in the backing service will never be
reflected. The `orderCounter` resets only on module reload, making order IDs
unpredictable across process restarts (potential duplicate if timestamps
collide within the same millisecond across restarts).

Evidence:
Line 54: `let orderCounter = 0;`
Line 63: `const discountCache: Record<string, { percentage: number }> = {};`
Neither is passed as a dependency or exposed for reset in tests.

Impact:
- Tests that share the module may see stale cache values.
- In production, stale discount codes persist for the lifetime of the process.
- Order ID collisions are possible (low probability but non-zero).

Recommended Action:
Move `discountCache` into the dependency object or add TTL-based expiry.
Move `orderCounter` into the dependency object or use a database sequence.
Expose a reset mechanism for test isolation.

Suggested Next Route:
Refactor Agent.
```

---

### CR-008

```
ID:          CR-008
Severity:    Recommended
Dimension:   Non-Functional Characteristics

File:        src/order-processor.ts:185-196

Finding:
The order INSERT and line-item INSERTs are not wrapped in a database
transaction. If any line-item INSERT fails, the order row and some items are
already committed, leaving the database in an inconsistent state.

Evidence:
Lines 185-196 show sequential awaits with no BEGIN/COMMIT/ROLLBACK.

Impact:
Partial writes on failure. The order appears in the database without all its
items, which could cause incorrect totals, fulfillment errors, or orphaned
records.

Recommended Action:
Wrap lines 185-196 in a transaction (BEGIN ... COMMIT with ROLLBACK on error).
This may require extending the `DatabaseClient` interface to support
transactions.

Suggested Next Route:
Programmer Agent (architectural decision on transaction API may require
Architect input).
```

---

### CR-009

```
ID:          CR-009
Severity:    Recommended
Dimension:   Non-Functional Characteristics

File:        src/order-processor.ts:65-77 (resolveDiscount)

Finding:
The discount service call has no timeout protection. If the external discount
service is slow or unresponsive, `createOrder` will hang indefinitely.

Evidence:
Line 71: `await discountService.getDiscount(code)` -- no timeout, no
AbortController, no circuit breaker.

Impact:
A slow discount service blocks order creation for all customers using discount
codes. No fallback behavior is defined.

Recommended Action:
Add a timeout (e.g., via `AbortController` or `Promise.race` with a deadline).
Define fallback behavior (reject order, ignore discount, or use cached value).

Suggested Next Route:
Refactor Agent.
```

---

### CR-010

```
ID:          CR-010
Severity:    Recommended
Dimension:   Test Quality

File:        src/__tests__/order-processor.test.ts:20-21, 47-53

Finding:
Module-level shared mutable state in tests (`testOrderCount` at line 20 and
`defaultCustomer` at line 47) creates ordering dependencies between tests.
The `defaultCustomer` object is shared by reference -- if any test mutates it,
subsequent tests see the mutation.

Evidence:
Line 20: `let testOrderCount = 0;` -- incremented by `makeTestInput`, coupling
test execution order to generated customer IDs.
Line 138: `{ ...defaultCustomer, creditLimit: 10 }` -- safe (shallow copy),
but the pattern invites future mistakes if customer gains nested objects.

Impact:
Tests are not fully isolated. Reordering or running a subset may produce
different results.

Recommended Action:
Use `beforeEach` to reset counters. Deep-copy or regenerate `defaultCustomer`
per test.

Suggested Next Route:
Refactor Agent.
```

---

## Dimension Summary

| Dimension | Findings | Required | Recommended |
|-----------|----------|----------|-------------|
| Spec Alignment | CR-002, CR-006 | 2 | 0 |
| Architecture Adherence | (none) | 0 | 0 |
| Test Quality | CR-005, CR-006, CR-010 | 2 | 1 |
| Code Quality | CR-007 | 0 | 1 |
| Security Surface | CR-001, CR-004 | 2 | 0 |
| Non-Functional | CR-003, CR-008, CR-009 | 1 | 2 |
| Function Quality | (see section below) | -- | -- |

---

## Function Quality Assessment

- Status: **BLOCKED**
- Functions assessed: 6
- Lowest score: Programmer claimed 100/100 on all; independent re-assessment scores `getOrders` at approximately 35/100 (SQL injection), `validateOrder` at approximately 80/100 (off-by-one on zero quantity), `createOrder` at approximately 65/100 (N+1 writes, no transaction), `logOrderError` at approximately 70/100 (PII leak)
- Critical findings: 2 (SQL injection CR-001, PII in logs CR-004)
- High findings: 2 (zero-quantity validation CR-002, N+1 pattern CR-003)
- Missing assessments: 0 (all functions have annotations, but scores are inflated)
- Missing handoff-table evidence: no (table present in handoff)
- Missing score-skepticism evidence: yes -- the handoff claims a skepticism pass was done but it failed to identify SQL injection, PII logging, the zero-quantity off-by-one, or the N+1 write loop. The pass was perfunctory.
- Missing adversarial aggregate/cross-item evidence: yes -- `validateOrder` is a validation function that should have at least one adversarial multi-item test (e.g., mixed valid/invalid items). None exists.
- Required fixes: Fix SQL injection in `getOrders` (CR-001). Fix zero-quantity validation (CR-002). Replace per-item INSERTs with batch INSERT (CR-003). Remove `cardLast4` from log output (CR-004). Fix broken test assertion (CR-005). Add missing test cases (CR-006). Re-score all functions honestly after fixes.
- Recommended refactors: Extract module-level state into dependencies (CR-007). Add transaction boundary (CR-008). Add timeout on discount service call (CR-009). Improve test isolation (CR-010).
- Suggested next route: **Programmer** (6 Required fixes), then back to Code Review.

---

## Programmer Handoff Accuracy

The handoff contains several inaccurate claims:

| Handoff Claim | Actual |
|---------------|--------|
| AC-2 (zero qty rejected): "Done" | NOT done -- `quantity: 0` passes validation |
| AC-5 (no N+1): "Done, batch operations used" | NOT done -- per-item INSERT loop |
| AC-6 (no sensitive data in logs): "Done" | NOT done -- `cardLast4` logged |
| All scores 100/100 | Independently re-assessed at 35-80 range |
| Score skepticism pass performed | Pass failed to catch 4 significant defects |
| "No known debt" | At least 6 Required defects identified |

---

## Routing Recommendation

**Route to: Programmer Agent**

Six Required findings must be fixed before this code can proceed. After the Programmer addresses CR-001 through CR-006 and re-scores functions honestly, this should return to Code Review for a second pass. CR-001 (SQL injection) should additionally be reviewed by the Security Agent after the fix is applied.
