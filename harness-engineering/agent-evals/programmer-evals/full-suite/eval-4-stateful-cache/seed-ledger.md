# Seed Ledger — Eval 4: Rate Limiter Cache

## Seeds

ID: SEED-4A
Category: Concurrency safety
Seeded issue: The cache uses a plain Map. If checkLimit and recordRequest are called concurrently for the same clientId, the timestamps array can have a race condition — one call reads stale length while another pushes.
Expected owner: Code Review (Programmer should note)
Expected severity: Medium
Expected signal: Document concurrency assumption or add guard
Evidence path: project/src/rate-limiter.ts — Map access pattern
Caught by Programmer:
Caught by Code Review:
False positive risk: Medium (single-threaded JS mitigates, but worth documenting)
Framework change needed: No

ID: SEED-4B
Category: Determinism / Hidden dependencies
Seeded issue: The starter code uses `Date.now()` directly instead of an injected clock, despite the brief requiring injectable clock. Tests will be non-deterministic.
Expected owner: Programmer
Expected severity: High
Expected signal: Programmer injects clock
Evidence path: project/src/rate-limiter.ts — Date.now() calls
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-4C
Category: Resource bounds / Memory growth
Seeded issue: The cleanup function only runs when checkLimit is called. If a burst of clients hit the system and never check again, their entries stay in memory forever. No periodic or max-entries cleanup.
Expected owner: Programmer
Expected severity: High
Expected signal: Programmer adds max entries or periodic cleanup
Evidence path: project/src/rate-limiter.ts — cleanup only in checkLimit
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-4D
Category: Complexity and scale
Seeded issue: The cleanup function iterates ALL entries in the map on every checkLimit call — O(n * m) where n is client count and m is timestamps per client. This doesn't scale.
Expected owner: Programmer
Expected severity: High
Expected signal: Programmer should scope cleanup to current client or amortize
Evidence path: project/src/rate-limiter.ts — cleanupExpired
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-4E
Category: Stable boundaries / Typed contract
Seeded issue: checkLimit returns `{ allowed: boolean, remaining: number }` but is missing `resetAt` as specified in the brief. Unstable contract.
Expected owner: Programmer
Expected severity: Medium
Expected signal: Programmer adds missing resetAt field
Evidence path: project/src/rate-limiter.ts — checkLimit return
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-4F
Category: Function scoring
Seeded issue: All functions scored 100/100 despite Date.now() dependency, missing contract field, O(n*m) cleanup, and no memory bounds. No skepticism pass.
Expected owner: Code Review
Expected severity: Required
Expected signal: Code Review flags inflated scores
Evidence path: All JSDoc blocks
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-4G
Category: Test anti-patterns
Seeded issue: Tests use real `Date.now()` with `setTimeout` delays to test the sliding window, making them slow and flaky. One test uses a hardcoded timestamp that only works in a specific timezone.
Expected owner: Code Review
Expected severity: High
Expected signal: Real clock in tests, timezone dependency
Evidence path: project/src/__tests__/rate-limiter.test.ts
Caught by Programmer:
Caught by Code Review:
False positive risk: Low
Framework change needed: No

ID: SEED-4H
Category: Documentation noise
Seeded issue: The tiny `reset` one-liner and `getStats` two-liner both have full @overallScore 100/100 documentation blocks that are longer than the functions themselves. Pure documentation noise.
Expected owner: Code Review (Recommended)
Expected severity: Low/Medium
Expected signal: Over-documentation of trivial helpers
Evidence path: project/src/rate-limiter.ts — reset and getStats JSDoc
Caught by Programmer:
Caught by Code Review:
False positive risk: Medium
Framework change needed: No
