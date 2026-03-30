# External Audit Command (/audit-work)

## Purpose
To package the current work for one external LLM auditor, collect its review, and return a decision-ready synthesis that tells the user what the auditor said, what the Coordinator agrees with, what should change, and what the Coordinator disagrees with.

## Usage
Provide optional controls and an audit focus. The active agent will inspect the current work, build an audit packet, send it to one external LLM CLI, and return a structured external-audit report.

## Arguments
- `[controls] [focus]`
- `controls` (optional): `auditor=<claude|gemini|codex>`, `scope=<work-log|current-diff|staged|last-commit>`, `audit_timeout_seconds=<int>`, `claude_model=<exact-id>`, `gemini_model=<exact-id>`, and/or `codex_model=<exact-id>`
- `focus`: what you want the external auditor to examine most closely

---

**Directive:**
Act as an External Audit Coordinator.

1. Parse `$ARGUMENTS`:
   - Detect optional controls anywhere in args: `auditor=<claude|gemini|codex>`, `scope=<work-log|current-diff|staged|last-commit>`, `audit_timeout_seconds=<int>`, `claude_model=<exact-id>`, `gemini_model=<exact-id>`, and `codex_model=<exact-id>`.
   - Remaining text is the audit focus.
   - Defaults if omitted: `scope=work-log`; `audit_timeout_seconds=300`.
2. Load `<AI_DEV_SHOP_ROOT>/skills/external-audit/SKILL.md`.
3. Also use `skills/llm-operations/references/peer-llm-dispatch.md` for shared packet, transport, diagnostics, and capability rules.
   - If the planned auditor is Claude, also use `skills/llm-operations/references/claude-code-cli-audits.md`.
   - Treat native Windows shells as unverified for this command. The dispatch-path strategy is OS-agnostic, but the command examples and probe flow assume a Bash-compatible shell unless adapted to PowerShell.
4. Inspect the current work surface before dispatching:
   - use the current session context plus repo evidence (`git status --short`, touched files, relevant file diffs, and when needed `git log -1 --stat`)
   - separate in-scope work from unrelated worktree changes
   - build a concrete work log of what was changed, why, what was verified, and what remains uncertain
   - default to the curated work log as the main packet payload; include commit or diff references only when they materially help the auditor inspect details
5. Build an audit packet using `skills/external-audit/references/audit-packet-template.md`.
   - Save packets to `<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/external-audit/packets/<timestamp>-audit-packet.md` by default.
   - If the user explicitly asks to retain the packet, save it to `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/external-audit/packets/` instead.
   - Prefer serving the packet to the peer as a self-contained `stdin` payload when the bounded work log fits cleanly in one prompt.
   - If the peer still needs to read the packet from disk, follow the shared transport fallback rules in `skills/llm-operations/references/peer-llm-dispatch.md` and record both the authoring and dispatch paths in the packet.
6. Run external-auditor preflight:
   - detect which peer CLIs (`claude`, `gemini`, `codex`) are installed
   - prefer a different model family from the current host
   - if `auditor=` is omitted, filter out the current host family and choose the first available CLI in this exact order: `claude`, `gemini`, `codex`
   - if no different-family external CLI is available, stop and tell the user instead of silently using the same family
   - resolve the planned model only by: per-run override naming an exact model/version, saved pinned preference naming an exact model/version, or local CLI/config proof of the exact model/version
7. If the planned auditor is Claude and the requested or saved Claude model is unproven or rejected, do not keep guessing manually. Run `python3 skills/swarm-consensus/scripts/cli_smoke_test.py --discover-claude --claude-model <requested-or-saved-model> --claude-require both --output-format json` first.
   - A valid Claude proof is either an exact environment cache hit from `<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/swarm-consensus/smoke-tests/last-known-good.json` with a real artifact path, or a fresh discovery run that writes a new artifact.
   - If discovery finds a working exact Claude model in the same requested family/version, use it and continue.
   - If discovery finds only a different family/version, stop and ask the user before switching.
8. If the exact auditor model/version is not explicitly pinned or locally proven, stop and print a model-pinning gate:
   `Planned auditor CLI: <CLI>. Exact model/version is not proven locally. Reply with auditor=... and claude_model=..., gemini_model=..., or codex_model=... using an exact model name/version to proceed.`
9. If the exact auditor model/version is explicit or locally proven, dispatch the audit prompt.
   - do not hand `<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/` paths directly to the peer when file-based reads are required; use the shared transport fallback rules from `skills/llm-operations/references/peer-llm-dispatch.md`
   - run a cheap readability probe first when using file-based transport: ask the peer to read the dispatch packet and echo the first Markdown heading
   - require the auditor to begin with an `Auditor Scope Check` that states what it believes it is auditing, the scope and target it used, which files or artifacts it reviewed, and any mismatch or uncertainty it noticed before giving findings
   - prefer a short prompt that points to the dispatch packet over embedding the full packet body inline when the peer can read files directly
   - if the packet already names the relevant files, prefer a bounded sectioned prompt over an open-ended repo-audit prompt
   - if the auditor is Claude, apply the Claude Code reference and prefer its dedicated runner when available
   - Prefer structured output modes when available.
   - Parse `stdout` only as the auditor answer.
   - Treat `stderr` as diagnostics.
   - Save raw stdout/stderr captures to `<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/external-audit/offloads/` by default.
   - Retry transient failures like `429` and `503` within `audit_timeout_seconds`, with at most 2 retries.
   - only classify `empty_result_transport_failure` after the peer process exits successfully and stdout is still empty
   - use any host-specific live-run timing or fallback bounds from the host reference you loaded
   - if the peer exits successfully but returns an empty answer body, classify it as `empty_result_transport_failure` and retry once with a tighter bounded prompt and constrained read-only tool surface when supported
   - when file-based dispatch was used, delete the temporary dispatch copy after the run unless the user explicitly asks to retain it for debugging or evidence
10. Synthesize the result back to the user. The final answer must include:
   - the exact report structure from `skills/external-audit/references/external-audit-report-template.md`
   - the exact auditor model version used (`Resolved Model`) and the auditor CLI version
   - `Work Log`
   - `Auditor Scope Check`
   - `What The External LLM Said`
   - `Coordinator Response -> Agree`
   - `Coordinator Response -> Change`
   - `Coordinator Response -> Disagree`
   - `Audit Outcome`
   - `Decision Points For User`
   - if the exact model version cannot be proven, do not run the audit; ask for a pinned model instead
11. Before writing the final report, if the user has not already specified retention, ask:
   `Save external audit report? Reply "save report" to retain it in <ADS_PROJECT_KNOWLEDGE_ROOT>/reports/external-audit/runs/, "local only" to keep it in <ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/external-audit/runs/, or "inline only" for no file.`
   Save ad hoc reports to `<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/external-audit/runs/<timestamp>-external-audit-report.md` by default. If the user explicitly wants to retain the artifact, save it to `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/external-audit/runs/<timestamp>-external-audit-report.md` instead.
