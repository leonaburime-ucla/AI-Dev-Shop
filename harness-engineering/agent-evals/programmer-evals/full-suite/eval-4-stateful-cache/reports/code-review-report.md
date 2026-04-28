# Code Review Report — Rate Limiter (Sliding Window)

**Reviewer**: Code Review Agent v1.1.1
**Date**: 2026-04-26
**Spec**: project-brief.md (Rate Limiter with Sliding Window Cache)
**Files Reviewed**: `project/src/rate-limiter.ts`, `project/src/__tests__/rate-limiter.test.ts`

---

## Verdict: PASS WITH FINDINGS

The implementation is solid, well-tested, and meets the vast majority of spec requirements. Three findings need attention before shipping -- one is a spec deviation, one is a design gap flagged in the brief, and one is a documentation concern.

---

## Findings

### F1 — Missing Default Values for windowMs and maxRequests [SPEC DEVIATION] [MUST FIX]

**Spec says**: "configurable duration (default 60 seconds)" and "configurable max requests per window (default 100)."

**Implementation**: Both `windowMs` and `maxRequests` are required fields in `RateLimiterInput`. There are no defaults. A caller must always provide both values.

**Impact**: This violates requirements 1 and 2. The spec explicitly states defaults of 60 seconds and 100 requests. The interface should make both fields optional and fall back to `windowMs = 60_000` and `maxRequests = 100` when omitted.

**Suggested fix**: Make the fields optional in `RateLimiterInput` and apply defaults inside `createRateLimiter`:

```ts
export interface RateLimiterInput {
  windowMs?: number;
  maxRequests?: number;
}

// Inside createRateLimiter:
const windowMs = input.windowMs ?? 60_000;
const maxRequests = input.maxRequests ?? 100;
```

Add a test confirming `createRateLimiter({})` works with expected defaults.

---

### F2 — No Max-Entries Cap or Periodic Cleanup for Unbounded Client Growth [DESIGN GAP] [SHOULD FIX]

**Spec says** (requirement 5): "Expired entries outside the window must be cleaned up to prevent memory growth."

**Implementation**: Cleanup is lazy -- per-client pruning happens on access (`checkLimit`, `recordRequest`), and `getStats` prunes all clients. However, if a client sends one request and is never queried again, that client's entry persists in the `windows` Map indefinitely until `getStats` is called.

More critically, there is no cap on the total number of distinct client IDs in the map. An attacker (or a system with rotating client IDs like IP-based limiting behind a CDN) could create millions of map entries that are never pruned because no one calls `checkLimit` or `getStats` for those stale clients.

**Recommendation**: Add one or both of:
1. A `maxClients` configuration option that evicts the oldest-accessed client when the cap is reached.
2. A periodic or threshold-triggered full-map sweep (e.g., run the `getStats`-style prune every N operations).

The Programmer's handoff correctly replaced the old global O(n*m) cleanup-on-every-check with per-client pruning, which is the right call for hot-path performance. But the spec's "prevent memory growth" language implies some mechanism for stale client eviction beyond lazy access-triggered cleanup. At minimum, document the assumption that the caller is responsible for periodic `getStats` calls or external eviction.

---

### F3 — Over-Documentation on Trivial Functions [STYLE] [OPTIONAL]

The `reset` function is a single `windows.delete(clientId)` call. It carries:
- A JSDoc block with `@param`, `@complexity O(1)`, and `@overallScore 95/100`

A one-liner map deletion does not warrant a complexity annotation or a quality score. The `@overallScore 95/100` on a trivial delegating call is noise -- it is neither informative nor actionable. The same applies to `checkLimit` which is a thin wrapper around `pruneClient` plus arithmetic.

**Recommendation**: Reserve `@complexity` and `@overallScore` annotations for functions with non-obvious algorithmic behavior. `pruneClient` and `getStats` warrant them; `reset` does not.

---

### F4 — Concurrency Model Not Documented [MINOR] [SHOULD DOCUMENT]

The implementation assumes single-threaded execution. The `pruneClient` function reads, slices, and writes back to the Map in multiple steps. In a concurrent environment (e.g., if this were used in a worker-threads or SharedArrayBuffer context), this would be a race condition.

Node.js is single-threaded by default, so this is safe in typical use. However, the module-level JSDoc should state this assumption explicitly, since rate limiters are commonly used in server contexts where concurrency questions arise.

**Suggested addition to the module docblock**:

```ts
/**
 * ...
 * Assumes single-threaded execution (standard Node.js event loop).
 * Not safe for use across worker threads without external synchronization.
 */
```

---

### F5 — `pruneClient` Comment Says "Binary-Scan" but Performs Linear Scan [NITPICK]

Line 79: `// Timestamps are in insertion order (ascending), so we can binary-scan`

The code then does a `while` loop incrementing `firstValid` one step at a time. This is a linear scan, not a binary scan. The comment is misleading. Either fix the comment to say "linear scan" or implement an actual binary search (which would be an improvement for clients with very large timestamp arrays, but is likely unnecessary for typical workloads).

---

## Dimension Assessments

### 1. Spec Alignment — 7/10

Six of seven requirements are fully met. Requirement items 1 and 2 are partially met -- the configurability is there, but the specified default values (60s and 100) are missing. The `checkLimit` return type, `recordRequest` behavior, `reset`, and `getStats` all conform to the spec.

### 2. Architecture Adherence — 10/10

Factory pattern with two-object signature. Injectable clock via `options.now`. Typed exports for all interfaces. Clean separation between construction and usage. No classes, no singletons, no global state.

### 3. Test Quality — 9/10

21 deterministic tests with zero real-time dependencies. Good coverage of input validation, boundary conditions (exact windowMs expiry), edge cases (maxRequests=1, 50 independent clients), and the rejected-request-no-record behavior. Deduction: no test for default values (because they do not exist -- see F1). The test "works without options object (uses real clock)" is slightly non-deterministic since it uses the real clock, but the assertions are loose enough that it will not flake.

### 4. Code Quality and Maintainability — 9/10

Clean, readable implementation. Single clock call per operation. Per-client pruning avoids the original O(n*m) global scan. Slice-based expiry is simple and correct. Type exports enable downstream consumers. Minor deduction for the misleading "binary-scan" comment.

### 5. Non-Functional Characteristics — 7/10

Per-client operations are O(k) which is correct. However, unbounded client-count growth (F2) is a real concern for production deployments. No cap, no eviction, no periodic sweep. The lazy pruning model means stale clients persist until explicitly touched.

### 6. Function Quality Assessment — 8/10

Scores are uniform 95/100 across all functions regardless of complexity, which flattens the signal. A one-line `reset` and a multi-branching `pruneClient` should not carry the same score. The Programmer's score-skepticism pass noted this as intentional, but the reasoning ("per-access O(k) pruning is a known trade-off") applies to `pruneClient`, not to `reset`. Deduction for over-annotation on trivial helpers.

---

## Summary Table

| ID | Severity | Category | Description |
|----|----------|----------|-------------|
| F1 | MUST FIX | Spec Deviation | Missing default values for windowMs (60s) and maxRequests (100) |
| F2 | SHOULD FIX | Design Gap | No cap on client count; stale clients never evicted without explicit access |
| F3 | OPTIONAL | Style | Over-documentation on trivial one-liner functions |
| F4 | SHOULD DOCUMENT | Minor | Single-threaded assumption not stated in module docs |
| F5 | NITPICK | Comment | "binary-scan" comment describes a linear scan |

---

## Recommendation

Return to Programmer for F1 (spec defaults) and F2 (document or mitigate unbounded client growth). F3-F5 can be addressed in the same pass or deferred.
