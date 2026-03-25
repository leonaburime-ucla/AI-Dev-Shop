# Pipeline State Format

Every pipeline run writes a `.pipeline-state.md` file to the active feature's canonical pipeline folder. The Coordinator reads this file at the start of every session to detect and resume incomplete runs.

**Location:** `framework/reports/pipeline/<NNN>-<feature-name>/.pipeline-state.md`

---

## File Format

```markdown
# Pipeline State

- run_id: <uuid or timestamp-based ID, e.g. 2026-02-22T14:30:00Z>
- feature: <NNN>-<feature-name>
- coordinator_mode: review | pipeline | direct
- debug_mode: on | off
- spec_provider: <speckit | openspec | bmad | other>
- spec_version: <version>
- spec_hash: <sha256>
- spec_entrypoint_path: <provider-defined planning entrypoint path>
- spec_readiness_artifact: <provider-defined readiness artifact path>
- spec_support_paths: <comma-separated list or N/A>
- started_at: <ISO-8601 UTC>
- last_updated_at: <ISO-8601 UTC>
- progress_ledger_path: <framework/reports/pipeline/.../progress-ledger.md or framework/reports/continuity/.../progress-ledger.md>
- current_stage: <stage name — see Stages below>
- status: IN_PROGRESS | WAITING_FOR_HUMAN | COMPLETE | FAILED | CANCELLED | ABORTED

## Completed Stages

| Stage | Completed At | Output Artifact | Output Hash |
|-------|-------------|-----------------|-------------|
| spec | 2026-02-22T14:32:00Z | <provider-defined spec entrypoint> | sha256:abc... |
| architect | 2026-02-22T15:10:00Z | framework/reports/pipeline/001-feature/adr.md | sha256:def... |
| tasks | 2026-02-22T15:12:00Z | framework/reports/pipeline/001-feature/tasks.md | sha256:ghi... |

## Current Stage Detail

- stage: tdd
- dispatched_at: 2026-02-22T15:13:00Z
- job_status: QUEUED | DISPATCHED | RUNNING | DONE | RETRYING | FAILED | ESCALATED | WAITING_FOR_HUMAN | CANCELLED | ABORTED
- retry_count: 0
- current_hypothesis: <one sentence or N/A>
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

## Field Reference

### `progress_ledger_path` (required for resumable or long-running work)

```markdown
progress_ledger_path: framework/reports/pipeline/<NNN>-<feature-name>/progress-ledger.md
```

Points to the human/agent-readable resume surface defined in `<AI_DEV_SHOP_ROOT>/harness-engineering/session-continuity.md`.

- Required when work is expected to cross sessions, handoffs, or retry-heavy loops
- Recommended for any feature that reaches programmer retry 2+
- If absent on a resumable run, the Coordinator should create it before further dispatch

### `coordinator_mode` (required)

```
coordinator_mode: review | pipeline | direct
```

Tracks the Coordinator's current operating mode:
- `pipeline` — full multi-agent pipeline is active; jobs are created and tracked
- `review` — Coordinator is reviewing artifacts or answering questions; no jobs are created
- `direct` — user is working directly with a single agent; in-progress jobs are set to WAITING_FOR_HUMAN, not cancelled

### `debug_mode` (optional, default: off)

```
debug_mode: on | off
```

When `on`, the Observer emits `[DEBUG]` trace entries at every dispatch, gate check, and mode switch. Does not affect job state or pipeline logic — controls trace verbosity only.

### `spec_provider` (required for new runs)

```markdown
spec_provider: speckit | openspec | bmad | other
```

Records which upstream planning provider owns the spec surface for this run.

Legacy runs may omit this field. In that case, treat the run as Speckit compatibility mode unless a human says otherwise.

### `spec_entrypoint_path` and `spec_readiness_artifact` (required for new runs)

```markdown
spec_entrypoint_path: <provider-defined requirements entrypoint>
spec_readiness_artifact: <provider-defined readiness artifact>
```

- `spec_entrypoint_path` is the file used for drift detection and resume hashing
- `spec_readiness_artifact` is the file or artifact used to prove the planning surface is ready for architecture work
- for the default Speckit provider, these typically map to `feature.spec.md` and `spec-dod.md`

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
| `qa-e2e` | QA/E2E Agent writing browser tests |
| `testrunner` | TestRunner Agent verifying pass rate |
| `code-review` | Code Review Agent classifying findings |
| `security` | Security Agent reviewing threat surface |
| `devops` | DevOps Agent producing IaC/CI/deployment configs |
| `docs` | Docs Agent generating user-facing documentation |
| `refactor` | Refactor Agent proposing improvements |
| `done` | Pipeline complete, artifacts shipped |

---

## Write Rules

- The Coordinator writes or updates `.pipeline-state.md` at every stage transition.
- Keep `progress_ledger_path` current when a progress ledger exists.
- Update `current_hypothesis` whenever a retry changes approach.
- After each human checkpoint is cleared, mark the corresponding checkbox.
- Never delete a completed stage row — append only.
- On FAILED status, write the failure reason to Notes before stopping.

---

## Read Rules

- At session start, the Coordinator checks for `.pipeline-state.md` in the active feature folder.
- If found and status is `IN_PROGRESS` or `WAITING_FOR_HUMAN`, follow the Recovery Playbook (`<AI_DEV_SHOP_ROOT>/framework/workflows/recovery-playbook.md`).
- If found and status is `ABORTED`, treat as resumable — follow the Recovery Playbook.
- If `progress_ledger_path` is present, read the ledger before resuming or retrying.
- If the ledger references offloaded evidence files, verify they still exist before resuming.
- If found and status is `COMPLETE`, `FAILED`, or `CANCELLED`, do not resume — start a new run or treat as reference only.
- If not found, create a new one at the start of the spec stage.

---

## Example: Mid-Run State (Programmer stage, active retry cluster)

```markdown
# Pipeline State

- run_id: 2026-02-22T14:30:00Z
- feature: 003-csv-invoice-export
- coordinator_mode: pipeline
- debug_mode: off
- spec_version: 1.1.0
- spec_hash: sha256:a3f8c2d1e4b7091f56ac83e29d047b5f1c6e82a4d9f3071b2c5e8d4a7f1b6c9
- started_at: 2026-02-22T14:30:00Z
- last_updated_at: 2026-02-22T17:45:00Z
- progress_ledger_path: framework/reports/pipeline/003-csv-invoice-export/progress-ledger.md
- current_stage: programmer
- spec_provider: speckit
- status: IN_PROGRESS
- spec_entrypoint_path: specs/003-csv-invoice-export/feature.spec.md
- spec_readiness_artifact: specs/003-csv-invoice-export/spec-dod.md
- spec_support_paths: specs/003-csv-invoice-export/api.spec.md, specs/003-csv-invoice-export/state.spec.md, specs/003-csv-invoice-export/orchestrator.spec.md, specs/003-csv-invoice-export/ui.spec.md, specs/003-csv-invoice-export/errors.spec.md, specs/003-csv-invoice-export/behavior.spec.md, specs/003-csv-invoice-export/traceability.spec.md, specs/003-csv-invoice-export/spec-manifest.md

## Completed Stages

| Stage | Completed At | Output Artifact | Output Hash |
|-------|-------------|-----------------|-------------|
| spec | 2026-02-22T14:32:00Z | specs/003-csv-invoice-export/feature.spec.md | sha256:a3f8... |
| red-team | 2026-02-22T14:55:00Z | framework/reports/pipeline/003-csv-invoice-export/red-team-findings.md | sha256:b1c4... |
| architect | 2026-02-22T15:30:00Z | framework/reports/pipeline/003-csv-invoice-export/adr.md | sha256:b9e2... |
| tasks | 2026-02-22T15:32:00Z | framework/reports/pipeline/003-csv-invoice-export/tasks.md | sha256:c7d3... |
| tdd | 2026-02-22T16:10:00Z | framework/reports/pipeline/003-csv-invoice-export/test-certification.md | sha256:c1d4... |

## Current Stage Detail

- stage: programmer
- dispatched_at: 2026-02-22T16:15:00Z
- job_status: RETRYING
- retry_count: 2
- current_hypothesis: CSV escaping logic wraps fields correctly but does not double embedded quotes
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
