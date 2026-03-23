# Session Continuity

This file defines the durable progress artifact for long-running or resumable work.

## Why This Exists

`.pipeline-state.md` tracks coordinator state and retry counters. It is not enough by itself for clean human or agent resume. Long-running work also needs a human-readable progress ledger that records what changed, what failed, and what should happen next.

## Required Artifact

Create a `progress-ledger.md` when either condition is true:

- the work is expected to cross sessions, handoffs, or context-window boundaries
- a failure cluster reaches retry 2 and resumption quality now matters more than raw speed

## Canonical Locations

- Feature pipeline runs: `<AI_DEV_SHOP_ROOT>/reports/pipeline/<NNN>-<feature-name>/progress-ledger.md`
- Non-feature toolkit maintenance or direct framework work: `<AI_DEV_SHOP_ROOT>/reports/continuity/<workstream>/progress-ledger.md`

The state file remains the machine-oriented checkpoint. The progress ledger is the human/agent resume surface.

## Minimum Contents

Every `progress-ledger.md` must include:

- workstream metadata and owner
- current objective
- last verified good state
- recent progress since the last checkpoint
- next 1-3 concrete actions
- blockers or open questions
- artifact/path references
- failure-cluster history with current hypothesis
- explicit resume instructions for a fresh session

Use `<AI_DEV_SHOP_ROOT>/templates/progress-ledger-template.md`.

## Update Triggers

Update the ledger:

1. when the ledger is first created
2. before any planned session stop or handoff
3. after each retry for a recurring failure cluster
4. before asking a fresh session or another agent to resume the work
5. before claiming a long-running workstream is complete

## Coordinator Rules

- Create the ledger at the first meaningful checkpoint for long-running work if it does not already exist.
- Include the ledger path in `.pipeline-state.md`.
- Read the ledger before resuming any interrupted run.
- If a run is resumable but the ledger is missing, recreate it before further dispatch.

## Scope Notes

- This is not a full audit log. Keep it concise and high-signal.
- Prefer references to artifact paths over large pasted logs.
- The goal is to let a fresh session continue with minimal reconstruction cost.
