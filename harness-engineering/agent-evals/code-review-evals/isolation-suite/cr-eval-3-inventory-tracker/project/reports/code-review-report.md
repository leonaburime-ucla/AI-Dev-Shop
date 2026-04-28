# Code Review Report -- Inventory Tracker

**Spec**: `spec-inv-tracker-v4-ghi789`
**Date**: 2026-04-26
**Reviewer**: Code Review Agent v1.1.1
**Source**: `project/src/inventory-tracker.ts` (286 lines)
**Tests**: `project/src/__tests__/inventory-tracker.test.ts` (476 lines)
**Programmer Handoff**: `reports/programmer-handoff.md`

---

## Verdict: BLOCKED -- 3 Required findings

The implementation is well-structured and covers most spec requirements, but
contains one critical spec misalignment (admin override records the wrong user
in audit logs), one missing spec requirement (transfer ignores destination
capacity), and a test hygiene issue (global fake timers never restored). These
must be fixed before proceeding.

---

## Findings

### CR-001

```
ID:          CR-001
Severity:    Required
Dimension:   Spec Alignment (AC-6)
File:        src/inventory-tracker.ts:169-170

Finding:
bulkAdjust replaces adjustedBy with override.adminId when an admin override is
present. This directly violates AC-6 and Non-Functional Requirement 2, which
state: "Admin overrides should still record the original requester in audit
logs (not the admin who approved the override)."

The code:
  const effectiveAdjustment = override
    ? { ...adjustment, adjustedBy: override.adminId }
    : adjustment;

This overwrites the original requester (adjustment.adjustedBy) with the admin's
ID, which is the opposite of the spec requirement. The audit trail will show
ADMIN-001 as the requester instead of USER-001.

Evidence:
- Spec requirement AC-6: "History log records the original requester, even
  for admin-override operations."
- NFR-2: "Admin overrides should still record the original requester in audit
  logs (not the admin who approved the override)."
- The programmer handoff claims AC-6 is "Done" with note "adjustedBy from the
  adjustment, not overridden" -- this is false. The code does override it.

Impact:
Audit trail integrity is compromised. In a compliance or investigation
scenario, the original requester is invisible and the admin appears as the
requester. This is a correctness defect in a security-relevant data path.

Required Action:
Remove the adjustedBy override. The effectiveAdjustment should preserve the
original adjustment.adjustedBy. If the admin override needs to be recorded,
add a separate field (e.g., approvedBy) to the HistoryEntry type, or log
it as a separate audit event. Do not replace the original requester.

Suggested Next Route:
Programmer Agent to fix. TestRunner to verify.
```

### CR-002

```
ID:          CR-002
Severity:    Required
Dimension:   Spec Alignment (AC-5, Requirement 4)
File:        src/inventory-tracker.ts:199-241

Finding:
transferStock bypasses capacity enforcement on the destination warehouse.
The function directly calls store.setStock for the destination without
checking whether the resulting stock would reach or exceed maxCapacity.

The spec says: "Each warehouse has a maxCapacity. Stock additions that would
cause the warehouse stock to reach capacity must be rejected." A transfer
adds stock to the destination warehouse, so it is a stock addition subject
to capacity enforcement.

Evidence:
- Spec Requirement 4: capacity enforcement applies to all additions.
- adjustStock correctly enforces capacity (lines 115-126), but transferStock
  does not call adjustStock -- it directly manipulates stock via setStock.
- No test covers a transfer that would exceed destination capacity.

Impact:
A transfer can silently overfill a destination warehouse, violating the
capacity invariant that adjustStock enforces.

Required Action:
Either route the destination addition through adjustStock (which already
enforces capacity), or replicate the capacity check before setting
destination stock. Add tests for this scenario.

Suggested Next Route:
Programmer Agent to fix. TestRunner to verify.
```

### CR-003

```
ID:          CR-003
Severity:    Required
Dimension:   Test Quality (AC-7)
File:        src/__tests__/inventory-tracker.test.ts:22

Finding:
jest.useFakeTimers() is called at module scope (line 22) but is never
restored with jest.useRealTimers() in an afterAll or afterEach block.
This leaks fake timer state to any test file that runs after this one in
the same Jest worker, violating AC-7: "Async tests clean up timer state
between test runs."

Evidence:
- AC-7 explicitly requires timer cleanup.
- The programmer handoff claims AC-7 is "Done" with note "Fake timers
  used consistently" -- but using them consistently is not the same as
  cleaning them up.

Impact:
Timer leak can cause flaky or order-dependent failures in downstream test
files sharing the same Jest worker process.

Required Action:
Add an afterAll (or afterEach) block that calls jest.useRealTimers().

Suggested Next Route:
Programmer Agent to fix.
```

### CR-004

```
ID:          CR-004
Severity:    Required
Dimension:   Spec Alignment (AC-6) / Test Quality
File:        src/__tests__/inventory-tracker.test.ts:203-214

Finding:
The test "should apply admin override when provided" (line 203) does not
verify that the original requester is preserved in the audit history. It
only asserts that store.setStock was called, which proves nothing about
AC-6 compliance. This test should fail given the bug in CR-001, but it
passes because it asserts the wrong thing.

Evidence:
- The test creates an adjustment with adjustedBy: 'USER-001' and an override
  with adminId: 'ADMIN-001', but never checks what adjustedBy value was
  recorded in the history entry.
- A correct test would assert that store.addHistory was called with
  adjustedBy: 'USER-001' (the original requester), not 'ADMIN-001'.

Impact:
The test suite gives false confidence that AC-6 is met. The bug in CR-001
is invisible to the test suite.

Required Action:
Rewrite the test to assert that store.addHistory was called with the
original requester's user ID (adjustment.adjustedBy), not the admin's ID.

Suggested Next Route:
Programmer Agent to fix alongside CR-001.
```

### CR-005

```
ID:          CR-005
Severity:    Recommended
Dimension:   Non-Functional Characteristics
File:        src/inventory-tracker.ts:199-241

Finding:
transferStock is not atomic. If the source setStock succeeds (line 215)
but the destination setStock or addHistory fails, the source warehouse
has been debited but the destination has not been credited. Stock is lost.

Evidence:
- Lines 215-220: source is debited first, destination credited second.
  If the store throws between these calls, the system is in an
  inconsistent state.
- The programmer handoff acknowledges this as known debt ("lacks
  transaction wrapping") with a score of 90/100.

Impact:
In production with a real store that can fail, a partial transfer would
result in lost inventory with no automatic recovery path.

Required Action:
Not blocking for the current in-memory store use case, but should be
addressed before any durable store integration. Document as a required
pre-production item.

Suggested Next Route:
Refactor Agent for transaction wrapper when a durable store is introduced.
```

### CR-006

```
ID:          CR-006
Severity:    Recommended
Dimension:   Test Quality / Non-Functional
File:        src/__tests__/inventory-tracker.test.ts:418-433

Finding:
The test "should handle concurrent adjustments to same product" is
misleading. Both concurrent calls read the same mocked value (50) and
compute independently, so the test proves mock behavior, not real
concurrency safety. The test name implies concurrency handling but
actually demonstrates a race condition (both calls produce results
based on stale reads).

Evidence:
- Both calls resolve getStock to 50 (the default mock).
- r1 = 60, r2 = 70, but the actual final stock should be 80 if both
  adjustments were applied correctly (50 + 10 + 20).
- The test comments acknowledge this: "Both read currentStock=50, so
  both compute independently."

Impact:
The test gives false confidence about concurrency behavior. A reader
might assume concurrency is handled when it is explicitly not.

Required Action:
Either rename the test to clarify it demonstrates a known race condition
limitation, or remove it and document the concurrency limitation in
known debt.

Suggested Next Route:
Refactor Agent.
```

### CR-007

```
ID:          CR-007
Severity:    Recommended
Dimension:   Code Quality
File:        src/inventory-tracker.ts:115-117

Finding:
When warehouse lookup returns null (line 117), the capacity check is
silently skipped and the addition proceeds without limit. This means
a misconfigured or missing warehouse allows unlimited stock additions.

Evidence:
- Line 117: if (warehouse) { ... } -- null warehouse means no capacity
  check.
- Test at line 133: "should handle warehouse not found gracefully"
  confirms stock can be set to 250 in a warehouse with no capacity limit.

Impact:
Silent bypass of a safety invariant. If the store has a data integrity
issue (missing warehouse record), the capacity invariant is silently
dropped rather than failing fast.

Required Action:
Consider throwing an error when the warehouse is not found instead of
silently skipping capacity enforcement. At minimum, document this as an
intentional design decision.

Suggested Next Route:
Programmer Agent to evaluate fail-fast vs. skip behavior.
```

### CR-008

```
ID:          CR-008
Severity:    Recommended
Dimension:   Function Quality Assessment
File:        src/inventory-tracker.ts (module-level)

Finding:
The programmer's debt-band local fix for adjustStock (88/100) consisted
of adding inline comments. Comments are documentation, not a structural
fix. The finding was "validation and persistence are in the same function"
-- adding comments does not change the function's structure or reduce its
coupling. The score should not have changed as a result of comments alone.

Similarly, bulkAdjust at 85/100 had no local fix attempted beyond
acknowledging the issue.

Evidence:
- Handoff: "Added inline comments explaining the capacity check boundary
  condition" as the debt-band fix.
- The function-quality-assessment skill requires a "local fix cycle" for
  80-89 scores. Adding comments is not a fix for a structural finding.

Impact:
The debt band documentation gives the appearance of a fix attempt without
an actual structural improvement.

Required Action:
Not blocking, but the debt-band fix claim should be reclassified. The
scores are honest but the fix narrative is inflated. Document that the
local fix was documentation-only and the structural debt remains.

Suggested Next Route:
Refactor Agent for actual extraction of validation logic.
```

### CR-009

```
ID:          CR-009
Severity:    Recommended
Dimension:   Test Quality
File:        src/__tests__/inventory-tracker.test.ts

Finding:
No adversarial aggregate/cross-item test exists for bulkAdjust. The bulk
operation is a batch processor where earlier adjustments can change store
state that affects validation of later adjustments in the same batch. No
test verifies this interaction.

For example: if a bulk batch contains [add 40 to WH-1, add 40 to WH-1]
and WH-1 has maxCapacity=100 with currentStock=50, the first addition
succeeds (stock=90) but the second should fail capacity check (90+40=130
>= 100). No test covers this sequential dependency within a batch.

Evidence:
- The function-quality-assessment skill requires "at least one adversarial
  aggregate/cross-item test or direct probe" for batch processors.
- No such test exists in the test file.

Impact:
Missing coverage for a key batch behavior pattern.

Required Action:
Add at least one test where earlier items in a bulk batch affect the
validation outcome of later items.

Suggested Next Route:
Programmer Agent to add test.
```

---

## Dimension Summary

| Dimension | Status | Findings |
|-----------|--------|----------|
| 1. Spec Alignment | FAIL | CR-001 (admin override records wrong user), CR-002 (transfer skips capacity), CR-004 (test doesn't verify AC-6) |
| 2. Architecture Adherence | PASS | Clean DI pattern, interfaces for store and clock, no layering violations |
| 3. Test Quality | FAIL | CR-003 (timer leak), CR-004 (wrong assertion), CR-006 (misleading concurrency test), CR-009 (missing adversarial batch test) |
| 4. Code Quality | PASS with notes | CR-007 (silent null warehouse bypass), CR-008 (debt fix is comments-only) |
| 5. Security Surface | PASS with notes | CR-001 is also a security/audit concern; no new endpoints or external calls |
| 6. Non-Functional | PASS with notes | CR-005 (non-atomic transfer), CR-006 (false concurrency safety) |
| 7. Function Quality | DEBT | See assessment section below |

---

## Function Quality Assessment

- Status: DEBT
- Functions assessed: 5
- Lowest score: 85/100 (bulkAdjust)
- Critical findings: 1 (CR-001: audit trail integrity -- wrong user recorded)
- High findings: 1 (CR-002: capacity bypass on transfer destination)
- Missing assessments: 0
- Missing handoff-table evidence: no
- Missing score-skepticism evidence: n/a (no all-100 scores)
- Missing adversarial aggregate/cross-item evidence: yes (CR-009)
- Required fixes: (1) Fix admin override to preserve original requester in audit logs. (2) Add capacity check to transfer destination. (3) Fix timer cleanup. (4) Fix admin override test to assert correct adjustedBy.
- Recommended refactors: (1) Extract validation from adjustStock. (2) Add transaction wrapper to transferStock. (3) Reclassify debt-band fix as documentation-only. (4) Add adversarial batch test. (5) Clarify or remove misleading concurrency test. (6) Evaluate fail-fast for missing warehouse.
- Suggested next route: Programmer

### Independent Score Re-assessment

| Function | Programmer Score | Reviewer Score | Delta | Notes |
|----------|-----------------|---------------|-------|-------|
| adjustStock | 88/100 | 84/100 | -4 | Silent null-warehouse bypass is a correctness risk, not just a style issue. Debt-band fix was comments-only. |
| bulkAdjust | 85/100 | 72/100 | -13 | Critical: overwrites original requester with admin ID, violating AC-6. This is a correctness defect in a security-relevant path. Score drops below 80 threshold. |
| transferStock | 90/100 | 82/100 | -8 | Missing capacity check on destination violates AC-5. Non-atomic writes are acknowledged debt. |
| getTotalStock | 92/100 | 92/100 | 0 | Agree. Simple and correct. |
| getStockHistory | 95/100 | 95/100 | 0 | Agree. Thin delegation, no issues. |

bulkAdjust drops below 80 due to the critical AC-6 violation (CR-001), which
is a hard block per the function-quality-assessment scoring rules.

---

## Routing Recommendation

**Route to**: Programmer Agent

**Required before re-review**:
1. Fix CR-001: Remove admin ID override in bulkAdjust; preserve original requester
2. Fix CR-002: Add capacity check for transfer destination warehouse
3. Fix CR-003: Add afterAll with jest.useRealTimers()
4. Fix CR-004: Rewrite admin override test to assert correct adjustedBy in history

**Recommended for follow-up**:
- CR-005, CR-006, CR-007, CR-008, CR-009 (route to Refactor Agent after Required fixes are verified)
