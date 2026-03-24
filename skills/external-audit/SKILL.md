---
name: external-audit
version: 1.1.0
last_updated: 2026-03-24
description: Package the current work for one external LLM auditor, capture its review, and return a decision-ready synthesis to the user.
---

# Skill: External Audit

**This skill is OFF by default.** Use it only when the user explicitly asks for another LLM to audit, check, or review the current work.

## When to Use

- User asks to have another LLM check your work
- A toolkit-maintenance change needs independent scrutiny before the user decides whether to keep it
- You want one external model to review a diff, a commit, or a bounded workstream and then compare its feedback against your own judgment

## Scope

This is not the same as pipeline `/code-review`, which routes implementation to the Code Review Agent and Security Agent.

This skill is for:
- one external auditor CLI
- one packaged audit packet
- one synthesis back to the user with explicit agreement and disagreement

This workflow is **packet-first**. Default to a curated work-log packet, not a blind diff against the last push.
Use `skills/llm-operations/references/peer-llm-dispatch.md` for shared packet, transport, diagnostics, and capability rules.

## Auditor Selection Rules

- Prefer a different model family from the current host.
- Do not use a same-family child/subagent as the external auditor by default.
- If the user explicitly wants same-family review, say so clearly and note that it is weaker independence.
- Never hallucinate an auditor response. If no external CLI is available, stop and say so.
- When `auditor=` is omitted, filter out the current host family by default, then choose the first available CLI in this exact order: `claude`, `gemini`, `codex`.
- If no different-family external CLI is available, stop and tell the user instead of silently falling back to the same family. Only use a same-family auditor when the user explicitly asks for it.

## Runtime Controls

- `auditor=<claude|gemini|codex>`: choose the external auditor CLI explicitly
- `scope=<work-log|current-diff|staged|last-commit>`: choose the default work surface
- `audit_timeout_seconds=<int>`: maximum wall-clock wait for the auditor call (default `300`)
- `claude_model=<id>`: per-run Claude model override
- `gemini_model=<id>`: per-run Gemini model override
- `codex_model=<id>`: per-run Codex model override

If controls are omitted, infer the smallest safe default and tell the user what was chosen before dispatch.

## Step 1 — Preflight

Before building the packet, inspect the external CLI surface:

```bash
which claude && claude --version 2>/dev/null || echo "claude: not installed"
which gemini && gemini --version 2>/dev/null || echo "gemini: not installed"
which codex  && codex  --version 2>/dev/null || echo "codex: not installed"
```

Then:

1. Record which external CLIs are available.
2. Exclude the current host family unless the user explicitly asks to use it anyway.
3. If `auditor=` is omitted, choose the planned auditor using the deterministic fallback order from `## Auditor Selection Rules`.
4. Resolve the planned auditor model using this order:
   - per-run override
   - saved user preference
   - local CLI default
   - alias assumption
5. If the exact planned model is inferred rather than explicitly pinned or proven, stop before dispatch and ask:

`Planned auditor: <CLI>=<resolved-or-inferred>. Reply with "run" to proceed or override with auditor=..., claude_model=..., gemini_model=..., codex_model=....`

Do not silently switch to a newer model family/version just because it exists locally.

## Step 2 — Build The Audit Packet

Use `skills/external-audit/references/audit-packet-template.md` as the layout reference.

The packet must capture:

- the original user request
- the exact scope under review
- the audit target reference (commit, diff, or explicit file set)
- what you changed
- why you changed it
- relevant files and artifacts
- tests/verification performed
- tests/verification not performed
- known risks, caveats, and open questions
- any unrelated worktree changes excluded from the audit scope
- the specific questions you want the external auditor to answer

Default behavior:

- `scope=work-log` is the default
- build the packet from the coordinator's work log plus the touched-file list and verification notes
- attach commit or diff references only when they materially help the auditor inspect details
- do not default to `origin/main..HEAD`, `last push`, or another broad diff unless the user explicitly asks for that view

Default packet path:

` .local-artifacts/external-audit/packets/<timestamp>-audit-packet.md `

If the user explicitly wants the packet retained as project evidence, save it instead at:

` reports/external-audit/packets/<timestamp>-audit-packet.md `

Packets are scratch by default unless the user explicitly asks to retain them.

## Step 3 — Dispatch The External Auditor

Prompt the external auditor to review the packet, not just the bare diff summary.

Before asking a peer to read a packet from disk, confirm that the packet path is peer-readable. If the authoring packet lives under `.local-artifacts/` or another path the peer cannot access, create a dispatch copy in a peer-readable workspace or host temp directory and retry once with that corrected path. Use `skills/llm-operations/references/peer-llm-dispatch.md` for the rule set.

Audit prompt requirements:

1. State that this is an independent audit of the packaged work.
2. Ask for findings ordered by severity.
3. Ask for file references when possible.
4. Ask which issues are real blockers vs optional improvements.
5. Ask for a short strengths section so the user sees what the auditor thinks is solid.

Prefer structured output when the CLI supports it.

- Parse `stdout` only as the auditor answer.
- Treat `stderr` as diagnostics.
- Save raw stdout/stderr captures to `.local-artifacts/external-audit/offloads/` by default.
- Only retain raw offloads in `reports/offloads/` if the user explicitly asks for retained evidence.

Retry policy:

- Retry clear transient failures such as `429`, `503`, rate-limit, or provider-capacity messages.
- Use bounded backoff.
- Stop after at most 2 retries.
- Never exceed `audit_timeout_seconds`.

## Step 4 — Synthesize Back To The User

Your final answer must not stop at "here is what the auditor said."

You must add your own judgment in separate sections:

- what the external auditor said
- what you agree with
- what you think should change
- what you disagree with and why
- what decision the user needs to make next

If the auditor is wrong, say so plainly and explain why using inspected evidence.
If the auditor is right, say what you would change and whether you should patch it now.

## Step 5 — Output

### Template Guard

1. Use the section order below for inline output and saved reports.
2. Do not collapse the external audit into a prose blob.
3. Before writing the final report to disk, if the user has not already specified retention, ask:

`Save external audit report? Reply "save report" to retain it in reports/external-audit/runs/, "local only" to keep it in .local-artifacts/external-audit/runs/, or "inline only" for no file.`

4. Default saved location for ad hoc runs:

` .local-artifacts/external-audit/runs/<timestamp>-external-audit-report.md `

5. Retained location when the user explicitly wants to keep it:

` reports/external-audit/runs/<timestamp>-external-audit-report.md `

Use this structure:

```markdown
# External Audit Report

**Date:** <ISO-8601>
**Scope:** <work-log | current-diff | staged | last-commit | custom>
**Focus:** <the user's audit question>
**Audit Packet:** <path>
**Dispatch Packet:** <peer-readable path or "same as audit packet">
**Auditor CLI:** <claude | gemini | codex>
**Requested Model:** <requested or "n/a">
**Resolved Model:** <resolved or "unknown">
**Selection Source:** <per_run_override | saved_preference | local_default | alias_assumption | unknown>
**CLI Version:** <version>
**Timeout:** <seconds>

## Work Log
- <what you did>
- <why>
- <verification run or not run>

## Auditor Diagnostics
| Field | Value |
|---|---|
| Output mode | <json | text> |
| stdout parser | <field or end marker> |
| stderr summary | <short summary> |
| Attempts | <count> |
| Final status | <Responded | Failed | Timed out | Retry exhausted | Not installed> |

## External Auditor Findings
<succinct but faithful summary of what the external auditor said>

## Coordinator Response

### Agree
<what you agree with and why>

### Change
<what you think should change as a result>

### Disagree
<what you disagree with and why>

## Decision Points For User
- <keep as-is / patch now / save retained report / request a second auditor / etc.>
```
