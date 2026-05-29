# External Audit Command (/audit-work)

## Purpose
To package the current work for one or more external LLM auditors, collect their independent reviews, and return a decision-ready synthesis that tells the user what each auditor said, where auditors agree or conflict, what the Coordinator agrees with, what should change, and what the Coordinator disagrees with.

## Usage
Provide optional controls and an audit focus. The active agent will inspect the current work, build one audit packet, send the same packet independently to one or more external LLM CLIs, and return a structured cross-auditor external-audit report.

## Arguments
- `[controls] [focus]`
- `controls` (optional): `auditors=<claude,gemini,codex|all>`, `auditor=<claude|gemini|codex>`, `min_auditors=<int>`, `allow_same_family=<true|false>`, `reuse_packet=<path>`, `scope=<work-log|current-diff|staged|last-commit>`, `suggest_changes=<patches|notes|none>`, `audit_timeout_seconds=<int>`, `claude_model=<exact-id>`, `gemini_model=<exact-id>`, and/or `codex_model=<exact-id>`
- `focus`: what you want the external auditors to examine most closely

---

**Directive:**
Act as an External Audit Coordinator.

1. Parse `$ARGUMENTS`:
   - Detect optional controls anywhere in args: `auditors=<claude,gemini,codex|all>`, `auditor=<claude|gemini|codex>`, `min_auditors=<int>`, `allow_same_family=<true|false>`, `reuse_packet=<path>`, `scope=<work-log|current-diff|staged|last-commit>`, `suggest_changes=<patches|notes|none>`, `audit_timeout_seconds=<int>`, `claude_model=<exact-id>`, `gemini_model=<exact-id>`, and `codex_model=<exact-id>`.
   - Remaining text is the audit focus.
   - Defaults if omitted: `scope=work-log`; `suggest_changes=patches`; `audit_timeout_seconds=300`; `allow_same_family=false`; `min_auditors=1`; auditor selection is all available different-family external CLIs in deterministic order.
   - If `auditors=` names an explicit list and `min_auditors=` is omitted, set `min_auditors` to the number of requested auditors so missing requested auditors cannot be silently dropped.
   - `auditors=all` is the explicit spelling of the default all-available behavior for scripts. It still excludes the current host family unless `allow_same_family=true`.
   - `reuse_packet=<path>` means rerun a prior packet, usually for failed auditors. Do not rebuild or reframe the packet when this is set; verify the path exists and use it as the canonical packet.
2. Load `<AI_DEV_SHOP_ROOT>/skills/external-audit/SKILL.md`.
3. Also use `skills/llm-operations/references/peer-llm-dispatch.md` for shared packet, transport, diagnostics, and capability rules.
   - If any planned auditor is Claude, also use `skills/llm-operations/references/claude-code-cli-audits.md`.
   - Treat native Windows shells as unverified for this command. The dispatch-path strategy is OS-agnostic, but the command examples and probe flow assume a Bash-compatible shell unless adapted to PowerShell.
4. Inspect the current work surface before dispatching:
   - use the current session context plus repo evidence (`git status --short`, touched files, relevant file diffs, and when needed `git log -1 --stat`)
   - separate in-scope work from unrelated worktree changes
   - build a concrete work log of what was changed, why, what was verified, and what remains uncertain
   - default to the curated work log as the main packet payload; include commit or diff references only when they materially help the auditor inspect details
   - determine whether the packet names a bounded enough file set for grounded file-change suggestions; if `suggest_changes=patches` but the scope is too broad or uncertain for safe file-level proposals, downgrade to `suggest_changes=notes` and say so before dispatch
5. Build an audit packet using `skills/external-audit/references/audit-packet-template.md`.
   - If `reuse_packet=<path>` is set, skip packet construction and use that existing packet as the canonical authoring packet.
   - Save packets to `<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/external-audit/packets/<timestamp>-audit-packet.md` by default.
   - If the user explicitly asks to retain the packet, save it to `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/external-audit/packets/` instead.
   - Record the effective `suggest_changes` mode in the packet.
   - Prefer serving the packet to the peer as a self-contained `stdin` payload when the bounded work log fits cleanly in one prompt.
   - If the peer still needs to read the packet from disk, follow the shared transport fallback rules in `skills/llm-operations/references/peer-llm-dispatch.md` and record both the authoring and dispatch paths in the packet.
6. Run external-auditor preflight:
   - detect which peer CLIs (`claude`, `gemini`, `codex`) are installed
   - prefer a different model family from the current host
   - if `auditors=` is provided, expand that explicit set; `auditors=all` means all installed peer CLIs, still excluding the current host family unless `allow_same_family=true`
   - if an explicit auditor list names the current host family, treat that as an explicit same-family request for that auditor and say that independence is weaker
   - if legacy `auditor=` is provided, run exactly that one auditor
   - if neither is provided, filter out the current host family unless `allow_same_family=true` and choose all available external CLIs in this exact order: `claude`, `gemini`, `codex`
   - if fewer than `min_auditors` are available, stop and tell the user which auditors were available, unavailable, or excluded
   - if no different-family external CLI is available, stop and tell the user instead of silently using the same family
   - resolve each planned auditor model only by: per-run override naming an exact model/version, saved pinned preference naming an exact model/version, or local CLI/config proof of the exact model/version
7. For each planned Claude auditor, first check whether the exact requested model already succeeded earlier in the current session on this same host/CLI. If yes, treat that as `session_success` proof and reuse it directly. Do not rerun discovery just because the cache file is absent.
8. For each planned Claude auditor where the requested or saved Claude model is still unproven after the session-success check, or it is rejected by the CLI, do not keep guessing manually. Run `python3 skills/swarm-consensus/scripts/cli_smoke_test.py --discover-claude --claude-model <requested-or-saved-model> --claude-require both --output-format json` first.
   - A valid Claude proof is an exact environment cache hit with a real artifact path, an exact-model `session_success` earlier in the current session on the same host/CLI, or a fresh discovery run that writes a new artifact.
   - If discovery finds a working exact Claude model in the same requested family/version, use it and continue.
   - If discovery finds only a different family/version, stop and ask the user before switching.
9. If any planned exact auditor model/version is not explicitly pinned or locally proven, stop and print a model-pinning gate:
   `Planned auditors: <CLI=model-or-unproven list>. Exact model/version is not proven for: <CLI list>. Reply with auditors=... and claude_model=..., gemini_model=..., or codex_model=... using exact model name/version(s) to proceed.`
10. If every planned exact auditor model/version is explicit or locally proven, dispatch the audit prompt to each planned auditor independently.
   - every auditor gets the same canonical packet
   - auditors must not see each other's answers before responding
   - construct every auditor prompt from the canonical packet before dispatching the first auditor; if dispatch must be sequential, do not revise, reframe, or add emphasis to later prompts based on earlier auditor responses
   - run peer calls in parallel when practical; otherwise run sequentially but keep the prompts independent
   - do not hand `<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/` paths directly to the peer when file-based reads are required; use the shared transport fallback rules from `skills/llm-operations/references/peer-llm-dispatch.md`
   - run a cheap readability probe first when using file-based transport: ask the peer to read the dispatch packet and echo the first Markdown heading
   - require the auditor to begin with an `Auditor Scope Check` that states what it believes it is auditing, the scope and target it used, which files or artifacts it reviewed, and any mismatch or uncertainty it noticed before giving findings
   - prefer a short prompt that points to the dispatch packet over embedding the full packet body inline when the peer can read files directly
   - if the packet already names the relevant files, prefer a bounded sectioned prompt over an open-ended repo-audit prompt
   - if an auditor is Claude, apply the Claude Code reference and prefer its dedicated runner when available
   - when `suggest_changes=notes`, ask for file-level change suggestions in prose or snippets only
   - when `suggest_changes=patches`, ask for file-level change suggestions plus candidate unified diffs or bounded replacement snippets only for files the auditor actually reviewed; if the scope is too uncertain for safe patch proposals, require the auditor to fall back to notes and say why
   - never ask auditors to apply edits; suggested changes are proposal-only artifacts
   - Prefer structured output modes when available.
   - Parse `stdout` only as each auditor answer.
   - Treat `stderr` as diagnostics.
   - Save raw stdout/stderr captures to `<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/external-audit/offloads/<timestamp>/<auditor>/` by default.
   - Retry transient failures like `429` and `503` within `audit_timeout_seconds`, with at most 2 retries.
   - only classify `empty_result_transport_failure` after the peer process exits successfully and stdout is still empty
   - use any host-specific live-run timing or fallback bounds from the host reference you loaded
   - if the peer exits successfully but returns an empty answer body, classify it as `empty_result_transport_failure` and retry once with a tighter bounded prompt and constrained read-only tool surface when supported
   - when file-based dispatch was used, delete the temporary dispatch copy after the run unless the user explicitly asks to retain it for debugging or evidence
   - if all planned auditors fail, stop and report the failure matrix instead of synthesizing findings
   - if some auditors fail and successful respondents are fewer than `min_auditors`, stop and ask whether to retry failed auditors using `reuse_packet=<path>`, proceed with degraded coverage, or abort
   - if some auditors fail but successful respondents still meet `min_auditors`, proceed only with a prominent `Degraded Coverage` note and a decision point to rerun failed auditors from the same packet
11. If any auditor returned suggested changes, save them as proposal artifacts using `skills/external-audit/references/proposed-fixes-template.md`.
   - Default save path: `<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/external-audit/proposed-fixes/<timestamp>/`
   - Retained save path only when the user explicitly asks: `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/external-audit/proposed-fixes/<timestamp>/`
   - Always save the raw extracted proposal bundle to `proposed-fixes.md`, grouped by auditor.
   - If an auditor returned grounded unified diffs, split them into `patches/<auditor>-<nnnn>-<slug>.diff` files when practical; otherwise keep them inline in `proposed-fixes.md`.
   - Treat these artifacts as suggestions only. Do not apply them automatically.
12. Synthesize the result back to the user. The final answer must include:
   - the exact report structure from `skills/external-audit/references/external-audit-report-template.md`
   - the exact auditor model version used (`Resolved Model`) and the auditor CLI version for each planned auditor
   - the effective `suggest_changes` mode used
   - `Work Log`
   - `Auditor Matrix`
   - `Degraded Coverage` when any planned auditor failed, was skipped, or did not review the target scope
   - `Per-Auditor Scope Checks`
   - `What The External LLMs Said`
   - `Cross-Auditor Synthesis`
   - `Suggested Changes By Auditor`
   - `Coordinator Response -> Agree`
   - `Coordinator Response -> Change`
   - `Coordinator Response -> Disagree`
   - `Coordinator Response -> Proposed Fix Handling`
   - `Audit Outcome`
   - `Decision Points For User`
   - if any exact model version cannot be proven, do not run the audit; ask for pinned model(s) instead
   - if two or more auditors independently converge on the same finding, do not dismiss it in `Disagree` without making it a `Decision Points For User` item and explaining the evidence required to override it
13. Before writing the final report, if the user has not already specified retention, ask:
   `Save external audit report? Reply "save report" to retain it in <ADS_PROJECT_KNOWLEDGE_ROOT>/reports/external-audit/runs/, "local only" to keep it in <ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/external-audit/runs/, or "inline only" for no file.`
   Save ad hoc reports to `<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/external-audit/runs/<timestamp>-external-audit-report.md` by default. If the user explicitly wants to retain the artifact, save it to `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/external-audit/runs/<timestamp>-external-audit-report.md` instead.
   - Suggested-change bundles remain in `.local-artifacts` by default even when the report is saved, unless the user explicitly asks to retain the proposed fixes too.
