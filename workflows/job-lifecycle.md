# Job Lifecycle

Every agent dispatch is a job. Jobs have explicit lifecycle states. The Coordinator tracks job state in the active `.pipeline-state.md` file and applies retry and backoff rules before escalating to a human.

---

## States

```
QUEUED → DISPATCHED → RUNNING → DONE
                              ↘ RETRYING → RUNNING (loop)
                              ↘ FAILED
                              ↘ ESCALATED
                              ↘ WAITING_FOR_HUMAN → RUNNING (after approval)
                              ↘ CANCELLED  (operator decision — terminal)
                              ↘ ABORTED    (external condition — terminal)
```

| State | Meaning |
|-------|---------|
| `QUEUED` | Coordinator has decided to dispatch but has not yet sent context to the agent |
| `DISPATCHED` | Agent context sent; waiting for first output |
| `RUNNING` | Agent is actively producing output |
| `DONE` | Agent produced a valid output satisfying its handoff contract |
| `RETRYING` | Output was rejected (failed validation, missing handoff contract, spec hash mismatch); queued for re-dispatch |
| `FAILED` | Retry budget exhausted; job cannot proceed without human intervention |
| `ESCALATED` | Coordinator has routed to human due to budget exhaustion or blocking condition |
| `WAITING_FOR_HUMAN` | Job is paused at a mandatory human checkpoint |
| `CANCELLED` | Human explicitly stopped the job. Intentional, no error. Record reason in `.pipeline-state.md` Notes. |
| `ABORTED` | Job stopped due to external condition (context limit hit, session dropped, system error). Not intentional — resume via recovery playbook. |

---

## Retry Policy

| Stage | Max Retries | Backoff | Escalation Trigger |
|-------|-------------|---------|-------------------|
| `spec` | 2 | None — immediate | Unresolvable [NEEDS CLARIFICATION] after 2 passes |
| `clarify` | 1 | None | Human must provide answers |
| `architect` | 2 | None | Architecture pattern violation without documented rationale |
| `tdd` | 3 | None | Same test failures after 3 cycles |
| `programmer` | 5 total retries across all clusters | Inject failure cluster summary each retry | Same failing cluster after 3 retries (escalate that cluster even if total budget not exhausted) |
| `testrunner` | 2 | None | Infrastructure/tooling failure (not test logic) |
| `code-review` | 1 | None | Rare — escalate if output is malformed |
| `security` | 1 | None | Escalate all Critical/High findings immediately |

**Backoff rule for Programmer retries 3+:**
Before dispatching retry 4 or 5, inject the full failure cluster history and ask the agent to reason about root cause before attempting a fix. Do not just re-dispatch with the same context — that produces the same result.

---

## Rejection Criteria

A job output is rejected (triggers `RETRYING`) if any of the following are true:

- Output does not reference the active spec version and hash
- Handoff contract is missing or incomplete (no input refs, output summary, risks, or suggested next)
- Agent operated outside its assigned scope (e.g., Programmer refactored untouched code)
- Output contains a known failure marker (e.g., "[NEEDS CLARIFICATION]" left unresolved by Spec Agent)

---

## Escalation Criteria

Escalate to human (set state to `ESCALATED`) when:

- Any stage hits its max retry count
- Programmer: same failing cluster persists after 3 retries — this signals a spec or architecture problem, not a code problem
- Security: any Critical or High finding
- Spec hash changes mid-run
- Two agents produce directly conflicting guidance

---

## Recording Job State

In `.pipeline-state.md`, update the Current Stage Detail block at every state transition:

```markdown
## Current Stage Detail

- stage: programmer
- dispatched_at: 2026-02-22T15:13:00Z
- job_status: RETRYING
- retry_count: 2
- last_output_summary: AC-03 and AC-07 still failing; timeout edge case not handled
```

When a job reaches `DONE`, move it to the Completed Stages table and clear the Current Stage Detail block for the next stage.
