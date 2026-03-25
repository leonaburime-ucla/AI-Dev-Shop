---
name: external-audit
version: 1.1.7
last_updated: 2026-03-25
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
If the planned auditor is Claude, also use `skills/llm-operations/references/claude-code-cli-audits.md`.

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
- `claude_model=<exact-id>`: per-run Claude model override with an exact model name/version
- `gemini_model=<exact-id>`: per-run Gemini model override with an exact model name/version
- `codex_model=<exact-id>`: per-run Codex model override with an exact model name/version

If controls are omitted, infer only non-model defaults and tell the user what was chosen before dispatch. Do not infer an exact auditor model name/version unless it is locally proven.

## Step 1 — Preflight

Native Windows shells are not yet verified for this workflow. The path strategy is OS-agnostic, but the command examples in this skill assume a Bash-compatible shell. On Windows, prefer Git Bash or WSL for now, or translate the shell snippets to PowerShell equivalents before relying on them.

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
   - per-run override naming an exact model/version
   - saved user preference naming an exact model/version
   - local CLI or config evidence that proves the exact model/version
5. If the exact planned model/version is not explicitly pinned or locally proven, stop before dispatch and ask:

`Planned auditor CLI: <CLI>. Exact model/version is not proven locally. Reply with auditor=... and claude_model=..., gemini_model=..., or codex_model=... using an exact model name/version to proceed.`

Do not silently switch to a newer model family/version just because it exists locally.
Do not dispatch using a local default, alias assumption, or inferred family name when this workflow promises exact model reporting.

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

Default dispatch copy path for peer-readable runs:

` framework/reports/external-audit/dispatch/<timestamp>-audit-packet.md `

If the user explicitly wants the packet retained as project evidence, save it instead at:

` framework/reports/external-audit/packets/<timestamp>-audit-packet.md `

Packets are scratch by default unless the user explicitly asks to retain them.

## Step 3 — Dispatch The External Auditor

Prompt the external auditor to review the packet, not just the bare diff summary.

Use `skills/llm-operations/references/peer-llm-dispatch.md` for the rule set.

Dispatch workflow:

1. Keep the authoring packet in `.local-artifacts/` or `framework/reports/` according to the user's retention choice.
2. If the peer needs to read a packet from disk, create a peer-readable dispatch copy first. For ad hoc local runs, default to `framework/reports/external-audit/dispatch/<timestamp>-audit-packet.md`.
3. Probe readability before the full audit call by asking the peer to read the dispatch packet and echo the first Markdown heading.
4. If the probe fails because the path is ignored, unreadable, or outside the peer workspace, classify it as `path_or_permission_failure`, move the dispatch copy, and retry once.
5. Use the dispatch packet path, not the authoring packet path, in the actual audit prompt.
6. Delete the temporary dispatch copy after the audit finishes unless the user explicitly asks to retain it for debugging or evidence.
7. If the auditor CLI is Claude, apply `skills/llm-operations/references/claude-code-cli-audits.md` and prefer its dedicated runner when available.

Audit prompt requirements:

1. State that this is an independent audit of the packaged work.
2. Ask for findings ordered by severity.
3. Ask for file references when possible.
4. Ask which issues are real blockers vs optional improvements.
5. Ask for a short strengths section so the user sees what the auditor thinks is solid.
6. Require the auditor to begin with an `Auditor Scope Check` before any findings. That scope check must restate what it believes it is auditing, the active scope and audit target, which files or artifacts it actually reviewed, and any ambiguity or mismatch it noticed.
7. Prefer a short prompt that references the dispatch packet path over embedding the full packet body inline when the peer can read files directly.
8. If the packet already contains a bounded file list, prefer a bounded sectioned prompt over an open-ended repo audit prompt.
9. For Claude Code packet-first audits, prefer a constrained `Read`-only tool surface when that is enough to inspect the packet and the listed files.

Prefer structured output when the CLI supports it.

- Parse `stdout` only as the auditor answer.
- Treat `stderr` as diagnostics.
- Save raw stdout/stderr captures to `.local-artifacts/external-audit/offloads/` by default.
- Only retain raw offloads in `framework/reports/offloads/` if the user explicitly asks for retained evidence.
- Use host-specific references for auditor-specific transport quirks instead of restating them inline.

Retry policy:

- Retry clear transient failures such as `429`, `503`, rate-limit, or provider-capacity messages.
- Only classify `empty_result_transport_failure` after the peer process exits successfully and stdout is still empty.
- On `empty_result_transport_failure`, retry once with a tighter bounded prompt and a constrained read-only tool surface when the peer supports it.
- Use any host-specific retry bounds or fallback guidance from the host reference you loaded.
- Use bounded backoff.
- Stop after at most 2 retries.
- Never exceed `audit_timeout_seconds`.

## Step 4 — Synthesize Back To The User

Your final answer must not stop at "here is what the auditor said."

You must add your own judgment in separate sections:

- what the external auditor said it was auditing
- what the external auditor said
- what you agree with
- what you think should change
- what you disagree with and why
- what decision the user needs to make next

If the auditor is wrong, say so plainly and explain why using inspected evidence.
If the auditor is right, say what you would change and whether you should patch it now.

## Step 5 — Output

### Template Guard

Use `skills/external-audit/references/external-audit-report-template.md` as the reference layout for inline output and saved reports.

1. Use the section order below for inline output and saved reports.
2. Do not collapse the external audit into a prose blob.
3. Before writing the final report to disk, if the user has not already specified retention, ask:

`Save external audit report? Reply "save report" to retain it in framework/reports/external-audit/runs/, "local only" to keep it in .local-artifacts/external-audit/runs/, or "inline only" for no file.`

4. Default saved location for ad hoc runs:

` .local-artifacts/external-audit/runs/<timestamp>-external-audit-report.md `

5. Retained location when the user explicitly wants to keep it:

` framework/reports/external-audit/runs/<timestamp>-external-audit-report.md `

6. The report must explicitly separate:
   - what the external LLM said it was auditing
   - what the external LLM said
   - what you agree with
   - what you would change
   - what you disagree with
   - the resulting audit outcome
7. If the auditor did not respond successfully, keep the same template and state that clearly in `What The External LLM Said` and `Audit Outcome`.
