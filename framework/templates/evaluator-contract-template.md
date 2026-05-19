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

## Evidence Surfaces

The evaluator must base its judgment on these surfaces. If required evidence is missing, the evaluator must fail the evaluation — not guess.

| Surface | Required | How To Inspect |
|---|---|---|
| Live runtime (UI paths, API requests, state) | Yes / No | <method: browser, curl, DB query> |
| Code diffs | Yes / No | <git diff scope> |
| Test execution results | Yes / No | <command or report path> |
| Coverage reports | Yes / No | <tool and threshold> |
| Generator handoff documentation | Yes / No | <expected path> |
| PR description / commit ledger | Yes / No | <where to find it> |

If a surface is not applicable, mark it `N/A` with a one-line rationale.

## Blocking Thresholds

| Dimension | Threshold | Why Blocking |
|---|---|---|
| <dimension> | <minimum acceptable score or pass condition> | <why failure here blocks the slice> |

## Fail Conditions

The slice explicitly FAILS if any of these occur, regardless of rubric scores:

- **Ignored Feedback**: Generator skipped or dismissed previous evaluator feedback without stated rationale
- **Missing Evidence**: Generator claimed pass without providing required test results, diffs, or handoff docs
- **Evaluation Lapse**: Evaluator failed to inspect a mandated evidence surface or runtime surface
- **Threshold Breach**: Any dimension falls below its defined hard blocking threshold
- **Artifact Gap**: Required artifacts (progress-ledger, evaluator report, offloads) are missing or malformed
- **Evidence Contradiction**: Handoff or PR claims contradict what the evaluator observed in evidence surfaces

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
