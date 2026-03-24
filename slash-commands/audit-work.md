# External Audit Command (/audit-work)

## Purpose
To package the current work for one external LLM auditor, collect its review, and return a decision-ready synthesis that tells the user what the auditor said, what the Coordinator agrees with, what should change, and what the Coordinator disagrees with.

## Usage
Provide optional controls and an audit focus. The active agent will inspect the current work, build an audit packet, send it to one external LLM CLI, and return a structured external-audit report.

## Arguments
- `[controls] [focus]`
- `controls` (optional): `auditor=<claude|gemini|codex>`, `scope=<current-diff|staged|last-commit>`, `audit_timeout_seconds=<int>`, `claude_model=<id>`, `gemini_model=<id>`, and/or `codex_model=<id>`
- `focus`: what you want the external auditor to examine most closely

---

**Directive:**
Act as an External Audit Coordinator.

1. Parse `$ARGUMENTS`:
   - Detect optional controls anywhere in args: `auditor=<claude|gemini|codex>`, `scope=<current-diff|staged|last-commit>`, `audit_timeout_seconds=<int>`, `claude_model=<id>`, `gemini_model=<id>`, and `codex_model=<id>`.
   - Remaining text is the audit focus.
   - Defaults if omitted: `scope=current-diff` when the current worktree has in-scope edits, otherwise `scope=last-commit`; `audit_timeout_seconds=300`.
2. Load `<AI_DEV_SHOP_ROOT>/skills/external-audit/SKILL.md`.
3. Inspect the current work surface before dispatching:
   - use the current session context plus repo evidence (`git status --short`, `git diff --stat`, relevant file diffs, and when needed `git log -1 --stat`)
   - separate in-scope work from unrelated worktree changes
   - build a concrete work log of what was changed, why, what was verified, and what remains uncertain
4. Build an audit packet using `skills/external-audit/references/audit-packet-template.md`.
   - Save packets to `.local-artifacts/external-audit/packets/<timestamp>-audit-packet.md` by default.
   - If the user explicitly asks to retain the packet, save it to `reports/external-audit/packets/` instead.
5. Run external-auditor preflight:
   - detect which peer CLIs (`claude`, `gemini`, `codex`) are installed
   - prefer a different model family from the current host
   - if `auditor=` is omitted, choose the safest available external auditor and state that choice
   - resolve the planned model using the same policy as Swarm Consensus: per-run override, saved preference, local default, then alias assumption
6. If the exact auditor model is inferred instead of explicitly pinned or proven, stop and print a confirmation gate:
   `Planned auditor: <CLI>=<resolved-or-inferred>. Reply with "run" to proceed or override with auditor=..., claude_model=..., gemini_model=..., codex_model=....`
7. If the auditor is explicit or the user confirms, dispatch the audit prompt.
   - Prefer structured output modes when available.
   - Parse `stdout` only as the auditor answer.
   - Treat `stderr` as diagnostics.
   - Save raw stdout/stderr captures to `.local-artifacts/external-audit/offloads/` by default.
   - Retry transient failures like `429` and `503` within `audit_timeout_seconds`, with at most 2 retries.
8. Synthesize the result back to the user. The final answer must include:
   - `Work Log`
   - `External Auditor Findings`
   - `Coordinator Response -> Agree`
   - `Coordinator Response -> Change`
   - `Coordinator Response -> Disagree`
   - `Decision Points For User`
9. Before writing the final report, if the user has not already specified retention, ask:
   `Save external audit report? Reply "save report" to retain it in reports/external-audit/runs/, "local only" to keep it in .local-artifacts/external-audit/runs/, or "inline only" for no file.`
   Save ad hoc reports to `.local-artifacts/external-audit/runs/<timestamp>-external-audit-report.md` by default. If the user explicitly wants to retain the artifact, save it to `reports/external-audit/runs/<timestamp>-external-audit-report.md` instead.
