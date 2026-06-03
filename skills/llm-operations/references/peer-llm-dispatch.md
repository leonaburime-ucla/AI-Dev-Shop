# Peer LLM Dispatch

Use this reference when one LLM is asking another LLM CLI to review, debate, or validate work.

## Default Pattern

- Build a shared packet first.
- Make the packet packet-first and work-log-first.
- Treat raw diffs, commits, or logs as supporting evidence, not the default payload.
- Prefer delivering a self-contained packet via `stdin` when the peer does not need repo file reads and the payload fits cleanly in one bounded request.
- Use file-based dispatch only when the peer must inspect repo files directly or the packet would become too large or brittle to inline safely.

For most toolkit-maintenance work, the packet should lead with:

1. what changed
2. why it changed
3. exact files touched
4. what was verified
5. what was not verified
6. out-of-scope local changes
7. the exact question for the external LLM

Use commit or diff references only when they materially help the auditor inspect details.

## Heavier Repo Workloads

Treat this as guidance, not a hard constraint:

- Prefer packet-first prompts plus an explicit file list before escalating to open-ended repo exploration.
- If a peer stalls, returns empty output, or behaves inconsistently on a broad repo-audit prompt, retry once with the same packet and a bounded file set.
- If the packet already names the relevant files, prefer a bounded prompt and a constrained read-only tool surface over a broad open-ended repo-audit prompt.
- Do not assume a failure on an open-ended repo audit means the peer cannot handle repo work in general; first test whether the bounded version succeeds.

## Session Reuse

Some peer CLIs perform expensive startup work (reading project docs, running bootstrap sequences) on the first turn. To avoid paying this cost repeatedly within a single workflow (e.g., a `/cowork` run with diagnosis → verification → correction phases), reuse the same peer session across phases.

### Codex Peer Dispatch

Codex reads repo instruction files (AGENTS.md, `.rules`) and performs mandatory startup on the first turn of every new session unless `--ignore-rules` is used. The AGENTS.md Mandatory Startup section explicitly excludes peer/subagent contexts.

**Two modes:**

#### Single-shot dispatch (default for `/debate`, `/consensus`, `/audit-work`)

Use `--ignore-rules --ephemeral` for one-off prompts where no session continuity is needed:

```bash
codex exec --ignore-rules --ephemeral --json -C "$REPO" "Your task..." \
  > "$RUN_DIR/codex-output.json" 2>"$RUN_DIR/codex-output.stderr"
```

#### Multi-phase dispatch (for `/cowork` with diagnosis → correction)

Omit `--ephemeral` when you need session reuse across phases. Use `--ignore-rules` alone to prevent startup loops while preserving session persistence:

```bash
# Phase 1 — first dispatch, captures session ID
codex exec --ignore-rules --json -C "$REPO" "Your task..." \
  > "$RUN_DIR/codex-phase1.json" 2>"$RUN_DIR/codex-phase1.stderr"

# Extract session ID from JSON stream
SESSION_ID=$(python3 -c "
import json, sys
for line in open('$RUN_DIR/codex-phase1.json'):
    try:
        obj = json.loads(line.strip())
        if obj.get('type') == 'thread.started':
            print(obj['thread_id']); break
    except: pass
")

# Phase 2+ — resume existing session
codex exec resume "$SESSION_ID" --json "Next task..." \
  > "$RUN_DIR/codex-phase2.json" 2>"$RUN_DIR/codex-phase2.stderr"
```

**Rules:**
- Capture `thread_id` from the `thread.started` JSON event on the first dispatch.
- Store the session ID in the run folder for the duration of the workflow.
- All subsequent dispatches to the same Codex peer use `codex exec resume <SESSION_ID>`.
- The resumed session retains full context from prior turns — no need to re-send the context packet.
- If `resume` fails (e.g., session expired or corrupted), classify as `malformed_or_no_output` and start a fresh session.
- Session reuse is scoped to one workflow run. Do not reuse Codex sessions across different `/cowork`, `/consensus`, or `/audit-work` runs.

### Gemini Session Reuse

Gemini CLI in headless mode (`-p`) does not perform expensive startup (it prioritizes the prompt over project docs). Session reuse is not required for Gemini but is available via `--resume latest` or `--resume <index>` if multi-turn dispatch is needed.

### Claude CLI Session Reuse

Claude Code CLI sessions are managed by the host process. When Claude is the primary (not a peer), session continuity is automatic. When Claude is dispatched as a peer via `claude -p`, each invocation is stateless — reuse is not currently supported in headless mode.

## Transport Rules

- Prefer structured output modes when the peer CLI supports them.
- Parse `stdout` only as the peer answer.
- Treat `stderr` as diagnostics and save it separately.
- Keep raw offloads in local scratch by default unless the user explicitly wants retained evidence.
- Do not treat zero-byte redirected offload files from an in-flight peer process as a failure signal by themselves. Some peers, including Claude Code in this repo's packet-audit pattern, may buffer output until process exit.
- Prefer `stdin` or another self-contained prompt transport before asking the peer to read a packet from disk.
- If the peer must read a packet from disk, make sure the packet lives in a peer-readable location.
- Prefer a short prompt that points the peer at the packet path over inlining the full packet body into a shell argument when a peer-readable file is available.
- When invoking peer CLIs from shell, avoid nested heredocs, large command substitutions, or other brittle quoting patterns for long prompts. Prefer a small stable prompt string or a prompt file.
- If a host-sensitive peer flow has a dedicated local runner script, prefer that script over rebuilding the shell wrapper ad hoc each time.
- If the peer is Claude Code CLI, also use `<AI_DEV_SHOP_ROOT>/skills/llm-operations/references/claude-code-cli-audits.md` for host-specific transport quirks, timing behavior, and runner guidance.
- The dispatch-copy pattern is intended to be cross-platform, but it is not yet verified on native Windows shells in this repo. Current shell examples assume a Bash-compatible environment.

## User-Facing Dispatch Brief

Before asking the user to approve a peer dispatch, show a compact brief rather
than dumping the full packet inline by default. The packet file remains the
exact source of truth and must be linked or named so the user can inspect it.

The brief should include:

1. **Planned peers** — model names first; CLI versions are diagnostics only.
2. **Current positions** — one short line per participant when prior peer
   positions exist.
3. **Reasoning summary** — the strongest 2-4 reasons, disagreements, or risks.
4. **Next ask** — the exact question this dispatch asks the peers to answer.
5. **Run meaning** — what replying `run` will execute.

For debate rebuttal rounds, the brief must make the next-round ask explicit:
what positions are being challenged, which disagreements matter, and what
evidence or assumption change the peers should address. Do not require the user
to read a long terminal-rendered prompt to understand why the next dispatch is
happening.

### Reporting Peer Results to the User

When reporting results, synthesis, decision ledgers, or any peer output back to
the user, identify each participant by **model family + version + reasoning
mode** — not by CLI name or generic family alone.

Correct examples:
- `Gemini 3.1 Pro` (not "Gemini" or "gemini-cli")
- `Codex GPT-5.5 xhigh` (not "Codex" or "codex-cli")
- `Claude Opus 4.6` (not "Claude" or "claude-cli")

If the peer session reports its own identity (e.g., Codex session header shows
`model: gpt-5.5`), use that. If reasoning effort is known (e.g., `xhigh`,
`high`), include it. The user must always know exactly which model and tier
produced which output.

### Peer-Readable Packet Locations

This section is the source of truth for the temporary dispatch fallback location. Do not duplicate the exact fallback path across workflow docs unless a tool-specific runner requires it.

Do not assume every peer CLI can read every local path.

- Ignored repo paths such as `<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/` may be invisible to some tool layers.
- Generic OS temp paths such as `/tmp` may be outside the peer's allowed workspace.
- Default pattern:
  - write the authoring packet to `<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/`
  - if the peer can be served with a self-contained `stdin` payload, use that instead of any file path
  - if the peer can read the authoring path and still needs file-based transport, use it directly
  - if the peer cannot read it because the path is ignored, unreadable, or out of workspace, tell the user briefly and create a temporary peer-readable dispatch copy under `<ADS_PROJECT_KNOWLEDGE_ROOT>/tmp/peer-dispatch/<workflow>/`
  - give the peer the dispatch copy path, not the authoring path
- If needed, create a dispatch copy inside:
  - `<ADS_PROJECT_KNOWLEDGE_ROOT>/tmp/peer-dispatch/<workflow>/` inside the workspace root for local-only runs, or
  - `<AI_DEV_SHOP_ROOT>/tmp/peer-dispatch/<workflow>/` when the toolkit is a subfolder install and `<ADS_PROJECT_KNOWLEDGE_ROOT>` is a sibling path outside the peer CLI's allowed workspace,
  - a retained `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/...` path only when the user explicitly wants a repo-kept artifact or the workflow itself is already being retained
- Do not put the dispatch copy under a gitignored or tool-ignored path if the peer needs to read it with file tools.
- Do not promote a local-only packet into `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/` just to satisfy peer readability. Use the workspace `tmp/` fallback first.

If the packet is copied for dispatch, record both:

- `authoring packet`: where the coordinator wrote it
- `dispatch packet`: the peer-readable path actually given to the external LLM

### Readability Probe

Before the full peer review or debate call, run a cheap readability probe against the dispatch packet.

- Ask the peer to read the dispatch packet and echo the first Markdown heading or another small deterministic string from it using an explicit ACK form, such as:
  `ACK_PACKET_RECEIVED <packet-id or deterministic packet marker> -- I received the packet and will work on it.`
- If that probe fails because the path is ignored, unreadable, or out of workspace, classify it as `path_or_permission_failure`.
- Tell the user briefly which path failed.
- Fix the dispatch path, prefer `<ADS_PROJECT_KNOWLEDGE_ROOT>/tmp/peer-dispatch/<workflow>/`, and retry once before spending tokens on the real task.
- Do not treat a failed readability probe as model disagreement or reasoning failure.

### Peer Handshake Gate

Before starting the full peer-task timer for any long peer dispatch, run a cheap packet-bound handshake and show the result to the user.

- The handshake must prove the peer received the actual packet or prompt marker, not merely a generic request.
- For file-based packets, the readability probe is the handshake. Require the peer to return `ACK_PACKET_RECEIVED <packet-id or deterministic packet marker> -- I received the packet and will work on it.` before the full task starts.
- For self-contained `stdin` or inline prompt transport, include a packet ID or first-heading marker in the payload and require the same `ACK_PACKET_RECEIVED ...` form with no substantive reasoning.
- Use a 60-second ACK window by default unless the user overrides it.
- Start the full `cowork_timeout_seconds`, `swarm_timeout_seconds`, or audit timer only after the handshake succeeds.
- If the handshake fails, returns empty output, or times out, classify it as `handshake_failed` or the more specific transport failure (`path_or_permission_failure`, `malformed_or_no_output`, capacity error) and fix transport before spending the full task budget.
- The handshake is transport evidence only. Do not synthesize it as a peer answer.
- Adaptive escalation order:
  1. Try the easiest supported packet-bound ACK transport first.
  2. If it fails, fix the packet location or prompt transport and retry once using another supported method such as stdin, file path, in-repo dispatch copy, prompt file, session resume, or a CLI/provider-specific attachment mechanism.
  3. If the peer CLI supports streaming output, use streaming mode so ACK text can be observed as soon as the peer starts emitting tokens.
  4. If context retention matters, use a same-run ACK + task invocation: the peer reads the packet marker, emits `ACK_PACKET_RECEIVED ...`, then continues the substantive task in that same run.
  5. If all supported transports fail, mark that peer unavailable or ask the user whether to proceed degraded.

### Live-Run Observation

While the peer process is still running:

- Treat process liveness and elapsed wall-clock time as the primary signal, not the current byte count of redirected stdout/stderr files.
- Keep the workflow timeout (`audit_timeout_seconds`, `cowork_timeout_seconds`, or `swarm_timeout_seconds`) as the hard ceiling.
- Use host-specific references for any peer-specific soft suspicion thresholds or buffering quirks.
- **BLOCKING RULE: Always run the Heartbeat Monitor below.** Every peer dispatch in `/cowork`, `/consensus`, `/debate`, and `/audit-work` MUST show heartbeat output to the user. This is not optional. If you dispatch a peer without a heartbeat, you have violated this rule.

### Heartbeat Monitor (Mandatory, Non-Blocking)

Start the heartbeat loop only after the Peer Handshake Gate succeeds. Do not run heartbeat checks during the ACK window itself.

Run a lightweight heartbeat every 30 seconds while ANY peer LLM process is running. Show the output to the user by default. This is **informational only** — it never kills, never blocks, never auto-escalates. It just reports so the user can see what's happening.

**Rules:**

- The heartbeat NEVER kills a peer process.
- The heartbeat NEVER blocks workflow progress.
- The heartbeat reports liveness and elapsed time. That's it.
- If the user wants to kill a stalled peer, they decide — not the heartbeat.

**What to check (every 30s):**

1. **Process liveness:** `kill -0 $PID` — is the peer process still alive?
2. **Elapsed time:** how long since dispatch?
3. **Output bytes (informational):** `wc -c < $STDOUT_FILE` — note that some peers buffer until exit.

**How to report:**

- While alive: `[peer-heartbeat] <peer_name> | alive | <elapsed>s`
- On exit: `[peer-heartbeat] <peer_name> | done | <elapsed>s | <bytes> bytes`

Keep it to one short line. Don't add stall warnings or recommendations — the user can read elapsed time themselves.

**Known buffering behavior by peer:**

- **Codex CLI** (`codex exec`): Buffers ALL stdout until process exit. Zero bytes during execution is normal. GPT-5.5 at xhigh reasoning takes 3-5 minutes for complex prompts. This is expected, not a stall.
- **Claude CLI** (`claude -p`): May buffer until exit in headless mode.
- **Gemini CLI** (`gemini -p`): Typically streams; byte growth is a valid liveness signal.

**Cost:** Zero tokens, negligible CPU (~1ms per check). The heartbeat adds no peer interaction — it only inspects local process state and file size.

### Dispatch Cleanup

Dispatch copies are transport artifacts, not primary evidence.

- Keep the authoring packet in `<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/` or `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/` according to the user's retention choice.
- Delete temporary dispatch copies after the peer run finishes unless the user explicitly asks to retain them.
- If a local-only dispatch copy in `tmp/` should be kept after the run, move it into `<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/` instead of leaving it in the workspace `tmp/`.
- If the dispatch copy is retained temporarily for troubleshooting, say so and clean it up before closing the task when feasible.

## Failure Classification

Classify peer failures before retrying:

- `path_or_permission_failure`: peer could not read the packet or target files
- `capacity_or_rate_limit`: `429`, `503`, provider-capacity exhaustion
- `timeout`
- `malformed_or_no_output`
- `empty_result_transport_failure`: peer exited successfully but returned an empty answer body
- `truncated_output`

Only retry transient transport failures such as `429` and `503` by default.
Do not treat path/permission failures as model reasoning failures.
Fix the path, then retry once with the corrected dispatch copy.
Only classify `empty_result_transport_failure` after the peer process has exited successfully and stdout is still empty.
If a broad packet-based audit returns `empty_result_transport_failure`, retry once with a tighter prompt, a bounded file set, and a constrained read-only tool surface when the peer supports it.
If that retry falls back to plain text, keep the fallback on a shorter bounded timeout instead of reusing the full audit timeout again.

## Model And Prompt Hygiene

- Pin the model when the user requests it or when reproducibility matters.
- If the workflow promises exact model reporting, do not dispatch on an inferred or alias-only model. Require an explicit or locally proven exact model name/version before running.
- When resolving model names, always check `skills/swarm-consensus/references/cli-smoke-test.md` for documented model IDs before falling back to CLI probes or asking the user. That file is the canonical source for locally verified peer model names/versions.
- Before declaring a peer model unresolved, run the Model Memory Map below. Do not stop at `which <cli>` or `<cli> --version`; CLI version strings prove tool availability only, not model identity.
- If a requested Claude model is unproven locally or the CLI rejects it, run `skills/swarm-consensus/scripts/cli_smoke_test.py` in discovery mode before asking the user for another model. Do not keep guessing manually when the smoke harness already exists.
- If Claude rejects an alias and prints `Try --model to switch to ...`, treat that suggestion as a discovery candidate only. Do not switch to a different family/version until the Model Memory Map has been checked for an exact saved preference or model-plan `command_model`.
- For Claude consensus flows, use discovery with `--claude-require json`. For Claude audit flows that may need plain-text fallback, use `--claude-require both`.
- A valid Claude proof is any one of: an exact environment cache hit from `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/swarm-consensus/smoke-tests/last-known-good.json` with a real artifact path, an exact-model `session_success` earlier in the current session on the same host/CLI, or a fresh discovery run that writes a new artifact.
- If discovery finds a working exact model in the same requested family/version, use that exact model and say it was smoke-proven on this host. If discovery only finds a different family/version, stop and ask the user before switching.
- Keep the ask explicit: what to inspect, what to ignore, what output shape to return.
- Require strengths as well as findings so the user sees what should stay unchanged.

### Model Memory Map

Use this checklist for `/consensus`, `/debate`, `/audit-work`, `/cowork`, and any other external peer LLM dispatch. Its purpose is to prevent the Coordinator from forgetting where saved peer model preferences and proof artifacts live.

Check model sources in this order:

1. Per-run controls: `claude_model=...`, `gemini_model=...`, `codex_model=...`.
2. Project knowledge root evidence: resolve `<ADS_PROJECT_KNOWLEDGE_ROOT>` from `ADS_PROJECT_KNOWLEDGE_ROOT`, `ADS_WORKSPACE_ROOT`, or sibling `ADS-project-knowledge/`, then inspect retained and local smoke-test caches, discovery reports, and consensus reports there.
3. AI Dev Shop repo evidence: inspect repo `.local-artifacts/`, repo `reports/`, and bounded peer-dispatch packets under `tmp/peer-dispatch/`.
4. Home CLI config files that expose model defaults. Claude CLI uses `~/.claude/settings.json`; Gemini CLI uses `~/.gemini/settings.json` and the model name is at `model.name`; these are fallback preferences such as `us.anthropic.claude-opus-4-6-v1[1m]` or `gemini-3.1-pro-preview`.
5. Candidate ladders: `skills/swarm-consensus/references/model-candidate-ladders.json`. These are discovery candidates, not proof by themselves.

To make this lookup mechanical, run:

```bash
python3 skills/swarm-consensus/scripts/cli_smoke_test.py \
  --model-plan-only \
  --output-format json
```

Interpretation rules:

- Prefer exact model IDs over aliases. A provider-qualified saved model string is stronger retained evidence than a family alias.
- For Claude, the exact saved preference in `~/.claude/settings.json` can be passed directly to `claude --model` when `--model-plan-only` reports it as `command_model`; do not replace it with a lower-version CLI suggestion produced by an invalid alias.
- Treat a Claude cache entry as environment-exact proof only when hostname, OS, machine, Claude CLI version, transport requirement, and artifact path match the current run. If those do not match but an exact model appears in retained smoke reports or consensus reports, use it as a saved preference and say current-host proof is stale or requires a fresh smoke test.
- Treat project knowledge and repo-local evidence as higher priority than home CLI defaults; home defaults are still required fallback sources when project/repo evidence is absent.
- Treat `~/.gemini/settings.json` `model.name` as the saved Gemini model preference when present. Do not demote it to unresolved just because `gemini --version` only returns the CLI version.
- Never print `model unresolved` until every source in this map has been checked or is unavailable.

## Capability Discovery

Use these sources in this order:

1. local capability probes in `harness-engineering/validators/`
2. `framework/routing/capability-probes.tsv`
3. `framework/routing/compatibility-matrix.md`
4. host-specific smoke-test artifacts when they exist

Useful local references:

- `harness-engineering/validators/probe_host_capabilities.sh`
- `harness-engineering/validators/resolve_subagent_mode.sh`
- `framework/routing/capability-probes.tsv`
- `framework/routing/compatibility-matrix.md`
- `skills/swarm-consensus/references/cli-smoke-test.md`

## Reusable Rule

If a peer-LLM interaction pattern turns out to be host-sensitive, move it into a shared reference like this one instead of copying the rule into one command only.
