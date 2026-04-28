# Seed Ledger — Eval 3: Payment Gateway Adapter

## Seeds

ID: SEED-3A
Category: Security/privacy
Seeded issue: The starter code logs the full cardToken in the charge operation log line. Card tokens should never appear in logs.
Expected owner: Programmer
Expected severity: Critical
Expected signal: Programmer removes PII/secrets from logs
Evidence path: src/adapter.py — charge_card method log line
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-3B
Category: Typed/stable result
Seeded issue: The adapter catches SDK errors with a broad `catch(e: any)` and returns `{ error: e.message }` — a raw string, not the typed error union specified in the brief.
Expected owner: Programmer
Expected severity: High
Expected signal: Programmer maps to typed error codes
Evidence path: src/adapter.py — except blocks
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-3C
Category: Resource bounds
Seeded issue: No timeout protection exists despite the brief requiring 5-second timeouts. SDK calls can hang indefinitely.
Expected owner: Programmer
Expected severity: High
Expected signal: Programmer adds AbortController or Promise.race timeout
Evidence path: src/adapter.py — no timeout logic
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-3D
Category: Explicit dependencies
Seeded issue: The adapter creates its own `new Date()` for timing and uses `console.log` directly instead of accepting a logger dependency.
Expected owner: Programmer
Expected severity: Medium
Expected signal: Inject logger and clock
Evidence path: src/adapter.py — print() and time.time()
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-3E
Category: Pure logic vs effects
Seeded issue: The error mapping logic (SDK code -> internal code) is embedded inside the catch block with the logging and retry logic, not a separate pure function.
Expected owner: Programmer
Expected severity: Medium
Expected signal: Extract error mapping to pure function
Evidence path: src/adapter.py — except blocks
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-3F
Category: Handoff/reporting
Seeded issue: The starter code has no function-quality table, no coverage metrics, no risk disclosure in any documentation.
Expected owner: Programmer (should include in handoff)
Expected severity: Medium
Expected signal: Programmer handoff should include quality table
Evidence path: All source files (src/*.py) — no handoff documentation
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-3G
Category: Test anti-patterns
Seeded issue: Tests mock the SDK by monkey-patching a global object. The mock doesn't reset between tests. One test asserts on console.log output by spying on the global console.
Expected owner: Code Review
Expected severity: High
Expected signal: Global mocks, no isolation, console spy as assertion
Evidence path: tests/test_adapter.py
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-3H
Category: Observability for effects
Seeded issue: The refund and getTransaction methods have no logging at all — only charge logs anything.
Expected owner: Programmer
Expected severity: Medium
Expected signal: All external calls need observability
Evidence path: src/adapter.py — refund and get_transaction methods
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No
