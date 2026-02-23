# State & Schema Validator Checklist

A quick sanity-check for humans before resuming a pipeline run or reviewing memory entries. Run this when: resuming an interrupted run, onboarding to an in-progress feature, or auditing memory quality.

---

## 1. Pipeline State File (`.pipeline-state.md`)

Located at: `specs/<NNN>-<feature-name>/.pipeline-state.md`

### Required fields
- [ ] `run_id` is present and non-empty
- [ ] `spec_hash` is present — re-hash `spec.md` and confirm it matches
- [ ] `current_stage` is a valid stage name (see `AI-Dev-Shop/workflows/pipeline-state-format.md`)
- [ ] `status` is one of: `IN_PROGRESS` | `WAITING_FOR_HUMAN` | `COMPLETE` | `FAILED`
- [ ] `last_updated_at` timestamp is recent (if stale by days, the run may have been abandoned)

### Completed stages
- [ ] Every file listed in the Completed Stages table actually exists on disk
- [ ] Output hashes are present for each completed stage (not blank)

### Human checkpoints
- [ ] Checkboxes reflect what was actually approved — no unchecked box for a stage that's already past

### Current stage detail
- [ ] `job_status` is a valid state: `QUEUED` | `DISPATCHED` | `RUNNING` | `RETRYING` | `DONE` | `FAILED` | `ESCALATED` | `WAITING_FOR_HUMAN` | `CANCELLED` | `ABORTED`
- [ ] If `job_status` is `RETRYING`, `retry_count` is present and within the stage's budget
- [ ] If `job_status` is `ABORTED`, treat as resumable — follow `AI-Dev-Shop/workflows/recovery-playbook.md`
- [ ] If `job_status` is `CANCELLED`, do not resume — start a new run

### Failure clusters
- [ ] Each cluster row has a `First Seen` date and `Retry Count`
- [ ] No cluster has retry count above its stage budget without an escalation note

---

## 2. Memory Store Entries (`project-knowledge/memory-store.md`)

Run this when reviewing entries written by the Observer, or when promoting entries to agent skills.md files.

### Per-entry checks
- [ ] `entry_id` is present and follows format: `TYPE-YYYYMMDD-NNN` (e.g. `FAILURE-20260222-001`)
- [ ] `date` is a valid ISO-8601 timestamp
- [ ] `tags` are present and use `#lowercase-hyphenated` format
- [ ] If `supersedes` references another entry_id, that entry exists in the file
- [ ] If `expires_at` is set, check whether the entry has expired — expired entries should be excluded from injection

### FAILURE entries
- [ ] `root_cause` is one sentence, specific enough to be actionable
- [ ] `resolution` is present if `resolved_by` is set (unresolved failures are OK if still open)
- [ ] `occurrences` count is accurate

### DECISION entries
- [ ] `decision` field is a single declarative sentence (not a question, not "we might")
- [ ] `rationale` explains why the alternative was not chosen

### FACT entries
- [ ] `content` is specific — not "check the docs" but the actual fact
- [ ] `expires_at` is set if the fact is time-sensitive (e.g. an API version that will change)

---

## 3. Quick Resume Decision

After running the above checks:

| Condition | Action |
|-----------|--------|
| All checks pass, status `IN_PROGRESS` | Resume from `current_stage` per recovery playbook |
| Spec hash mismatch | Stop — escalate to human before resuming |
| Missing artifact for completed stage | Re-run that stage, then continue |
| `job_status` is `ABORTED` | Resume per recovery playbook |
| `job_status` is `CANCELLED` | Do not resume — start fresh |
| `job_status` is `FAILED` | Do not resume — start fresh, reference Notes for context |
| Status is `COMPLETE` | Do not resume — pipeline finished |
