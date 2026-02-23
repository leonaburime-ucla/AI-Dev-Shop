# Pipeline State Format

Every pipeline run writes a `.pipeline-state.md` file to the active feature folder. The Coordinator reads this file at the start of every session to detect and resume incomplete runs.

**Location:** `specs/<NNN>-<feature-name>/.pipeline-state.md`

---

## File Format

```markdown
# Pipeline State

- run_id: <uuid or timestamp-based ID, e.g. 2026-02-22T14:30:00Z>
- feature: <NNN>-<feature-name>
- output_root: <absolute path to project-local output directory>
- coordinator_mode: review | pipeline | direct
- debug_mode: on | off
- spec_version: <version>
- spec_hash: <sha256>
- started_at: <ISO-8601 UTC>
- last_updated_at: <ISO-8601 UTC>
- current_stage: <stage name — see Stages below>
- status: IN_PROGRESS | WAITING_FOR_HUMAN | COMPLETE | FAILED | CANCELLED | ABORTED

## Completed Stages

| Stage | Completed At | Output Artifact | Output Hash |
|-------|-------------|-----------------|-------------|
| spec | 2026-02-22T14:32:00Z | specs/001-feature/spec.md | sha256:abc... |
| architect | 2026-02-22T15:10:00Z | specs/001-feature/adr.md | sha256:def... |
| tasks | 2026-02-22T15:12:00Z | specs/001-feature/tasks.md | sha256:ghi... |

## Current Stage Detail

- stage: tdd
- dispatched_at: 2026-02-22T15:13:00Z
- job_status: RUNNING | RETRYING | WAITING_FOR_HUMAN
- retry_count: 0
- last_output_summary: <one sentence>

## Iteration Counts

| Stage | Cycle Count | Budget | Status |
|-------|-------------|--------|--------|
| tdd | 1 | 3 | WITHIN_BUDGET |
| programmer | 0 | 5 | NOT_STARTED |

## Failure Clusters

| Cluster | First Seen | Retry Count | Stage | Notes |
|---------|-----------|-------------|-------|-------|
| AC-03 timeout edge case | 2026-02-22T15:20:00Z | 2 | programmer | |

## Human Checkpoints Cleared

- [ ] Spec approval
- [ ] Architecture sign-off (includes Constitution Check)
- [ ] Convergence escalation (if triggered)
- [ ] Security sign-off

## Notes

<free-form notes from Coordinator, e.g. "AC-05 deferred to next spec revision", "Security agent flagged Medium finding, tracked in adr.md", "Constitution Article III exception logged in ADR">
```

---

## Field Reference: New Required and Optional Fields

### `output_root` (required)

```
output_root: <absolute path to project-local output directory>
```

- Must be set before any artifact is written
- Coordinator validates it is not inside `AI-Dev-Shop/`
- All artifact paths in the pipeline are resolved relative to this root

### `coordinator_mode` (required)

```
coordinator_mode: review | pipeline | direct
```

Tracks the Coordinator's current operating mode:
- `pipeline` — full multi-agent pipeline is active; jobs are created and tracked
- `review` — Coordinator is reviewing artifacts or answering questions; no jobs are created
- `direct` — user is working directly with a single agent; in-progress jobs are PAUSED, not cancelled

### `debug_mode` (optional, default: off)

```
debug_mode: on | off
```

When `on`, the Observer emits `[DEBUG]` trace entries at every dispatch, gate check, and mode switch. Does not affect job state or pipeline logic — controls trace verbosity only.

---

## Stages (Valid Values for `current_stage`)

| Stage | Description |
|-------|-------------|
| `spec` | Spec Agent writing or revising spec |
| `clarify` | Spec Agent resolving [NEEDS CLARIFICATION] markers |
| `architect` | Architect Agent producing research.md + ADR |
| `tasks` | Coordinator generating tasks.md |
| `tdd` | TDD Agent writing and certifying tests |
| `programmer` | Programmer Agent implementing |
| `testrunner` | TestRunner Agent verifying pass rate |
| `code-review` | Code Review Agent classifying findings |
| `security` | Security Agent reviewing threat surface |
| `refactor` | Refactor Agent proposing improvements |
| `done` | Pipeline complete, artifacts shipped |

---

## Write Rules

- The Coordinator writes or updates `.pipeline-state.md` at every stage transition.
- After each human checkpoint is cleared, mark the corresponding checkbox.
- Never delete a completed stage row — append only.
- On FAILED status, write the failure reason to Notes before stopping.

---

## Read Rules

- At session start, the Coordinator checks for `.pipeline-state.md` in the active feature folder.
- If found and status is `IN_PROGRESS` or `WAITING_FOR_HUMAN`, follow the Recovery Playbook (`AI-Dev-Shop/workflows/recovery-playbook.md`).
- If found and status is `ABORTED`, treat as resumable — follow the Recovery Playbook.
- If found and status is `COMPLETE`, `FAILED`, or `CANCELLED`, do not resume — start a new run or treat as reference only.
- If not found, create a new one at the start of the spec stage.

---

## Example: Mid-Run State (Programmer stage, active retry cluster)

```markdown
# Pipeline State

- run_id: 2026-02-22T14:30:00Z
- feature: 003-csv-invoice-export
- output_root: /Users/la/projects/my-app
- coordinator_mode: pipeline
- debug_mode: off
- spec_version: 1.1.0
- spec_hash: sha256:a3f8c2d1e4b7091f56ac83e29d047b5f1c6e82a4d9f3071b2c5e8d4a7f1b6c9
- started_at: 2026-02-22T14:30:00Z
- last_updated_at: 2026-02-22T17:45:00Z
- current_stage: programmer
- status: IN_PROGRESS

## Completed Stages

| Stage | Completed At | Output Artifact | Output Hash |
|-------|-------------|-----------------|-------------|
| spec | 2026-02-22T14:32:00Z | specs/003-csv-invoice-export/spec.md | sha256:a3f8... |
| red-team | 2026-02-22T14:55:00Z | specs/003-csv-invoice-export/red-team-findings.md | sha256:b1c4... |
| architect | 2026-02-22T15:30:00Z | specs/003-csv-invoice-export/adr.md | sha256:b9e2... |
| tasks | 2026-02-22T15:32:00Z | specs/003-csv-invoice-export/tasks.md | sha256:c7d3... |
| tdd | 2026-02-22T16:10:00Z | specs/003-csv-invoice-export/test-certification.md | sha256:c1d4... |

## Current Stage Detail

- stage: programmer
- dispatched_at: 2026-02-22T16:15:00Z
- job_status: RETRYING
- retry_count: 2
- last_output_summary: AC-06 and AC-07 (CSV escaping) still failing; double-quote escape logic inverted

## Iteration Counts

| Stage | Cycle Count | Budget | Status |
|-------|-------------|--------|--------|
| tdd | 1 | 3 | WITHIN_BUDGET |
| programmer | 2 | 5 | WITHIN_BUDGET |

## Failure Clusters

| Cluster | First Seen | Retry Count | Stage | Notes |
|---------|-----------|-------------|-------|-------|
| AC-06/AC-07 RFC4180 escaping | 2026-02-22T16:20:00Z | 2 | programmer | Double-quote escape logic inverted — wraps but does not double internal quotes |

## Human Checkpoints Cleared

- [x] Spec approval
- [x] Architecture sign-off (includes Constitution Check)
- [ ] Convergence escalation (if triggered)
- [ ] Security sign-off

## Notes

Resumed from checkpoint at 2026-02-22T17:00:00Z. Prior session ended during programmer retry 1.
AC-06/AC-07 cluster: if retry count reaches 3, escalate — this may be a spec precision issue on INV-01.
```
