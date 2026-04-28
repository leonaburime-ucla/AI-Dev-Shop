Seeds targeting: resource bounds, idempotency, I/O shape, explicit dependencies, observability, complexity/scale, concurrency safety, test anti-patterns, handoff/reporting

```
ID: SEED-2A
Category: I/O shape / N+1
Seeded issue: The starter code calls userService.getUser() inside a for loop for every single notification — classic N+1. Should batch-resolve users.
Expected owner: Programmer
Expected severity: High
Expected signal: Programmer flags per-item I/O and batches
Evidence path: src/processor.py — process_batch loop
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-2B
Category: Resource bounds
Seeded issue: No pagination/chunking despite brief requiring chunks of 50. The starter processes all items in one pass. No max batch size enforcement.
Expected owner: Programmer
Expected severity: High
Expected signal: Programmer adds chunking and max batch guard
Evidence path: src/processor.py — no chunking logic
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-2C
Category: Idempotency
Seeded issue: Retry logic resends the email without any idempotency key. If the email provider times out but actually sent the email, retrying duplicates the send.
Expected owner: Programmer
Expected severity: Critical
Expected signal: Programmer adds idempotency key to email send
Evidence path: src/processor.py — retry loop
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-2D
Category: Explicit dependencies
Seeded issue: The processor reads Date.now() directly for elapsed time calculation and uses Math.random() for jitter in retry backoff. Not injectable, not testable.
Expected owner: Programmer
Expected severity: Medium
Expected signal: Programmer injects clock and random source
Evidence path: src/processor.py — time.time() calls
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-2E
Category: Concurrency safety
Seeded issue: The deduplication Set is populated during processing, not before. In an async scenario, parallel chunk processing could miss deduplication window.
Expected owner: Programmer (or Code Review)
Expected severity: Medium
Expected signal: Dedup should happen before processing begins
Evidence path: src/processor.py — seen set inside the loop
Caught by Programmer:
Caught by Code Review:
False positive risk: Medium (depends on async model)
Framework change needed: No

ID: SEED-2F
Category: Observability for effects
Seeded issue: No logging, metrics, or traces on any of the external calls (user lookup, template render, email send). Silent failure/success.
Expected owner: Programmer
Expected severity: Medium
Expected signal: Programmer adds observability at effect boundaries
Evidence path: src/processor.py — no log/metric/trace calls
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-2G
Category: Typed/stable result
Seeded issue: The function returns a plain object with inconsistent shape — sometimes has `error` string, sometimes has `results` array, sometimes has both. Return type is `any`.
Expected owner: Programmer
Expected severity: Medium
Expected signal: Programmer should define a typed result
Evidence path: src/processor.py — return statements
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-2H
Category: Test anti-patterns
Seeded issue: Tests use real setTimeout via retry logic (sleeps in tests), and mock the email service with a shared mutable counter that leaks between tests.
Expected owner: Code Review
Expected severity: High
Expected signal: Sleeps in tests, shared mutable mock state
Evidence path: tests/test_processor.py
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No
```
