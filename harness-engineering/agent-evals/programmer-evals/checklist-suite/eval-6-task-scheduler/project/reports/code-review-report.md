# Code Review Report -- Task Scheduler

- **Reviewer**: Code Review Agent v1.1.1
- **Date**: 2026-04-26
- **Spec**: project-brief.md (Task Scheduler)
- **Source**: `src/scheduler.ts` (304 lines)
- **Tests**: `src/__tests__/scheduler.test.ts` (416 lines)

---

## 1. Spec Alignment

The implementation covers the majority of spec requirements. However, there is one material gap and one ambiguity.

```
ID:          CR-001
Severity:    Required
Dimension:   Spec Alignment
File:        src/scheduler.ts:150-164 (assignTask)

Finding:
Spec requirement 3 states: "Assign tasks to users based on priority score
and current workload." The implementation assigns based solely on workload
capacity (activeTasks < maxTasks). The priority score is computed but never
used in the assignment decision. A high-priority task and a low-priority
task receive identical assignment treatment.

Evidence:
assignTask() receives only { taskId, assigneeId } -- it never receives or
inspects the priority score. The assignment logic is a simple capacity
check with no score-based behavior (e.g., preemption, queue ordering,
capacity reservation for high-priority work).

Impact:
The scheduler does not fulfill the "based on priority score" part of
requirement 3. In a real system, high-priority tasks could be left
unassigned while low-priority tasks consume all capacity.

Required Action:
Either (a) incorporate priority score into the assignment decision (e.g.,
reserve capacity slots for critical tasks, or reject low-priority tasks
when capacity is tight), or (b) get explicit spec clarification that
priority score is informational only and not used for assignment gating.

Suggested Next Route:
Spec Agent for clarification, then Programmer Agent for implementation.
```

```
ID:          CR-002
Severity:    Recommended
Dimension:   Spec Alignment
File:        src/scheduler.ts:35-42 (TaskInput)

Finding:
The spec says tasks should be accepted with an assigneeId, implying the
caller picks the assignee. However, requirement 3 says "assign tasks to
users based on priority score and current workload," which implies the
scheduler should make or influence the assignment decision. The current
design accepts a single pre-selected assigneeId and either confirms or
rejects it, but does not select among multiple candidates.

Evidence:
TaskInput.assigneeId is a single string. There is no mechanism for the
scheduler to choose from a pool of available users.

Impact:
If the intended behavior is caller-selects-assignee with scheduler
validating capacity, the current design is adequate. If the scheduler
should pick the best assignee, the design is incomplete.

Required Action:
Clarify with spec owner whether the scheduler should select from a pool
or only validate a caller-provided assignee. Document the decision.

Suggested Next Route:
Spec Agent for clarification.
```

**Covered spec requirements:**
- Requirement 1 (task creation fields): All six fields present in TaskInput. PASS.
- Requirement 2 (priority scoring 0-100): Base scores match spec exactly, urgency and tag weight bonuses implemented, clamped to [0,100]. PASS.
- Requirement 4 (ScheduleResult shape): All five fields present and typed. PASS.
- Requirement 5 (rejection with descriptive errors): Missing title, invalid priority, and past due dates all rejected with descriptive messages. PASS.
- Requirement 6 (configurable tag weights): Passed via ScheduleOptions.tagWeights. PASS.
- Constraint: pure TypeScript, no external deps. PASS.
- Constraint: priority scoring is pure. PASS.
- Constraint: tests included. PASS.

---

## 2. Architecture Adherence

The architecture is clean and well-structured. No violations found.

- Pure scoring function separated from side-effectful assignment. Good.
- WorkloadService is an injected interface (port/adapter pattern). Good.
- Validation is a separate helper. Good.
- Clock and ID generator are injectable for testability. Good.

No findings.

---

## 3. Test Quality

Tests are generally thorough with good use of deterministic helpers (fixed clock, stub IDs, mock workload service). Coverage of unhappy paths is solid.

```
ID:          CR-003
Severity:    Recommended
Dimension:   Test Quality
File:        src/__tests__/scheduler.test.ts

Finding:
No test verifies behavior with negative tag weights. The scorePriority
function uses tagWeights values directly in addition, and negative weights
could push the score below zero. The clamp to [0,100] handles this
correctly, but there is no test proving it.

Evidence:
All tag weight tests use positive values (15, 10, 50). No test passes a
negative tag weight to verify the floor clamp.

Impact:
Low -- the clamp logic is simple and correct. But an explicit test would
document the intended behavior for negative weights.

Required Action:
Add a test with a negative tag weight confirming the score floors at 0.

Suggested Next Route:
Programmer Agent.
```

```
ID:          CR-004
Severity:    Recommended
Dimension:   Test Quality
File:        src/__tests__/scheduler.test.ts

Finding:
No test verifies that handleTask works correctly when called with no
options object at all (i.e., handleTask(input) with no second argument).
The opts parameter is optional, but every test passes at least
{ now: fixedClock }.

Evidence:
All handleTask tests supply at least one option. The default code path
for Date.now() and defaultGenerateId() in handleTask is untested
end-to-end.

Impact:
Low -- individual functions have default-path tests, but the integration
through handleTask is not exercised with fully defaulted options.

Required Action:
Add one test calling handleTask(validInput) with no options argument.

Suggested Next Route:
Programmer Agent.
```

**Covered test areas:**
- scorePriority: base scores, urgency, tags, clamping, default clock. Good.
- assignTask: capacity check, at-capacity, over-capacity, recordAssignment ordering, error propagation. Good.
- handleTask validation: empty title, whitespace title, invalid priority, past date, unparseable date. Good.
- handleTask success: full result shape, capacity warning, no-service warning, service error warning, tag weights, custom ID, ISO timestamp. Good.

---

## 4. Code Quality and Maintainability

Code is clean, well-named, and well-structured. Functions are single-purpose. Types are precise.

```
ID:          CR-005
Severity:    Recommended
Dimension:   Code Quality
File:        src/scheduler.ts:241-304 (handleTask)

Finding:
The `now` function is called multiple times across the handleTask
pipeline: once in validateTaskInput (line 247 via opts), once in
scorePriority (line 254-261 via opts), and once at line 295 for
scheduledAt. If the clock advances between calls, the validation,
scoring, and timestamp could use different "now" values.

Evidence:
Lines 247, 260, and 295 each independently invoke the clock. With a real
clock (not the test stub), these could diverge.

Impact:
In practice the divergence would be microseconds and unlikely to matter.
However, for correctness, capturing now once at the top of handleTask and
passing it through would be more robust.

Required Action:
Capture `const nowMs = (opts?.now ?? Date.now)()` once at the top of
handleTask and pass the resolved timestamp (not the function) to
subroutines.

Suggested Next Route:
Refactor Agent.
```

```
ID:          CR-006
Severity:    Recommended
Dimension:   Code Quality
File:        src/scheduler.ts:254-261

Finding:
The `input.priority as Priority` type assertion bypasses TypeScript's
type narrowing after validation. This is safe here because
validateTaskInput has already confirmed the value is valid, but the
assertion creates a coupling between the validation order and the cast.

Evidence:
Line 256: `priority: input.priority as Priority`. If someone reorders
the code to score before validating, the cast would hide a bug.

Impact:
Low -- the current code is correct. But a safer pattern would be to have
validateTaskInput return a narrowed type or a validated TaskInput.

Required Action:
Consider having validateTaskInput return a discriminated union or a typed
validated object so the cast is unnecessary.

Suggested Next Route:
Refactor Agent.
```

No other code quality issues. Names are domain-aligned. No duplication. Complexity is appropriate.

---

## 5. Security Surface

```
ID:          CR-007
Severity:    Recommended
Dimension:   Security Surface
File:        src/scheduler.ts:35-42 (TaskInput)

Finding:
The description and tags fields are accepted without length validation.
In a real system, unbounded string input could be used for storage abuse
or injection attacks if these values are persisted or rendered.

Evidence:
validateTaskInput checks title, priority, and dueDate but does not
validate description length or tag count/length.

Impact:
Low for this scope (pure TypeScript, no persistence). Would become
relevant if integrated with a storage layer or UI rendering.

Required Action:
No action required for current scope. Flag for future if persistence is
added.

Suggested Next Route:
None for current scope.
```

No secrets, no endpoints, no external calls beyond the injected WorkloadService.

---

## 6. Non-Functional Characteristics

```
ID:          CR-008
Severity:    Recommended
Dimension:   Non-Functional
File:        src/scheduler.ts:124-128

Finding:
The tag bonus loop iterates over all tags with no bound on the number of
tags. For typical usage this is fine, but there is no guard against a
pathologically large tags array.

Evidence:
Lines 126-128: `for (const tag of input.tags)`. No length check on
input.tags.

Impact:
Negligible for current scope. Would matter if this function is called in
a hot path with user-controlled tag arrays.

Required Action:
No action required for current scope. Consider adding a max-tags
validation if the function will be exposed to untrusted input.

Suggested Next Route:
None for current scope.
```

No unbounded queries, no unprotected external calls, no missing error logging (errors are captured in warnings). The error path in handleTask (lines 284-288) correctly catches and surfaces workload service failures.

---

## 7. Function Quality Assessment

### Independent Re-Assessment

| Function | Programmer Score | Reviewer Score | Critical | High | Notes |
|---|---|---|---|---|---|
| `scorePriority` | 98 | 96 | 0 | 0 | Pure, well-documented. Minor: no complexity annotation (O(n) on tags). |
| `assignTask` | 95 | 93 | 0 | 1 | Does not incorporate priority score per spec req 3 (High). |
| `validateTaskInput` | 96 | 94 | 0 | 0 | Solid. Minor: no validation of dueDate edge case where date is exactly `now`. |
| `defaultGenerateId` | 100 | 100 | 0 | 0 | Trivial helper, score is appropriate. |
| `handleTask` | 93 | 90 | 0 | 1 | Multiple clock invocations (High: consistency risk). Spec gap on priority-based assignment flows through here. |

### Score Skepticism

The programmer did not score everything at 100, so a full skepticism pass is not required. However, `defaultGenerateId` at 100 is a trivial helper and the score is justified.

The module-level `@overallScore 95/100` is slightly high given the spec alignment gap in CR-001. Reviewer would place the module at 90-92 pending resolution of CR-001.

### Adversarial/Cross-Item Testing

The scheduler is not a batch processor or reducer, so adversarial aggregate testing is not strictly required. However, there is no test that exercises multiple sequential task assignments to the same user to verify that capacity tracking works across calls (this depends on the WorkloadService mock, so it is partially out of scope).

### Summary

```
## Function Quality Assessment

- Status: DEBT
- Functions assessed: 5
- Lowest score: 90 (handleTask, reviewer-adjusted)
- Critical findings: 0
- High findings: 2
- Missing assessments: 0
- Missing handoff-table evidence: yes
- Missing score-skepticism evidence: n/a
- Missing adversarial aggregate/cross-item evidence: n/a
- Required fixes: CR-001 (priority score not used in assignment per spec req 3)
- Recommended refactors: CR-003 (negative tag weight test), CR-004 (default-options integration test), CR-005 (single clock capture), CR-006 (type narrowing instead of cast)
- Suggested next route: Programmer (for CR-001), then Refactor (for CR-005, CR-006)
```

---

## Findings Summary

| ID | Severity | Dimension | Summary |
|---|---|---|---|
| CR-001 | **Required** | Spec Alignment | Priority score not used in assignment decision (spec req 3) |
| CR-002 | Recommended | Spec Alignment | Ambiguity: scheduler selects vs. validates assignee |
| CR-003 | Recommended | Test Quality | No test for negative tag weights |
| CR-004 | Recommended | Test Quality | No test for fully-defaulted handleTask options |
| CR-005 | Recommended | Code Quality | Clock called multiple times; should capture once |
| CR-006 | Recommended | Code Quality | Type assertion instead of type narrowing after validation |
| CR-007 | Recommended | Security Surface | No length bounds on description/tags (future concern) |
| CR-008 | Recommended | Non-Functional | No max-tags guard (future concern) |

**Required count**: 1
**Recommended count**: 7

---

## Verdict

**BLOCKED** on CR-001. The priority score is computed but never influences assignment, which contradicts spec requirement 3. This must be resolved (either by implementation change or spec clarification) before the work can proceed.

All other findings are Recommended and can be addressed by the Refactor Agent or deferred to a follow-up cycle.

**Suggested routing**: Spec Agent (to clarify req 3 intent) -> Programmer Agent (to implement fix for CR-001) -> Refactor Agent (for CR-005, CR-006).
