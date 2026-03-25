# Evaluator Contract: <slice-slug>

- Contract Slug: <short-slice-name>
- Workstream: <feature-id or maintenance-name>
- Scope Type: feature-pipeline | toolkit-maintenance | direct-run
- Generator Owner: <agent or human>
- Evaluator Owner: <agent or human>
- Source Prompt Or Spec: <path, issue, or prompt summary>
- Evaluator Mode: required | optional
- Artifacts Root: <reports path for this workstream>
- Opened At: <ISO-8601 UTC>
- Last Updated At: <ISO-8601 UTC>

## Slice

<what this loop is trying to build right now>

## Non-Goals

- <explicit non-goal>
- <explicit non-goal>

## Completion Criteria

- <criterion 1>
- <criterion 2>
- <criterion 3>

## Runtime Surfaces To Exercise

- <UI path, API path, state path, or service path>
- <UI path, API path, state path, or service path>

## Blocking Thresholds

| Dimension | Threshold | Why Blocking |
|---|---|---|
| <dimension> | <minimum acceptable score or pass condition> | <why failure here blocks the slice> |

## Required Artifacts

| Artifact | Location | Required | Notes |
|---|---|---|---|
| progress-ledger | <path or N/A> | Yes / No | |
| evaluator report | <path> | Yes / No | |
| offloads | <path or N/A> | Yes / No | |

## Scoring Rubric

| Dimension | Passing Signal | Failure Signal | Weight Or Threshold |
|---|---|---|---|
| <dimension> | <what pass looks like> | <what fail looks like> | <weight or hard threshold> |

## Generator Response Rule

Describe when the generator should refine the current direction, when it should pivot, and what evidence the next round must include.
