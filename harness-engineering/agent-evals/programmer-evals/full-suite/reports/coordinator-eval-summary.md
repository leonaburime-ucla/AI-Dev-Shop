# Coordinator Eval Summary — Full Agent Eval Suite

**Eval ID**: full-suite
**Date**: 2026-04-26
**Agents Tested**: Programmer v1.4.1, Code Review v1.1.1
**Total Seeds**: 42 across 5 mini-projects
**Eval Protocol**: `harness-engineering/quality/function-quality-seeded-evals.md`

---

## Executive Summary

| Metric | Programmer | Code Review | Combined Pipeline |
|--------|-----------|-------------|-------------------|
| Seeds fully caught | 35/42 (83%) | Backstopped 6 misses | 41/42 (98%) |
| Seeds partially caught | 4/42 | Deepened 4 partials | — |
| Seeds missed | 3/42 | Caught 3/3 missed | **1/42 (2%)** |
| False positives | 0 | 0 | 0 |
| Added findings beyond seeds | — | 19 additional | 19 |

**One seed not fully caught by either agent**: SEED-1A (duplicate SKU aggregation). Code Review flagged it as Recommended missing test but did not classify it as Required or identify it as a correctness bug. Both agents treated per-line-item bulk discount as a defensible design choice rather than a spec violation.

---

## Per-Eval Results

### Eval 1: Discount Rule Engine (9 seeds)

| Seed ID | Category | Programmer | Code Review | Combined |
|---------|----------|-----------|-------------|----------|
| SEED-1A | Adversarial aggregate (duplicate SKUs) | MISSED | Partial (Recommended missing test) | **PARTIAL** |
| SEED-1B | Hidden branching (switch fallthrough) | Caught (Critical) | Confirmed + found new outer-loop break issue | Caught |
| SEED-1C | Extension point (hardcoded switch) | Caught | Confirmed | Caught |
| SEED-1D | Score inflation (all 100/100) | Caught | Confirmed, noted 2-4pt remaining inflation | Caught |
| SEED-1E | Predictable errors (mixed throw/return) | Caught (Critical) | Confirmed | Caught |
| SEED-1F | Stable boundaries (positional args) | Caught | Confirmed | Caught |
| SEED-1G | Single responsibility (CC~8 monolith) | Caught | Confirmed | Caught |
| SEED-1H | Pure logic vs effects (console.log) | Caught | Confirmed clean | Caught |
| SEED-1I | Test anti-patterns (shared state, weak assertions) | Caught | Confirmed + found 3 more missing tests | Caught |

**Programmer**: 8/9 | **Code Review**: backstopped 0 misses fully, 1 partial | **Combined**: 8.5/9

---

### Eval 2: Batch Email Processor (8 seeds)

| Seed ID | Category | Programmer | Code Review | Combined |
|---------|----------|-----------|-------------|----------|
| SEED-2A | I/O shape (N+1 user lookups) | MISSED | **Caught** (R-03, Required) | Caught |
| SEED-2B | Resource bounds (no chunking) | Caught (Critical) | Confirmed | Caught |
| SEED-2C | Idempotency (retry duplicates emails) | MISSED | **Caught** (R-01, Critical) | Caught |
| SEED-2D | Explicit deps (Date.now, Math.random) | Partial (fixed random, missed clock) | **Caught** (R-02, Required) | Caught |
| SEED-2E | Concurrency safety (dedup timing) | Caught | Confirmed | Caught |
| SEED-2F | Observability (no logging) | Caught | Confirmed | Caught |
| SEED-2G | Typed result (any everywhere) | Caught | Confirmed | Caught |
| SEED-2H | Test anti-patterns (shared counter, order dep) | Caught | Confirmed + found real setTimeout in chunking test | Caught |

**Programmer**: 5.5/8 | **Code Review**: backstopped 3 misses | **Combined**: 8/8

---

### Eval 3: Payment Gateway Adapter (8 seeds)

| Seed ID | Category | Programmer | Code Review | Combined |
|---------|----------|-----------|-------------|----------|
| SEED-3A | Security (card token logged) | Caught (Critical PCI) | Confirmed + suggested error-path test | Caught |
| SEED-3B | Typed result (raw SDK errors escape) | Caught | Confirmed | Caught |
| SEED-3C | Resource bounds (no timeout) | Caught | Confirmed + noted non-cancellation | Caught |
| SEED-3D | Explicit deps (hardcoded Date/console) | Caught | Confirmed | Caught |
| SEED-3E | Pure logic (error mapping in catch) | Caught | Confirmed clean extraction | Caught |
| SEED-3F | Handoff reporting (missing docs) | Caught | Confirmed thorough handoff | Caught |
| SEED-3G | Test anti-patterns (global mocks) | Caught | Confirmed clean rewrite | Caught |
| SEED-3H | Observability (only charge logged) | Caught | Confirmed all 3 methods logged | Caught |

**Programmer**: 8/8 | **Code Review**: 0 misses to backstop | **Combined**: 8/8

---

### Eval 4: Rate Limiter Cache (8 seeds)

| Seed ID | Category | Programmer | Code Review | Combined |
|---------|----------|-----------|-------------|----------|
| SEED-4A | Concurrency safety (Map race) | Partial (fixed mutation, didn't document assumption) | **Caught** (F4, document single-threaded) | Caught |
| SEED-4B | Determinism (Date.now not injectable) | Caught | Confirmed | Caught |
| SEED-4C | Resource bounds (unbounded memory) | Partial (per-client cleanup, no max entries) | **Caught** (F2, no eviction for stale clients) | Caught |
| SEED-4D | Complexity (O(n*m) global cleanup) | Caught | Confirmed | Caught |
| SEED-4E | Stable contract (missing resetAt) | Caught | Confirmed | Caught |
| SEED-4F | Score inflation (all 100/100) | Caught | Deepened (uniform 95 flattens signal) | Caught |
| SEED-4G | Test anti-patterns (setTimeout, timezone) | Caught | Confirmed + noted one minor real-clock test | Caught |
| SEED-4H | Documentation noise (over-documented helpers) | Partial | **Caught** (F3, reset one-liner shouldn't have score) | Caught |

**Programmer**: 5/8 fully + 3 partial | **Code Review**: backstopped all 3 partials | **Combined**: 8/8

---

### Eval 5: Secure Search Query Builder (9 seeds)

| Seed ID | Category | Programmer | Code Review | Combined |
|---------|----------|-----------|-------------|----------|
| SEED-5A | Security (SQL injection via ORDER BY) | Caught (Critical) | Confirmed all 10 vectors safe | Caught |
| SEED-5B | Security (PII logging) | Caught (Critical) | Confirmed metadata-only logging | Caught |
| SEED-5C | Resource bounds (no pageSize validation) | Caught | Confirmed | Caught |
| SEED-5D | Predictable errors (silent defaults) | Caught | Confirmed | Caught |
| SEED-5E | Typed result (any return) | Caught | Confirmed | Caught |
| SEED-5F | Stable boundaries (positional args) | Caught | Confirmed | Caught |
| SEED-5G | Single responsibility (monolithic function) | Caught | Confirmed | Caught |
| SEED-5H | Adversarial tests (missing boundary tests) | Caught (46 tests, 7 injection) | Confirmed + found LIKE char escaping gap | Caught |
| SEED-5I | Score inflation (100 with Critical bugs) | Caught | Confirmed scores credible | Caught |

**Programmer**: 9/9 | **Code Review**: 0 misses to backstop | **Combined**: 9/9

---

## Skill & Guard Coverage Matrix

| Skill / Guard | Seeds Testing It | Programmer Catch Rate | CR Backstop Rate |
|---------------|-----------------|----------------------|-----------------|
| Coding Foundations (explicit deps) | 2A, 2D, 3D, 4B | 3/4 (75%) | 4/4 (100%) |
| Coding Foundations (pure logic vs effects) | 1H, 3E | 2/2 (100%) | — |
| Coding Foundations (stable contracts) | 1F, 3B, 4E, 5E, 5F | 5/5 (100%) | — |
| Coding Foundations (predictable errors) | 1E, 5D | 2/2 (100%) | — |
| Coding Foundations (single responsibility) | 1G, 5G | 2/2 (100%) | — |
| Implementation Guardrails (complexity/scale) | 4D | 1/1 (100%) | — |
| Implementation Guardrails (I/O shape) | 2A | 0/1 (0%) | 1/1 (100%) |
| Implementation Guardrails (resource bounds) | 2B, 3C, 4C, 5C | 3/4 (75%) | 4/4 (100%) |
| Testable Design Patterns (two-object sig) | 1F, 5F | 2/2 (100%) | — |
| Testable Design Patterns (test anti-patterns) | 1I, 2H, 3G, 4G | 4/4 (100%) | — |
| Function Quality Assessment (score inflation) | 1D, 4F, 5I | 3/3 (100%) | — |
| Function Quality Assessment (skepticism pass) | 1D, 4F, 5I | 3/3 (100%) | — |
| Function Quality Assessment (handoff table) | 3F | 1/1 (100%) | — |
| Security/Privacy (PII/secrets logging) | 3A, 5B | 2/2 (100%) | — |
| Security/Privacy (SQL injection) | 5A | 1/1 (100%) | — |
| Adversarial aggregate behavior | 1A, 5H | 1/2 (50%) | 1.5/2 (75%) |
| Idempotency | 2C | 0/1 (0%) | 1/1 (100%) |
| Concurrency safety | 4A | 0.5/1 (50%) | 1/1 (100%) |
| Determinism | 4B, 2D | 1.5/2 (75%) | 2/2 (100%) |
| Observability for effects | 2F, 3H | 2/2 (100%) | — |
| Extension points | 1C | 1/1 (100%) | — |
| Hidden branching | 1B | 1/1 (100%) | — |
| Documentation noise | 4H | 0.5/1 (50%) | 1/1 (100%) |

---

## Programmer Agent — Strengths

1. **Security-critical issues**: Near-perfect. SQL injection, PII logging, card token exposure — all caught immediately and classified as Critical.
2. **Score inflation awareness**: Every eval that had fake 100/100 scores was caught and corrected with genuine skepticism passes.
3. **Test anti-pattern detection**: Shared mutable state, order-dependent tests, weak assertions, real-time dependencies — always caught and rewritten from scratch.
4. **Typed contracts**: Every `any` type was replaced. Two-object parameter convention applied consistently.
5. **Pure logic separation**: Console.log in business logic removed in every case.
6. **Extension points**: Hardcoded switches converted to strategy patterns.

## Programmer Agent — Weaknesses

1. **Idempotency awareness**: Missed entirely in Eval 2. The Programmer did not consider "what happens if the provider received the email but the ack was lost." This is a production-critical concern for any retry-capable system.
2. **N+1 I/O batching**: Missed in Eval 2. The Programmer optimized chunking (parallel within chunk) but didn't think about batching user lookups across items.
3. **Aggregate/cross-item behavior**: Missed the duplicate-SKU aggregation in Eval 1. The bulkDiscount function checks per-line-item, but the spec says "10+ of same SKU" which implies cross-line aggregation. The Programmer treated the existing per-line logic as correct without questioning it.
4. **Memory bound caps**: Partially missed in Eval 4. Fixed the immediate O(n*m) problem but didn't add a max-entries eviction policy for the Map.
5. **Concurrency documentation**: Tends to fix the immediate code issue but doesn't document threading/concurrency assumptions.

## Code Review Agent — Strengths

1. **Backstop reliability**: Caught all 3 Programmer misses (idempotency, N+1, Date.now clock) and all 3 partial catches (memory cap, concurrency docs, over-documentation).
2. **Score recalibration**: Independently re-scored functions and caught remaining inflation (mapErrorCode at 100 should be 95, processOne at 95 should be 78).
3. **Test gap identification**: Found missing test cases beyond the seed ledger in every eval.
4. **Non-functional awareness**: Consistently flagged timeout behavior, memory growth, and scale concerns.
5. **Finding classification discipline**: Clear Required vs Recommended separation with actionable fix suggestions.

## Code Review Agent — Weaknesses

1. **Aggregate behavior severity**: Classified the duplicate-SKU gap (SEED-1A) as Recommended rather than Required. The spec says "10+ of same SKU" which arguably means aggregate quantity, making this a spec alignment issue that should block.
2. **No new Critical-severity discoveries**: All Critical findings originated from the Programmer agent's brownfield fixes. Code Review confirmed but didn't independently discover new Critical issues in the Programmer's code.

---

## Guard Promotion Recommendations

Based on the eval results (promote only when the same miss repeats across 2+ evals or is Critical enough for one occurrence):

### Promote to Programmer Blocker

1. **Idempotency check for retry-capable I/O**: The Programmer must identify and document idempotency strategy (key, dedup, or at-most-once) before implementing any retry loop over external writes. Missed once (Eval 2), Critical severity.
   - *Rationale*: One occurrence but Critical severity (duplicate emails/charges in production). Justifies a blocker.

2. **N+1 I/O pre-check for batch workflows**: Before implementing a batch processor, the Programmer must identify per-item I/O calls and propose batching. Currently only the complexity/scale pre-check exists; it should explicitly call out per-item external calls.
   - *Rationale*: Missed once (Eval 2), but the implementation-guardrails skill already covers this conceptually. Needs sharper wording.

### Promote to Code Review Required

1. **Aggregate/cross-item behavior as Required when spec implies aggregation**: When the spec uses language like "10+ of same X" or "combined total," Code Review should classify missing aggregate tests as Required (spec misalignment), not Recommended.
   - *Rationale*: The one partially-missed seed (SEED-1A) across the entire suite was because Code Review treated it as a test recommendation rather than a spec alignment issue.

### Keep as Checklist (No Promotion Needed)

- Score inflation detection: Working perfectly at both agent levels.
- Test anti-pattern detection: Working perfectly.
- Security/PII/injection detection: Working perfectly.
- Memory bounds: Partially caught by Programmer, fully caught by Code Review. Current two-agent backstop is sufficient.
- Concurrency documentation: Partially caught by Programmer, fully caught by Code Review. Current backstop is sufficient.
- Over-documentation noise: Low severity, current Recommended classification is appropriate.

---

## False Positive Analysis

**Zero false positives across all 42 seeds and 10 agent runs.** Neither agent invented problems that weren't supported by evidence. Code Review's 19 additional findings (beyond seeds) were all legitimate improvements:
- 6 missing test cases
- 4 test quality improvements
- 3 documentation/comment fixes
- 3 non-functional observations
- 2 score recalibrations
- 1 code quality improvement

---

## Comparison to Previous Mini-Eval

The previous mini-eval (function-quality-mini-2026-04-26) found:
- Programmer scored everything 100/100 (score inflation) — **Fixed: Programmer now self-corrects inflated scores in all 5 evals**
- Code Review caught a real bug tests missed (aggregate inventory) — **Replicated: Code Review caught idempotency, N+1, and Date.now that Programmer missed**
- No adversarial aggregate tests — **Improved: Programmer added adversarial tests in 4/5 evals, missed aggregate SKU aggregation in 1**

The seeded-eval protocol is working. The agents are substantially more rigorous than the mini-eval suggested, but the protocol successfully identified the remaining gaps (idempotency, N+1, aggregate severity classification).

---

## Next Steps

1. Apply the 3 guard promotion recommendations above to `agents/programmer/skills.md` and `agents/code-review/skills.md`.
2. Re-run Eval 2 after the idempotency guard promotion to verify the fix.
3. Consider adding a "premature abstraction / over-engineering" seed category per Gemini's earlier feedback — none of the current seeds test for this.
4. Consider splitting the checklist per Gemini's suggestion: the 24-item checklist worked well but could benefit from grouping into 5-6 categories for faster scanning.
