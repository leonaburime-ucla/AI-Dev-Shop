# Coordinator Eval Summary — Checklist Suite

**Eval ID**: checklist-suite
**Date**: 2026-04-26
**Agents Tested**: Programmer v1.4.1, Code Review v1.1.1
**Total Seeds**: 32 across 4 mini-projects (8 per eval)
**Eval Protocol**: `harness-engineering/quality/function-quality-seeded-evals.md`
**Target**: Function Quality Assessment Checklist items 1-24 (one seed per item) + 8 trick seeds

---

## Executive Summary

| Metric | Programmer | Code Review | Combined Pipeline |
|--------|-----------|-------------|-------------------|
| Seeds fully caught | 29/32 (90.6%) | Backstopped 0.5 | 29.5/32 (92.2%) |
| Seeds partially caught | 1/32 | Deepened 0 partials | 1/32 |
| Seeds missed | 2/32 | Caught 0.5/2 | **1.5/32 (4.7%)** |
| False positives | 0 | 0 | 0 |
| Additional findings beyond seeds | — | 15 | 15 |

**Seeds not fully caught by either agent**:
- **SEED-CL-TRICK-02** (Misleading variable name): Programmer tested capacity scenarios but didn't question the `remainingCapacity` name/value mismatch. Code Review didn't flag it either — focused on a different spec gap (priority not influencing assignment).
- **SEED-CL-14** (Resource bounds — max roles/timeout): Programmer batched N+1 calls but didn't add max role limits or service timeout. Code Review caught unbounded cache (CR-006) which is adjacent but not the same concern. **Partial credit.**

---

## Per-Eval Results

### Eval 6: Task Scheduler (CL 1-6 + 2 tricks)

| Seed ID | Checklist Item | Programmer | Code Review | Combined |
|---------|---------------|-----------|-------------|----------|
| CL-01 | 1. Purpose clarity | CAUGHT — extracted focused functions | Confirmed | Caught |
| CL-02 | 2. Explicit inputs | CAUGHT — eliminated CONFIG, per-call opts | Confirmed | Caught |
| CL-03 | 3. Two-object args | CAUGHT — refactored to (input, opts?) | Confirmed | Caught |
| CL-04 | 4. Typed contract | CAUGHT — ScheduleResult union | Confirmed | Caught |
| CL-05 | 5. Pure-by-default | CAUGHT — removed side effects, injected clock | Confirmed | Caught |
| CL-06 | 6. Effect boundary | CAUGHT — removed webhook from scorer | Confirmed | Caught |
| TRICK-01 | Missing await | CAUGHT — added await | Confirmed | Caught |
| TRICK-02 | Misleading variable name | **PARTIAL** — tested capacity but not the name mismatch | Not caught (different finding) | **PARTIAL** |

**Programmer**: 7.5/8 | **Code Review backstop**: 0 | **Combined**: 7.5/8

**Code Review additional findings**: 1 Required (priority score not used in assignment — legitimate spec gap beyond seeds), 7 Recommended.

---

### Eval 7: Data Pipeline (CL 7-12 + 2 tricks)

| Seed ID | Checklist Item | Programmer | Code Review | Combined |
|---------|---------------|-----------|-------------|----------|
| CL-07 | 7. Single responsibility | CAUGHT — extracted 6 helpers from 90-line monolith | Confirmed | Caught |
| CL-08 | 8. Small testable unit | CAUGHT — 57 tests, 10 describe blocks | Confirmed | Caught |
| CL-09 | 9. Test anti-patterns | CAUGHT — deleted weak tests, rewrote from scratch | Confirmed | Caught |
| CL-10 | 10. Predictable errors | CAUGHT — unified to invalid[] array | Confirmed | Caught |
| CL-11 | 11. Hidden state/branching | CAUGHT — removed env read + lastRunTimestamp | Confirmed | Caught |
| CL-12 | 12. Complexity/scale | CAUGHT — O(n^2) → Set-based O(1) | Confirmed | Caught |
| TRICK-03 | Mutation trap | CAUGHT — removed sort(), shallow spread, shared ref | Confirmed | Caught |
| TRICK-04 | Dead code | CAUGHT — integrated dead function into pipeline | Confirmed | Caught |

**Programmer**: 8/8 | **Code Review backstop**: 0 needed | **Combined**: 8/8

**Code Review additional findings**: 0 Required, 9 Recommended (phone optionality, scope creep dedup, string coupling, etc.).

---

### Eval 8: Access Control (CL 13-18 + 2 tricks)

| Seed ID | Checklist Item | Programmer | Code Review | Combined |
|---------|---------------|-----------|-------------|----------|
| CL-13 | 13. I/O shape (N+1) | CAUGHT — batched to getRoles() | Confirmed | Caught |
| CL-14 | 14. Resource bounds | **MISSED** — no max roles, no timeout | Partial (CR-006: unbounded cache) | **PARTIAL** |
| CL-15 | 15. Idempotency | CAUGHT — Set dedup + NO_OP audit | Confirmed | Caught |
| CL-16 | 16. Concurrency/cache | CAUGHT — instance-scoped + invalidation | Confirmed | Caught |
| CL-17 | 17. Determinism | CAUGHT — injectable Clock | Confirmed | Caught |
| CL-18 | 18. Observability | CAUGHT — removed noisy reads, added audit | Confirmed | Caught |
| TRICK-05 | && vs \|\| bug | CAUGHT — unified wildcard logic | Partial (CR-002: no regression test) | Caught |
| TRICK-06 | splice(-1,1) | CAUGHT — switched to Set.delete() | Confirmed | Caught |

**Programmer**: 7/8 | **Code Review backstop**: 0.5 (partial on CL-14) | **Combined**: 7.5/8

**Code Review additional findings**: 0 Required, 7 Recommended (broken test, partial wildcard regression, cache key collision, audit ordering, etc.).

---

### Eval 9: Report Generator (CL 19-24 + 2 tricks)

| Seed ID | Checklist Item | Programmer | Code Review | Combined |
|---------|---------------|-----------|-------------|----------|
| CL-19 | 19. Security/PII | CAUGHT — removed debug field (Critical) | Confirmed | Caught |
| CL-20 | 20. Extension point | CAUGHT — format map replaces 3 switches | Confirmed | Caught |
| CL-21 | 21. Refactor signal | CAUGHT — extracted 5 helpers, CC 8→3 | Confirmed | Caught |
| CL-22 | 22. Adversarial aggregate | CAUGHT — dedup, sum not max, per-region rounding | Confirmed | Caught |
| CL-23 | 23. Coverage evidence | CAUGHT — 4→35 tests, real 98.5% | Confirmed | Caught |
| CL-24 | 24. Score calibration | CAUGHT — honest scores with skepticism pass | Deepened (roundTwo 100→92) | Caught |
| TRICK-07 | Premature abstraction | CAUGHT — removed class hierarchy | Confirmed | Caught |
| TRICK-08 | Floating point drift | CAUGHT — per-step rounding | Deepened (CR-001: negative midpoint) | Caught |

**Programmer**: 8/8 | **Code Review backstop**: 0 needed + 2 new Required findings | **Combined**: 8/8

**Code Review additional findings**: 2 Required (negative midpoint rounding bug, dead normalizeRegion — both legitimate beyond-seed discoveries), 4 Recommended.

---

## Per-Checklist-Item Coverage Map

| # | Checklist Item | Eval | Programmer | CR Backstop | Combined | Notes |
|---|---------------|------|-----------|-------------|----------|-------|
| 1 | Purpose clarity | 6 | CAUGHT | — | CAUGHT | |
| 2 | Explicit inputs/outputs | 6 | CAUGHT | — | CAUGHT | |
| 3 | Two-object args | 6 | CAUGHT | — | CAUGHT | |
| 4 | Typed contract | 6 | CAUGHT | — | CAUGHT | |
| 5 | Pure-by-default | 6 | CAUGHT | — | CAUGHT | |
| 6 | Effect boundary | 6 | CAUGHT | — | CAUGHT | |
| 7 | Single responsibility | 7 | CAUGHT | — | CAUGHT | |
| 8 | Small testable unit | 7 | CAUGHT | — | CAUGHT | |
| 9 | Test anti-patterns | 7 | CAUGHT | — | CAUGHT | |
| 10 | Predictable errors | 7 | CAUGHT | — | CAUGHT | |
| 11 | Hidden state/branching | 7 | CAUGHT | — | CAUGHT | |
| 12 | Complexity/scale | 7 | CAUGHT | — | CAUGHT | |
| 13 | I/O shape (N+1) | 8 | CAUGHT | — | CAUGHT | |
| 14 | Resource bounds | 8 | **MISSED** | Partial (cache) | **PARTIAL** | No max roles, no timeout |
| 15 | Idempotency | 8 | CAUGHT | — | CAUGHT | Improved from Phase 1 miss |
| 16 | Concurrency safety | 8 | CAUGHT | — | CAUGHT | |
| 17 | Determinism | 8 | CAUGHT | — | CAUGHT | |
| 18 | Observability | 8 | CAUGHT | — | CAUGHT | |
| 19 | Security/privacy | 9 | CAUGHT | — | CAUGHT | |
| 20 | Extension point | 9 | CAUGHT | — | CAUGHT | |
| 21 | Refactor signal | 9 | CAUGHT | — | CAUGHT | |
| 22 | Adversarial aggregate | 9 | CAUGHT | — | CAUGHT | |
| 23 | Coverage evidence | 9 | CAUGHT | — | CAUGHT | |
| 24 | Score calibration | 9 | CAUGHT | Deepened | CAUGHT | |

**Checklist coverage: 23/24 fully caught, 1/24 partial (resource bounds)**

---

## Trick Seed Coverage

| # | Trick | Eval | Programmer | CR Backstop | Combined |
|---|-------|------|-----------|-------------|----------|
| 1 | Missing await | 6 | CAUGHT | — | CAUGHT |
| 2 | Misleading variable name | 6 | PARTIAL | Not caught | **PARTIAL** |
| 3 | Mutation trap (sort + shallow spread) | 7 | CAUGHT | — | CAUGHT |
| 4 | Dead code inflating coverage | 7 | CAUGHT | — | CAUGHT |
| 5 | Copy-paste && vs \|\| bug | 8 | CAUGHT | — | CAUGHT |
| 6 | splice(-1,1) off-by-one | 8 | CAUGHT | — | CAUGHT |
| 7 | Premature abstraction | 9 | CAUGHT | — | CAUGHT |
| 8 | Floating point accumulation | 9 | CAUGHT | Deepened | CAUGHT |

**Trick coverage: 7/8 caught, 1/8 partial (misleading variable name)**

---

## Programmer Agent — Strengths (Checklist Suite)

1. **Foundational coding skills (CL 1-6)**: Near-perfect. Purpose clarity, explicit deps, two-object args, typed contracts, purity, effect boundaries — all caught immediately and classified correctly.
2. **Code structure skills (CL 7-12)**: Perfect. SRP extraction, testable units, test anti-pattern rewrites, error normalization, hidden state removal, complexity refactoring — all caught.
3. **Security awareness (CL 19)**: PII leak caught and removed immediately as Critical.
4. **Aggregate behavior (CL 22)**: Duplicate dedup, wrong aggregation (max vs sum), per-region rounding — all caught. Significant improvement over Phase 1 where aggregate behavior was the weakest area.
5. **Trick detection (7/8)**: Missing await, mutation traps, dead code, copy-paste bugs, off-by-one, premature abstraction, floating point — all caught naturally.
6. **Idempotency (CL 15)**: CAUGHT — a notable improvement from Phase 1 where idempotency was missed entirely.

## Programmer Agent — Weaknesses (Checklist Suite)

1. **Resource bounds (CL-14)**: Missed again. The Programmer batched N+1 calls (CL-13) but didn't add max role limits or service call timeouts. This is a repeat weakness from Phase 1 (partial catch on memory bounds in Eval 4). The Programmer fixes the immediate O(n) problem but doesn't think about what happens when n is adversarially large.
2. **Misleading names (TRICK-02)**: Partial. The Programmer tested the capacity logic but didn't question whether `remainingCapacity` accurately describes what it computes. This suggests the Programmer trusts variable names and focuses on behavior rather than name/value consistency.

## Code Review Agent — Strengths (Checklist Suite)

1. **Independent discovery**: Found 2 genuine Required bugs in Eval 9 (negative midpoint rounding, dead normalizeRegion) that were beyond the seed scope. These are real production bugs.
2. **Score recalibration**: Independently re-scored functions in every eval, catching small inflation consistently (roundTwo 100→92, computeRevenueByRegion 100→93).
3. **Test gap identification**: Found missing regression tests for partial wildcards, broken test names, and untested code paths in every eval.
4. **Spec interpretation**: Found a genuine spec alignment gap in Eval 6 (priority score not influencing assignment) that wasn't even in the seed ledger.

## Code Review Agent — Weaknesses (Checklist Suite)

1. **Resource bounds blind spot**: Did not catch the max-roles/timeout gap (CL-14). Found unbounded cache (adjacent concern) but not the core issue of unlimited roles causing unbounded service calls.
2. **Variable name auditing**: Did not catch the misleading variable name trick (TRICK-02). This suggests Code Review focuses on behavior correctness and structural issues rather than semantic accuracy of naming.
3. **No new Critical discoveries from Programmer code**: The 2 Required findings in Eval 9 were about code the Programmer wrote (rounding, dead code), not about the Programmer's failure to catch something. Code Review isn't discovering Critical-severity issues that the Programmer introduced — which is good (Programmer doesn't introduce bugs) but means Code Review's backstop value is primarily in spec alignment and edge case depth.

---

## Combined Results: Both Eval Suites

### Phase 1 (full-suite) + Phase 2 (checklist-suite)

| Metric | Phase 1 (42 seeds) | Phase 2 (32 seeds) | Combined (74 seeds) |
|--------|-------------------|-------------------|---------------------|
| Programmer alone | 35.5/42 (84.5%) | 30.5/32 (95.3%) | 66/74 (89.2%) |
| Combined pipeline | 41.5/42 (98.8%) | 31/32 (96.9%) | 72.5/74 (97.9%) |
| False positives | 0 | 0 | 0 |

### Programmer Improvement from Phase 1 to Phase 2

| Area | Phase 1 | Phase 2 | Improved? |
|------|---------|---------|-----------|
| Idempotency | MISSED (0%) | CAUGHT (100%) | Yes |
| N+1 batching | MISSED (0%) | CAUGHT (100%) | Yes |
| Aggregate behavior | 50% | 100% | Yes |
| Resource bounds | Partial (75%) | MISSED (0%) | **No — persistent weakness** |
| Score inflation | 100% | 100% | Maintained |
| Security/PII | 100% | 100% | Maintained |
| Test anti-patterns | 100% | 100% | Maintained |

---

## Guard Promotion Recommendations

### Promote to Programmer Blocker

1. **Resource bounds pre-check for service-backed loops**: Before implementing any function that calls an external service for a user-variable collection (roles, permissions, items), the Programmer MUST identify and document:
   - Maximum collection size (or add a configurable cap)
   - Timeout on external service calls
   - Behavior at the cap (error? truncate? paginate?)

   *Rationale*: Missed in Phase 1 (Eval 4 memory bounds) AND Phase 2 (Eval 8 max roles/timeout). Two occurrences across different contexts = promote to blocker.

### Keep Existing Promotions from Phase 1

2. **Idempotency check for retry-capable I/O**: Already recommended in Phase 1. Phase 2 confirms it's now caught — the promotion worked (or would work if applied).

3. **N+1 I/O pre-check for batch workflows**: Already recommended in Phase 1. Phase 2 confirms it's now caught.

### New Recommendation

4. **Variable name audit in skepticism pass**: When performing the score skepticism pass, the Programmer should verify that each variable's name accurately describes its computed value. This is a lightweight addition to the existing pass.

   *Rationale*: TRICK-02 partial catch. One occurrence, Medium severity, so this stays as Recommended rather than blocker.

---

## Comparison to Phase 1

- Programmer catch rate improved from 84.5% to 95.3% (+10.8 percentage points)
- Phase 2 targeted depth (one seed per checklist item) vs Phase 1 breadth (overlapping categories)
- The ONE persistent weakness across both phases is **resource bounds** — the Programmer consistently fixes the immediate issue but doesn't think about adversarial scale
- Code Review's backstop value is lower in Phase 2 (0.5 saves vs 6 saves in Phase 1), largely because the Programmer caught nearly everything

---

## Next Steps

1. Apply the resource bounds guard promotion to `agents/programmer/skills.md`
2. Add variable name audit to the score skepticism pass documentation
3. Consider adding a "resource bounds" seed to every future eval (since it's the persistent blind spot)
4. The two Code Review Required findings in Eval 9 (negative rounding, dead normalizeRegion) suggest adding "negative boundary arithmetic" and "dead code in pipeline" as future trick seed categories
5. Design the repeatable harness framework (Phase B) based on these results
6. Use results to improve the Programmer agent specifically around resource bounds awareness (Phase C)
