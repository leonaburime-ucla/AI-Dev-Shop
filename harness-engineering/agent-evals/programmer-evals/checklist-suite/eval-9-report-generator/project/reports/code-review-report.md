# Code Review Report -- Sales Report Generator

**Reviewer**: Code Review Agent v1.1.1
**Date**: 2026-04-26
**Spec**: project-brief.md (Sales Report Generator)
**Source**: src/reporter.ts
**Tests**: src/__tests__/reporter.test.ts
**Programmer Handoff**: reports/programmer-handoff.md

---

## Review Summary

The Programmer rewrote the module to fix 6 material bugs (PII leak, missing dedup, wrong aggregation, missing rounding, floating-point drift, over-engineering). The rewrite is well-decomposed, pure, has no external dependencies, and passes 35 tests at 98.5%+ statement coverage. Two Required findings and four Recommended findings are documented below.

---

## Findings

---

```
ID:          CR-001
Severity:    Required
Dimension:   Spec Alignment / Correctness

Finding:
roundTwo() produces incorrect results for negative midpoint values.
The rounding helper uses (value + Number.EPSILON) * 100, which biases
toward +Infinity. For negative midpoint values such as -1.005, the
expected result under standard banker-neutral or school rounding is
-1.01, but roundTwo(-1.005) returns -1.0 (as confirmed by the test on
line 429 which asserts expect(roundTwo(-1.005)).toBe(-1)).

The spec states "negative amounts (refunds reduce revenue)" and "all
report fields must be numbers rounded to 2 decimal places" (reqs 5, 6).
When a refund amount like -1.005 is rounded to -1.00 instead of -1.01,
the report overstates net revenue by $0.01 per such transaction. This
is a monetary correctness issue.

Evidence:
  reporter.ts:82  Math.round((value + Number.EPSILON) * 100) / 100
  reporter.test.ts:428-429  expect(roundTwo(-1.005)).toBe(-1);
  The test encodes the broken behavior as "passing."

Impact:
Monetary values involving negative midpoint rounding will be off by
$0.01. Over many refund transactions this accumulates into a
systematically inaccurate revenue figure.

Required Action:
Replace the EPSILON-based rounding with a method that handles negative
midpoints correctly, e.g.:
  Math.round(Math.abs(value) * 100 + Number.EPSILON) / 100 * Math.sign(value)
or use a toFixed-parseFloat approach. Update the test on line 429 to
assert roundTwo(-1.005) === -1.01.

Suggested Next Route:
Programmer Agent to fix, TestRunner to verify.
```

---

```
ID:          CR-002
Severity:    Required
Dimension:   Spec Alignment

Finding:
normalizeRegion() is exported and documented but never called in the
report pipeline. Region values flow into computeRevenueByRegion() and
DetailedTransaction.region as-is from the raw transaction. If the same
logical region arrives with different casing or whitespace (e.g.,
"North America" vs "  north america  "), the report will create
separate buckets instead of aggregating them.

The spec says "Group and aggregate by region" (req 4). Without
normalization, grouping is silently fragile.

Evidence:
  reporter.ts:364-366 -- normalizeRegion is defined and exported
  reporter.ts:169-180 -- computeRevenueByRegion uses t.region raw
  No call to normalizeRegion anywhere in generateReport or helpers

Impact:
Reports may show duplicate region entries for the same logical region,
producing incorrect per-region revenue and confusing consumers.

Required Action:
Apply normalizeRegion() (or equivalent) to t.region in the aggregation
pipeline -- at minimum inside computeRevenueByRegion,
topCustomersBySpend, and the DetailedTransaction mapping.
Alternatively, normalize once at the dedup/validate stage so all
downstream code sees clean region strings. Add a test with mixed-case
region inputs to verify aggregation.

Suggested Next Route:
Programmer Agent to fix, TestRunner to verify.
```

---

```
ID:          CR-003
Severity:    Recommended
Dimension:   Test Quality

Finding:
The test for roundTwo(-1.005) on line 429 asserts the wrong expected
value. It encodes the current buggy behavior (returning -1) rather
than the correct behavior (-1.01). This means the test suite will
pass even when the rounding is wrong for negative midpoints.

More broadly, there are no tests that exercise region normalization
edge cases (mixed case, trailing whitespace) through generateReport,
since normalizeRegion is never called in the pipeline.

Evidence:
  reporter.test.ts:428-429

Impact:
Test suite provides false confidence about negative rounding and
region aggregation correctness.

Required Action:
Fix test assertion after CR-001 is resolved. Add region normalization
integration test after CR-002 is resolved.

Suggested Next Route:
Programmer Agent (addressed alongside CR-001 and CR-002).
```

---

```
ID:          CR-004
Severity:    Recommended
Dimension:   Code Quality and Maintainability

Finding:
isValidFormat() cannot practically reject bad input because TypeScript
narrowing on the ReportFormat union means the runtime check at line 261
is reached only when the caller bypasses the type system (e.g., "as any"
cast). The runtime guard is harmless but the comment and error path are
effectively dead code in well-typed callers.

Meanwhile, isValidTransaction() silently drops invalid transactions
with no logging or indication of how many were filtered. In a
production context this makes debugging data quality issues difficult.

Evidence:
  reporter.ts:93-95, 261-263 -- format guard
  reporter.ts:105-113, 273 -- silent filter

Impact:
Minor. Silent filtering is a maintainability concern, not a
correctness issue, since the spec does not mandate error reporting
for invalid records.

Recommended Action:
Consider returning a diagnostics count (e.g., droppedCount) in the
report, or documenting the silent-drop behavior more prominently.
No blocking action required.

Suggested Next Route:
Refactor Agent if addressed.
```

---

```
ID:          CR-005
Severity:    Recommended
Dimension:   Non-Functional Characteristics

Finding:
computeDateRange() constructs a new Date object per transaction twice
(once for comparison, once could be optimized). For large transaction
arrays this is fine at typical scale, but the function also does not
guard against invalid date strings -- new Date('garbage').getTime()
returns NaN, which would silently corrupt min/max and produce
"Invalid Date" in output.

Evidence:
  reporter.ts:190-204

Impact:
Low in the current context (isValidTransaction checks for t.date
truthy but not date validity). A transaction with
date: "not-a-date" passes validation and corrupts the date range.

Recommended Action:
Add a date-validity check to isValidTransaction or
computeDateRange. Not blocking since the spec does not define
behavior for malformed dates, but it is a latent defect.

Suggested Next Route:
Refactor Agent.
```

---

```
ID:          CR-006
Severity:    Recommended
Dimension:   Security Surface

Finding:
The Transaction interface includes customerEmail (required) and
optional customerPhone/customerNotes. The PII stripping is correct --
the report output never includes these fields. However, the
Transaction type is exported, which means downstream consumers receive
the full PII-bearing type in their IDE autocomplete. This is not a
runtime leak but increases the risk of accidental PII exposure in
future code that handles Transaction objects.

Evidence:
  reporter.ts:12-23 -- Transaction is exported with PII fields

Impact:
Low. No runtime PII leak exists. The concern is about future
maintenance and accidental misuse of the exported type.

Recommended Action:
Consider exporting a separate InputTransaction or
SanitizedTransaction type that omits PII fields, or clearly document
that Transaction is an input-only type whose PII fields must never
appear in output. Not blocking.

Suggested Next Route:
Refactor Agent if addressed.
```

---

## Dimension Summary

| # | Dimension | Status |
|---|-----------|--------|
| 1 | Spec Alignment | 2 Required findings (CR-001, CR-002) |
| 2 | Architecture Adherence | Clean -- single module, pure functions, no dependency violations |
| 3 | Test Quality | 1 Recommended (CR-003) -- test encodes buggy behavior; otherwise strong at 35 tests |
| 4 | Code Quality and Maintainability | 1 Recommended (CR-004) -- silent filtering, minor dead code |
| 5 | Security Surface | 1 Recommended (CR-006) -- exported PII-bearing type, no runtime leak |
| 6 | Non-Functional Characteristics | 1 Recommended (CR-005) -- no date validation, acceptable at current scale |
| 7 | Function Quality Assessment | See section below |

---

## Function Quality Assessment

- Status: **DEBT**
- Functions assessed: 11
- Lowest score: 92 (roundTwo -- re-scored from Programmer's 100 due to CR-001)
- Critical findings: 0
- High findings: 1 (CR-001: monetary rounding incorrect for negative midpoints)
- Missing assessments: 0
- Missing handoff-table evidence: no
- Missing score-skepticism evidence: no (Programmer documented skepticism pass)
- Missing adversarial aggregate/cross-item evidence: no (dedup, customer aggregation, and cross-format PII tests present)
- Required fixes: Fix roundTwo for negative midpoint rounding (CR-001); integrate normalizeRegion into pipeline (CR-002)
- Recommended refactors: Fix test assertion for negative rounding (CR-003); add date validation (CR-005); consider PII-safe exported types (CR-006); add dropped-record diagnostics (CR-004)
- Suggested next route: **Programmer**

### Independent Re-Scoring

| Function | Programmer Score | Reviewer Score | Delta | Reason |
|----------|:---:|:---:|:---:|--------|
| roundTwo | 100 | 92 | -8 | Negative midpoint rounding incorrect (CR-001) |
| isValidFormat | 100 | 100 | 0 | Clean |
| isValidTransaction | 100 | 95 | -5 | No date-validity check (CR-005) |
| deduplicateById | 100 | 100 | 0 | Clean |
| topCustomersBySpend | 100 | 98 | -2 | Does not normalize region (minor, primary impact in computeRevenueByRegion) |
| computeRevenueByRegion | 100 | 93 | -7 | Missing region normalization (CR-002) |
| computeDateRange | 100 | 95 | -5 | No NaN guard on invalid dates (CR-005) |
| generateReport | 95 | 93 | -2 | Inherits CR-001 and CR-002 through helpers |
| formatCurrency | 100 | 100 | 0 | Clean |
| isWithinRange | 100 | 100 | 0 | Clean |
| normalizeRegion | 100 | 100 | 0 | Clean function, but dead code in pipeline |

### Score Skepticism Review

The Programmer's skepticism pass stated "Multiple functions score 100/100. Justified because they are 3-12 line pure functions with CC 1-2." This explanation is partially valid -- the functions are indeed small and pure. However, the skepticism pass missed:

1. roundTwo has a subtle negative-value bug despite being 3 lines.
2. normalizeRegion exists but is unused, meaning the region aggregation functions lack normalization they should have.
3. computeDateRange has no NaN guard.

The skepticism pass was present but insufficiently rigorous. Small function size does not guarantee correctness, particularly for edge-case-sensitive arithmetic.

---

## Verdict

**BLOCKED on 2 Required findings (CR-001, CR-002).** The Programmer should fix the negative midpoint rounding in roundTwo and integrate normalizeRegion into the aggregation pipeline, then update tests accordingly. Once resolved, 4 Recommended findings can be addressed by the Refactor Agent or deferred as documented tech debt.
