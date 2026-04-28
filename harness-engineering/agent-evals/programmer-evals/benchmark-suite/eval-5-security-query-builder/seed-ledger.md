# Seed Ledger — Eval 5: Secure Search Query Builder

## Seeds

ID: SEED-5A
Category: Security/privacy — SQL injection
Seeded issue: The starter code string-interpolates the sort field directly into SQL: `ORDER BY ${sortField}`. Since sortField comes from user input, this is SQL injection.
Expected owner: Programmer
Expected severity: Critical
Expected signal: Programmer must validate against allowlist before interpolating
Evidence path: src/query_builder.py — ORDER BY clause
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-5B
Category: Security/privacy — PII logging
Seeded issue: The log line includes the raw query text and filter values, which the brief says could contain PII. Violates the brief's "never log query text or filter values" requirement.
Expected owner: Programmer
Expected severity: Critical
Expected signal: Programmer removes PII from logs
Evidence path: src/query_builder.py — print() line
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-5C
Category: Resource bounds
Seeded issue: pageSize validation is missing. User can pass pageSize: 999999 and get an unbounded query. The brief says max 100.
Expected owner: Programmer
Expected severity: High
Expected signal: Programmer adds pageSize validation
Evidence path: src/query_builder.py — no page_size check
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-5D
Category: Predictable errors
Seeded issue: Invalid sort direction silently defaults to ASC instead of returning an error. Invalid page silently defaults to 1. This hides bad input.
Expected owner: Programmer
Expected severity: Medium
Expected signal: Fail-fast on invalid input per coding-foundations
Evidence path: src/query_builder.py — default fallbacks
Caught by Programmer:
Caught by Code Review:
False positive risk: Medium (could argue defaults are fine)
Framework change needed: No

ID: SEED-5E
Category: Typed/stable result
Seeded issue: The function return type is `any`. The brief specifies a typed return with sql, params, totalCountSql, totalCountParams.
Expected owner: Programmer
Expected severity: Medium
Expected signal: Programmer types the return
Evidence path: src/query_builder.py — return type
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-5F
Category: Stable boundaries
Seeded issue: The function takes 4 positional arguments instead of a required input object + optional options object.
Expected owner: Programmer
Expected severity: Medium
Expected signal: Two-object parameter convention
Evidence path: src/query_builder.py — function signature
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-5G
Category: Single responsibility
Seeded issue: The function validates input, builds WHERE clauses, builds ORDER BY, builds pagination, builds count query, AND logs — all in one 80+ line function.
Expected owner: Programmer
Expected severity: High
Expected signal: Extract into focused helpers
Evidence path: src/query_builder.py — monolithic function
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-5H
Category: Adversarial aggregate behavior
Seeded issue: No test for SQL injection attempts. No test for boundary values (pageSize=0, pageSize=101, empty tags array, tags with special characters). No test for combined filters.
Expected owner: Code Review
Expected severity: High
Expected signal: Missing adversarial/boundary tests
Evidence path: tests/test_query_builder.py
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-5I
Category: Function scoring
Seeded issue: @overallScore 100/100 on a function with SQL injection, PII logging, missing validation, and CC > 4. Blatant score inflation.
Expected owner: Code Review
Expected severity: Required
Expected signal: Code Review blocks on inflated score with Critical findings
Evidence path: src/query_builder.py — docstrings
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No
