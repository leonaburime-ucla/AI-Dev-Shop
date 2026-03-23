# Pre-Completion And Loop-Detection Tripwires

This file defines deterministic tripwires that catch two common failure modes:

- premature completion claims
- blind retry loops

## Pre-Completion Checklist

Before an agent claims `done`, `ready`, `fixed`, `green`, or equivalent, it must verify:

1. the active task/spec/ADR it was supposed to satisfy
2. fresh evidence from the relevant command or artifact
3. that no tests were deleted or weakened to manufacture a pass
4. that changed files stayed within scope or any deviation is explicitly reported
5. what remains open, if anything

For implementation and verification stages, the handoff should include a dedicated `Pre-Completion Checklist` section.

## Coordinator Rejection Rule

Reject the handoff and keep the job out of `DONE` if:

- the checklist is missing
- the checklist cites stale evidence
- the agent cannot map the claimed completion back to the task/spec

## Loop-Detection Triggers

Treat the run as being in a loop when any of these happen inside one failure cluster:

- the same file is edited 3 times
- the same test/command is rerun 3 times with materially identical failure output
- retry 2 completes without a materially new hypothesis or experiment

## Required Response To A Loop Alert

When a loop trigger fires:

1. stop blind retrying
2. write a `Loop Alert` note in the progress ledger
3. state the current hypothesis, why the last approach failed, and the next different approach
4. if no different approach exists, escalate instead of spending another cycle

## Relation To Retry Budgets

Loop detection sits below the normal stage retry budget. It is an early warning layer, not a replacement for escalation policy.

The goal is to interrupt waste earlier than "cluster burned 3 full retries."

## Examples

- same CSV escaping file edited three times with the same failing edge-case tests -> write loop alert and change debugging approach before retry 3
- agent says "done" after a partial suite run -> reject handoff because the completion checklist lacks fresh full-scope evidence
- tests pass only because assertions were removed -> hard failure, not a valid completion
