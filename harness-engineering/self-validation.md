# Self-Validation Harness Templates

This file defines the downstream runtime harness pattern for repos that use this toolkit.

## Why This Exists

Green unit tests are not the same as a working app. Before handoff, agents often need a repo-local runbook for booting the app, checking logs, exercising one critical path, and retrying once with fresh evidence.

## What A Self-Validation Harness Is

A self-validation harness is a stack-specific runbook that tells the implementing agent how to:

- boot the app or service
- inspect logs and startup health
- exercise a critical user or API path
- capture artifacts when something fails
- retry after one scoped fix before handoff

## When To Use It

Use a self-validation harness when the change affects:

- runtime startup or configuration
- HTTP/API behavior
- browser or mobile UI behavior
- auth, background jobs, queues, or integrations
- database migrations or deployment-sensitive behavior

Pure documentation work, policy/docs-only framework edits, and non-runtime markdown maintenance do not need one.

## Canonical Templates

Start from the closest stack template under `<AI_DEV_SHOP_ROOT>/templates/self-validation/`:

- `generic-web-app-template.md`
- `node-api-template.md`
- `python-service-template.md`
- `supabase-template.md`

## Minimum Validation Loop

Every self-validation harness should include:

1. environment preflight
2. boot command
3. log inspection checkpoints
4. one critical-path verification
5. one negative-path or edge-path verification
6. artifact capture for failures
7. one retry-after-fix pass before handoff

## Output Location

Store the run result at:

`<AI_DEV_SHOP_ROOT>/reports/self-validation/SV-<feature-or-workstream>-<YYYY-MM-DD-HHmm>.md`

If long logs or DOM dumps are needed, offload them per `<AI_DEV_SHOP_ROOT>/harness-engineering/context-offloading.md`.

## Handoff Rule

If runtime validation is in scope and the harness was not run, the agent must say so explicitly and treat the handoff as incomplete or partial. Do not imply “done” when the runtime path was never exercised.
