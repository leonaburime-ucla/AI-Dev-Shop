# Recovery Playbook

When a pipeline session ends mid-run (context limit hit, network drop, user closes session), the Coordinator uses this playbook to resume from the last valid checkpoint rather than restarting from scratch.

---

## Step 1 — Detect an Incomplete Run

At the start of every session, before doing anything else:

1. Ask the user: "Is there an active feature in progress?"
2. If yes, locate the feature folder: `specs/<NNN>-<feature-name>/`
3. Check for `.pipeline-state.md` in that folder
4. If found and status is `IN_PROGRESS` or `WAITING_FOR_HUMAN` → follow this playbook
5. If not found or status is `COMPLETE` → start fresh

---

## Step 2 — Validate the Checkpoint

Before resuming, verify the checkpoint is trustworthy:

| Check | How | Fail Action |
|-------|-----|-------------|
| Spec hash matches | Re-hash spec.md, compare to state file's `spec_hash` | Stop — spec may have changed. Escalate to human before resuming. |
| Completed stage artifacts exist | Check that every file listed in Completed Stages actually exists on disk | If missing, treat that stage as incomplete and re-run it |
| Current stage output is partial | Check whether the in-progress stage produced any artifact | If artifact exists and looks complete, treat stage as done and advance |

---

## Step 3 — Resume Decision Tree

```
Is status WAITING_FOR_HUMAN?
  YES → Present the pending human checkpoint to the user. Wait for approval. Then continue from current_stage.
  NO (IN_PROGRESS) → Continue at current_stage using the resume rules below.
```

### Resume Rules by Stage

| Stage | Idempotent? | Resume Action |
|-------|-------------|---------------|
| `spec` | Yes | Re-dispatch Spec Agent with existing spec as input. Instruct it to continue, not restart. |
| `clarify` | Yes | Re-dispatch Spec Agent in clarify mode with existing markers. |
| `architect` | Yes | Re-dispatch Architect Agent. Provide existing research.md if present. |
| `tasks` | Yes | Regenerate tasks.md from ADR. Safe to overwrite. |
| `tdd` | Yes | Re-dispatch TDD Agent. Provide existing partial test file if present. |
| `programmer` | **Partial** | Re-dispatch Programmer with existing code as context. Do not ask it to restart — continue from failing tests. |
| `testrunner` | Yes | Re-run. Pure reporting, no state. |
| `code-review` | Yes | Re-dispatch. Review is read-only. |
| `security` | Yes | Re-dispatch. Review is read-only. |
| `refactor` | Yes | Re-dispatch with same Code Review findings. |

**Partial** means: provide all existing artifacts as context. The agent should continue, not restart.

---

## Step 4 — Update State File

After successfully resuming:

1. Update `last_updated_at` in the state file
2. Add a note in the Notes section: `"Resumed from checkpoint at <timestamp>. Prior session ended at stage: <stage>."`
3. Continue writing state updates as normal from that point forward

---

## What Not to Do

- Do not re-run completed stages unless their artifact is missing or the spec hash has changed
- Do not ask the human to re-approve checkpoints they already cleared (the checkbox record is the source of truth)
- Do not resume if the spec hash has changed — this is a blocking condition requiring human review
- Do not resume a `FAILED` run — start fresh and reference the failed run's Notes for context
