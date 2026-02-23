# Escalation Policy

Defines when agents must stop and escalate to a human, what the retry budgets are per stage, and what distinguishes a recoverable failure from a systemic problem. This document governs all escalation decisions in the pipeline.

Supplements the convergence policy in `AI-Dev-Shop/AGENTS.md` and the resume logic in `AI-Dev-Shop/workflows/recovery-playbook.md`.

---

## Escalation Triggers (Blocking — Pipeline Halts)

The following conditions halt the pipeline immediately. The Coordinator must surface the issue to the human and wait for a decision before any further dispatch.

| Trigger | Stage | What to Surface to Human |
|---------|-------|--------------------------|
| Spec hash mismatch between dispatch and agent output | Any | The two hashes, which file changed, when it changed |
| 3+ BLOCKING findings from Red-Team Agent | post-spec | All BLOCKING findings with exact spec refs; recommended spec changes |
| Security finding classified Critical or High | security | Full finding, exploit scenario, proposed mitigation |
| Same failure cluster persists after hitting retry budget (see below) | programmer, tdd | Cluster ID, all failing tests, retry count, spec ACs involved, hypothesis |
| Spec discovered to be wrong mid-implementation | programmer | What the code reveals, what the spec says, recommended spec revision |

---

## Retry Budgets Per Stage

When a stage fails, the Coordinator re-dispatches up to the budget. On budget exhaustion, escalate to human — do not retry further.

**Source of truth:** `AI-Dev-Shop/workflows/job-lifecycle.md` defines these budgets. This table mirrors those values. If they ever conflict, `job-lifecycle.md` wins.

| Stage | Max Retries | Escalation Trigger | Reset Condition |
|-------|------------|-------------------|-----------------|
| `spec` | 2 | Unresolvable ambiguity after 2 passes | Human approval resets count |
| `clarify` | 1 | Human must provide answers directly | Human answers reset count |
| `architect` | 2 | Architecture violation without documented rationale | Human sign-off resets count |
| `tdd` | 3 | Same test failures after 3 cycles | Spec revision resets count |
| `programmer` | 5 total retries; escalate any single cluster after 3 retries | Single cluster failing after 3 retries signals spec/architecture problem | New cluster resets cluster count; spec hash change resets all |
| `testrunner` | 2 (tooling failures only) | Test logic failures are not retried — they route to Programmer | Tooling fix resets count |
| `code-review` | 1 | Rare — escalate only if output is malformed | N/A |
| `security` | 1; Critical/High escalate immediately without retry | All Critical/High findings are immediate blocking escalations | Human sign-off closes the finding |
| `refactor` | 1 | Not retried — output is proposals, not implementation | N/A |

**Programmer budget clarification:** The 5-retry total budget and the 3-retry per-cluster escalation are separate rules. A cluster failing 3 times triggers an immediate escalation on that cluster even if the total budget is not yet exhausted. Total budget exhaustion triggers escalation regardless of cluster count.

**Budget tracking:** The Coordinator records retry counts in the `Iteration Counts` table of `.pipeline-state.md`. An agent may not be dispatched if its stage is at budget — escalate first.

---

## Escalation Severity Levels

| Level | Examples | Human Action Required |
|-------|----------|----------------------|
| **BLOCKING** | Spec hash mismatch, Critical/High security finding | Full stop. Human decision before any dispatch. |
| **ADVISORY** | Red-Team ADVISORY finding, Medium security finding, Recommended code review finding | Pipeline continues. Human informed. Human may intervene or accept. |
| **FLAG** | Observer drift alert, Low security finding, scorecard regression | Logged. Surfaced in next Observer report. No immediate stop. |

---

## What Escalation Is Not

Do not escalate for:
- Expected test failures during `programmer` cycles (within budget)
- Red-Team findings classified as ADVISORY only
- Refactor proposals the Refactor Agent disagrees with
- Architecture alternatives the Architect considered and rejected with documentation
- Observer recommendations (these are inputs to future work, not stops)

Escalating for non-blocking issues erodes human trust in escalations and causes humans to ignore them. Reserve escalation for conditions that genuinely require a human decision.

---

## Escalation Message Format

When surfacing to the human, the Coordinator must include:

```
ESCALATION — [BLOCKING / ADVISORY / FLAG]

Feature: <feature name>
Stage: <pipeline stage>
Trigger: <one sentence — which rule was hit>

Evidence:
<specific artifact references, quotes, hashes>

Options:
A. <option and consequence>
B. <option and consequence>
C. Abort this feature run

Waiting for human decision.
```

The Coordinator does not suggest a preference unless asked. Present options neutrally.

---

## After Human Decision

1. Record the decision in `.pipeline-state.md` Notes section: what was decided, by whom, when
2. If the decision results in a spec revision, the spec hash changes — all downstream artifacts (ADR, test certification) are invalidated and must be re-run
3. Mark the relevant human checkpoint checkbox in `.pipeline-state.md`

---

## Systemic vs. One-Off Failures

The Observer Agent distinguishes:

- **One-off failure**: A cluster appears once, resolves within budget, does not recur across features. Log as `[FAILURE]` in memory-store, no further action.
- **Systemic failure**: Same cluster type appears in 3+ features, or same agent consistently requires max retries. This signals a skills.md problem, not a feature problem. Observer flags to Coordinator; Coordinator surfaces to human with a skills.md update recommendation.

Systemic failure escalation goes in the Observer's weekly pattern report, not as a blocking pipeline escalation.
