---
name: swarm-consensus
version: 1.6.2
last_updated: 2026-04-03
description: Orchestrate a multi-model swarm by dispatching a prompt to all available LLM CLIs (whichever ones are installed), collating independent responses, and synthesizing a consensus. Supports single-pass and debate modes. Model-agnostic — the primary model is whoever is currently running this skill. OFF by default.
---

# Skill: Swarm Consensus

**This skill is OFF by default.** Only invoke it when explicitly instructed by the user or the Coordinator.

## When to Use

- User explicitly requests "consensus", "swarm analysis", or uses the `/consensus` command
- User explicitly requests "debate" or uses the `/debate` shortcut command
- Coordinator directs a specific agent to use Swarm Consensus for a single hard task
- An ADR has profound architectural consequences and requires multi-perspective validation
- Red-Team is probing a spec for blind spots that a single model might miss

## Model-Agnostic Design

**You are the primary model.** Whatever LLM is currently running this skill is the primary reasoner. You generate your own response first, then dispatch the same prompt to any other available CLI tools, and synthesize the combined output.

The peer CLIs are external — they run as subprocesses via shell and return `stdout`. You do not know in advance which ones are installed. The prerequisite check determines this at runtime.

For shared packet, transport, diagnostics, and capability-discovery rules that apply beyond consensus, use `skills/llm-operations/references/peer-llm-dispatch.md`.

Supported peer CLIs:

| CLI | Invocation | Notes |
|---|---|---|
| `claude` | `claude -p --output-format json "<prompt>"` | Claude Code CLI. Prefer structured output when available. |
| `gemini` | `gemini -m <model> -o json -p "<prompt>"` | Gemini CLI. Put `-m` before `-p` when pinning a model. |
| `codex` | `codex exec --json "<prompt>"` | OpenAI Codex CLI. Prefer `exec --json`; some repos can inject startup chatter into plain-text runs. |

If you are Claude Code, you dispatch to `gemini` and `codex`. If you are Gemini, you dispatch to `claude` and `codex`. The skill works identically regardless of who is primary.

### Participant Roles

- The current host model is already the `Primary` participant in the swarm and in debate mode.
- Do not add a same-family child/subagent as an extra voting peer by default. That weakens independence and can overweight one model family.
- If the user explicitly wants a same-family helper, use it only for context-packet preparation, adversarial review, or synthesis critique. Record it as a non-voting helper in run notes or diagnostics, and exclude it from agreement math and the Decision Ledger.

### Primary Participation Guard (hard requirement)

- The current host model MUST contribute a substantive first-pass response before any peer synthesis, debate, or final recommendation.
- A consensus run that only relays peer outputs is invalid. Do not present peer-only debate as consensus.
- If the host environment cannot cleanly surface the current host model's own first-pass response, create exactly one same-family child/helper to supply that frozen first-pass response before reading peer outputs.
- That same-family child/helper fills the `Primary` slot only. It is not an extra voting peer, must not create a fourth vote, and must not be counted separately in agreement math.
- If neither the host model nor a same-family child/helper can provide a substantive primary response, stop and report the run as invalid instead of returning a peer-only result.

---

## Consensus Modes

Pick one mode explicitly at run start:

- `single-pass` (default): independent first-pass answers from all models, one synthesis pass, then final recommendation.
- `debate`: independent first-pass answers, then bounded rebuttal rounds, then final recommendation.

If the user does not specify mode, use `single-pass`.

---

## Runtime Controls

Consensus runs accept runtime controls from the user:

- `max_rounds=<int>`: maximum rebuttal rounds (default `2` when mode is `debate`)
- `min_confidence=<0.0-1.0>`: minimum agreement threshold to stop early (default `0.90`)
- `swarm_timeout_seconds=<int>`: total wall-clock budget for the full consensus run across all peer calls and debate rounds (default `300`)
- `claude_model=<id>`: per-run Claude model override
- `gemini_model=<id>`: per-run Gemini model override
- `codex_model=<id>`: per-run Codex model override

If controls are not provided, use defaults. In `single-pass`, `max_rounds` is unused. In `debate`, default to `2` rounds unless the user overrides it. If provided values are invalid, state the invalid value and fall back to defaults.

---

## Step 1 — Prerequisite Check + Preflight

Before dispatching anything, run these checks via shell:

```bash
which claude && claude --version 2>/dev/null || echo "claude: not installed"
which gemini && gemini --version 2>/dev/null || echo "gemini: not installed"
which codex  && codex  --version 2>/dev/null || echo "codex: not installed"
```

From the output:
- Record which CLIs are available (installed and returning a version)
- Record the CLI version string separately from the resolved model ID — these are not the same thing
- Skip any CLI that is not installed — do not error, just note it as absent in the report
- Check for any user-saved model version preferences (e.g. from a prior "always use Opus for consensus" instruction) and apply them via CLI flags if the tool supports it
- Run preflight transparency announcement before asking any model:
  - `Asking question to Gemini <version>, Codex <version>, Claude <version>`
  - If a CLI is missing: `Gemini not installed` (or equivalent) in the same announcement.

A minimum viable swarm is **primary model + 1 peer**. If no peers are available, tell the user and stop — running consensus with only one model produces no value. **This is a graceful stop, not a pipeline failure.** If Swarm Consensus was invoked as part of a pipeline stage, that stage proceeds using the primary model's output alone — the pipeline is not blocked by missing peer CLIs.

### Model Selection Resolution Protocol

Before dispatching prompts, resolve the planned model for each available peer CLI in this order:

1. Per-run override from the current prompt (`claude_model=...`, `gemini_model=...`, `codex_model=...`)
2. Saved user preference for consensus runs
3. Local CLI config/default model
4. Alias assumption such as `sonnet`, `opus`, `latest`, or `preview`

For each peer, record:

- `requested_model`: what the run asked for, if anything
- `resolved_model`: the exact model ID proven from CLI config/output, if available
- `selection_source`: `per_run_override`, `saved_preference`, `local_default`, `alias_assumption`, `smoke_test_discovery`, or `unknown`

If any peer model is not explicitly pinned for the current run, or the exact resolved model ID cannot be proven, pause before dispatch and tell the user:

- which peer models are planned
- which ones are inferred rather than explicitly pinned
- how to override them for this run

Use this pattern:

`Planned peer models: Claude=<resolved-or-inferred>, Gemini=<resolved-or-inferred>, Codex=<resolved-or-inferred>. Reply with "run" to proceed or override with claude_model=..., gemini_model=..., codex_model=....`

Do not silently upgrade a peer to a newly released model family/version just because it exists. If a newer model may be better, tell the user and let them choose.

If the Claude peer model is requested but not yet proven locally, or the CLI rejects the requested model name, do not keep guessing manually. Run the smoke-test harness in discovery mode first:

```bash
python3 skills/swarm-consensus/scripts/cli_smoke_test.py \
  --discover-claude \
  --claude-model <requested-or-saved-model> \
  --claude-require json \
  --output-format json
```

Use the discovered `winner.model` only when it is the same requested family/version and it passed locally in JSON mode. If discovery finds only a different family/version, stop and ask the user before switching.
A valid Claude proof is either an exact environment cache hit from `<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/swarm-consensus/smoke-tests/last-known-good.json` with a real artifact path, or a fresh discovery run that writes a new artifact for the current environment.

### Freshness policy

Consensus runs should avoid silently drifting to newer model families/versions.

- Claude: use `--model` when the user or a saved preference pins one.
- Gemini: use `-m` when the user or a saved preference pins one.
- Codex: use `-m` when the user or a saved preference pins one.

If a configured or inferred model appears stale, unavailable, preview-only, alias-based, or unknown, state it before the run and continue only if:
- the user confirms the plan, or
- the user supplies an override for this run.

### Smoke-Test Reference

Before changing saved consensus model preferences or updating the command docs to prefer a new flag pattern, rerun the CLI smoke-test harness:

- Script: `skills/swarm-consensus/scripts/cli_smoke_test.py`
- Guide: `skills/swarm-consensus/references/cli-smoke-test.md`

Use the smoke test to compare text vs structured output, stderr noise, end-marker behavior, and explicit model-flag handling on the current host.

By default, save ad hoc smoke-test artifacts to `<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/swarm-consensus/smoke-tests/`.
If the user explicitly wants a retained host baseline in the repo, set `--artifacts-dir <ADS_PROJECT_KNOWLEDGE_ROOT>/reports/swarm-consensus/smoke-tests`.

If there is no recent dated artifact for the current host, or if the host/CLI/model stack has changed materially since the last run, ask the user whether to run the smoke test now and save a dated artifact before changing saved preferences or slash-command guidance.
If a Claude model-resolution failure happens during a live consensus preflight, run the smoke test immediately instead of asking the user to guess another Claude model by hand.

---

## Step 2 — Prompt Formulation

Write one focused prompt that contains:
- The problem or question to analyze
- All relevant constraints and context
- The required output format (e.g. "structured recommendation with reasoning")

Keep it self-contained. The peer CLIs have no project context — everything they need must be in the prompt itself.

### Shared Context Packet Protocol

Use a shared context packet when the question depends on brownfield repo knowledge, greenfield planning docs, or any project context too large or important to rely on an ad hoc prompt alone.

1. Before writing a packet to disk, decide whether it is `local-only` scratch or a retained project artifact.
2. If the user has not already specified that choice, ask:
   `Save context packet? Reply "save packet" to retain it in <ADS_PROJECT_KNOWLEDGE_ROOT>/reports/swarm-consensus/context/ or "local only" to keep it in <ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/swarm-consensus/context/.`
3. Save the packet at `<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/swarm-consensus/context/CTX-<slug>-<YYYY-MM-DD>.md` by default.
4. If the user explicitly wants a reusable retained artifact, save or promote the packet to `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/swarm-consensus/context/CTX-<slug>-<YYYY-MM-DD>.md`.
5. Use `skills/swarm-consensus/references/context-packet-template.md` as the reference layout.
6. Put only the context every participant needs:
   - the exact question to answer
   - project type (`brownfield` or `greenfield`)
   - scope, goals, and constraints
   - architecture summary
   - relevant files and source artifacts
   - known unknowns and open decisions
7. Give the same packet content to every peer CLI. The primary model may inspect the repo directly, but peer transport should prefer a self-contained `stdin` payload when the packet fits cleanly in one bounded prompt.
8. If the question is materially repo-dependent and no shared packet exists yet, create one before dispatching peers.
9. If a peer still needs file-based packet access because the payload is too large or it must inspect repo files directly, follow the shared transport fallback rules in `skills/llm-operations/references/peer-llm-dispatch.md`.
10. Do not promote a local-only context packet into `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/` only to satisfy peer readability.

### Online Resource Pre-Fetch (primary model responsibility)

If the prompt requires online resources (URLs, external files, live data from the web):

1. **The primary model fetches all required resources before dispatching to peers.**
2. Embed fetched resource content into the shared prompt payload — do not pass raw URLs and expect peers to fetch independently.
3. If any required resource cannot be fetched (404, timeout, auth wall, etc.):
   - Do not proceed with a degraded prompt that omits the resource.
   - Tell the user immediately: which URL failed and why.
   - Ask whether to proceed without that resource or abort.
   - If the user says proceed, note the missing resource explicitly in the prompt so all models reason from the same incomplete-but-declared baseline.

**Rationale:** Some LLMs in the swarm may not have web access, or the same URL may return differently across models. Pre-fetching by the primary model guarantees all peers reason from identical source material.

### Prompt Transport Safety (hard requirement)

Do not pass large or untrusted prompt text directly as shell-interpolated inline strings.

1. Write the full prompt to a temporary file (for example `.swarm-prompt.txt`) or pipe it via stdin.
2. Invoke peer CLIs using file/stdin-safe patterns where possible.
3. If a tool only supports inline prompt args, apply strict escaping and note this risk in the report.
4. Never execute fetched resource content as shell code.

For file-based transport, prefer `<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/swarm-consensus/prompts/` over the repo root.

---

## Step 3 — Swarm Dispatch

**CRITICAL ANTI-HALLUCINATION RULE:** You MUST NOT fake, imagine, or hallucinate the responses from other models. If a CLI tool is not installed, or if the shell command fails or times out, you must strictly report that it failed or is unavailable. Do not invent a consensus or make up quotes from peer models. You are only allowed to synthesize the actual text captured from the `stdout` of the shell commands.

### First-pass anti-bias rule (hard requirement)

1. Primary model MUST produce its own answer first and freeze it.
2. Primary model MUST NOT read peer outputs until its first-pass answer is written.
3. Round-1 peer prompts MUST NOT include other models' answers.
4. If the host environment cannot surface the primary model's first-pass answer cleanly, it MUST create one same-family child/helper to fill the `Primary` slot before peer synthesis.
5. Peer-only consensus runs are invalid and MUST stop.

### Swarm timeout budget (hard requirement)

1. Start a wall-clock timer when peer dispatch begins.
2. Default to `swarm_timeout_seconds=300` unless the user overrides it.
3. Before every peer CLI call in any round, compute the remaining swarm budget.
4. Use that remaining budget as the maximum wait for the next peer call.
5. If the remaining budget is `<= 0`, stop dispatching additional peer calls, mark unfinished peers as timed out, and continue with synthesis from the responses already captured.

### Structured Output And Diagnostics Protocol

1. Prefer structured output modes such as JSON when a peer CLI supports them.
2. Parse the peer answer from `stdout` only.
3. Treat `stderr` as diagnostics, not as part of the peer answer.
4. If a CLI emits startup chatter, tool logs, or repo bootstrap text, exclude that material from the peer answer. Use only the structured payload or the end-marker-delimited answer.
5. If structured mode fails but plain text succeeds, record the fallback mode and include that fact in the report.

Store raw per-round stdout/stderr captures in `<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/swarm-consensus/offloads/` by default. Only save them under `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/offloads/` when the user explicitly wants retained evidence.

### Retryable Peer Failure Protocol

1. Treat transient transport/capacity failures as retryable when the signal is clearly temporary (for example HTTP `429`, HTTP `503`, rate-limit text, or provider capacity exhaustion text).
2. Retry with bounded backoff only while there is remaining `swarm_timeout_seconds` budget.
3. Stop after at most 2 retries per peer call.
4. If retries are exhausted, mark the peer as failed and record the attempt count plus the last error class in the report.

### Anti-Truncation Protocol (hard requirement)

Do not rely on subjective "looks abrupt" checks alone.

1. Require each peer response to end with a deterministic end marker, for example `<<SWARM_END>>`.
2. If marker is missing, or response is empty/obviously partial, mark it as `Failed (Truncated)`.
3. **Truncated responses MUST NOT be included in synthesis.**
4. Tell the user inline: `[ModelName]'s response was truncated or incomplete. It has been excluded from synthesis.`

### Round 1 (all modes)

1. **Self (primary model):** Generate full first-pass response and freeze it.
2. **Each available peer CLI:** Execute via shell, capture `stdout`. Use the remaining `swarm_timeout_seconds` budget for each call — if a tool hangs or the budget is exhausted, mark it as timed out and continue.

```bash
# Example patterns — adapt to actual CLI support
# Prefer structured output and keep stderr separate from the peer answer
claude --output-format json -p "$(cat .swarm-prompt.txt)" 2>peer-claude.stderr
gemini -m <resolved-model> -o json -p "$(cat .swarm-prompt.txt)" 2>peer-gemini.stderr
codex exec --json -m <resolved-model> --cd <dispatch-dir> --skip-git-repo-check "$(cat .swarm-prompt.txt)" 2>peer-codex.stderr
```

If a peer CLI returns a non-zero exit code or empty output, mark it as failed in the report and exclude it from synthesis.

### Resource Fetch Failure — Peer Withdrawal Protocol

If a peer model's response contains a resource fetch failure signal (e.g. it reports it could not access a required URL, file, or external dependency needed to answer the question):

1. **Mark that peer as "Resource unavailable" in the Swarm table** — do not include its response in synthesis.
2. **Tell the user immediately**, inline, before continuing:
   > `[ModelName] could not access [resource]. It has withdrawn from this round. Continuing with [remaining models].`
3. Do not silently include a response that was built on assumptions about content the model could not read — that contaminates synthesis with hallucinated context.
4. If the *primary model* cannot fetch a required resource, it must tell the user and stop the run (or ask to proceed without it) — it cannot dispatch a degraded prompt to peers without disclosing this.
5. If after withdrawals only one model remains (primary + 0 peers), stop and inform the user: not enough participants for meaningful consensus.

---

### Debate rounds (debate mode only)

In `debate` mode, run bounded rebuttal rounds after Round 1:

1. Build a decision-point ledger (architecture choice, data model strategy, risk posture, migration approach, etc.).
2. Summarize deltas only (where models disagree) and send the summarized deltas back to each model for rebuttal.
   - For each disputed decision point, require every responding model to state:
     - its current position
     - why it currently holds that position
     - the strongest reason against the leading opposing position
     - whether its position changed this round and, if so, why
     - what evidence, assumption change, or repo fact would change its mind
   - Do not accept a bare "still agree/disagree" rebuttal when the model can provide reasoning. The point of the debate round is rationale movement, not just vote counting.
   - **Mid-Debate Dropout Rule:** If a model that participated in Round 1 fails to respond, times out, or reports a resource failure in Round 2+, it **withdraws from the remainder of the debate**. 
   - Do not hallucinate its rebuttal. Note its withdrawal inline to the user. Its Round 1 positions remain in the ledger but are marked as "Final (Withdrawn)".
   - The same `swarm_timeout_seconds` budget applies to debate rounds. If the remaining budget expires mid-debate, stop additional rebuttal calls, mark affected peers as `Withdrawn`, and synthesize with the evidence already collected.
   - Recompute active participants each round. If active participants drop below two total responders (primary + at least one peer), stop debate and report insufficient participants for meaningful consensus.
3. Repeat for up to `max_rounds`.
4. Stop early when agreement is >=`min_confidence` on decision points.

Agreement formula:
- `agreement_percent = (decision_points_with_same_outcome / total_decision_points) * 100`

If max rounds reached without reaching `min_confidence`:
- stop debate,
- declare unresolved deltas,
- provide recommendation with explicit uncertainty/tradeoff callouts.

---

## Step 4 — Synthesis

With all responses collected:

1. **Areas of agreement** — where 2+ models reached the same conclusion independently. These are strong signals. Weight them heavily.
2. **Areas of divergence** — where models disagreed. Do not average them out. Explain *why* they diverged (different assumptions, different risk weighting, different information). Present both positions clearly.
3. **Unique insights** — something only one model raised. Flag it as unverified but worth considering.
4. **Final recommendation** — your synthesized conclusion. Be explicit about which inputs drove it and why.

---

## Step 5 — Output

### Template Guard (hard requirement)

1. The final report MUST use the Step 5 headings and tables in the order shown below.
2. Do not collapse a consensus run into a prose-only summary when the user asked for a report or when writing an artifact.
3. In `debate` mode, you may add a `## Debate Trace` section for round-by-round movement, but you must still include all mandatory sections from the template.
4. Before writing any report to disk, decide whether it is `local-only`, `retained`, or `inline-only`.
5. If the user has not already specified that choice, ask:
   `Save consensus report? Reply "save report" to retain it in <ADS_PROJECT_KNOWLEDGE_ROOT>/reports/swarm-consensus/runs/, "local only" to keep it in <ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/swarm-consensus/runs/, or "inline only" for no file.`
6. By default, write ad hoc run reports to `<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/swarm-consensus/runs/<timestamp>-consensus-report.md`.
7. If the user explicitly wants a retained architecture or project artifact, write the final report to `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/swarm-consensus/runs/<timestamp>-consensus-report.md` instead.
8. If a shared context packet was used, record its path in the report header.
9. If the user prefers inline output instead of a file, preserve the same section order and tables inline.
10. A valid report MUST include a non-empty `Primary` row in `## The Swarm`.
11. A valid report MUST include a non-empty `### <Primary model name>` subsection under `## Individual Responses`.
12. If either primary slot is missing or empty, stop and report the run as invalid rather than presenting peer-only output as consensus.

Produce a `consensus-report.md` (or inline if the user prefers) with this structure:

```markdown
# Consensus Report

**Date:** <ISO-8601>
**Prompt:** <the prompt used>
**Context Packet:** <path or "none">
**Mode:** <single-pass | debate>
**Controls:** `max_rounds=<int>`, `min_confidence=<0.0-1.0>`, `swarm_timeout_seconds=<int>`, optional per-run model overrides
**Primary model:** <name>

## The Swarm
| Role | CLI | Requested Model | Resolved Model | CLI Version | Selection Source | Status | Attempts |
|---|---|---|---|---|---|---|---|
| Primary | <your CLI> | <requested> | <resolved> | <version> | <source> | Responded | 1 |
| Peer | claude | <requested or "n/a"> | <resolved or "unknown"> | <version or "not installed"> | <source> | Responded / Failed / Failed (Truncated) / Timed out / Retry exhausted / Withdrawn / Not installed / Resource unavailable | <count> |
| Peer | gemini | <requested or "n/a"> | <resolved or "unknown"> | <version or "not installed"> | <source> | Responded / Failed / Failed (Truncated) / Timed out / Retry exhausted / Withdrawn / Not installed / Resource unavailable | <count> |
| Peer | codex  | <requested or "n/a"> | <resolved or "unknown"> | <version or "not installed"> | <source> | Responded / Failed / Failed (Truncated) / Timed out / Retry exhausted / Withdrawn / Not installed / Resource unavailable | <count> |

## Dispatch Diagnostics
| CLI | Output Mode | stdout Parser | stderr Summary | Retry Notes |
|---|---|---|---|---|
| claude | json | result field / end marker | <short summary> | <attempt summary> |
| gemini | json | response field / end marker | <short summary> | <attempt summary> |
| codex | json | event stream / agent message | <short summary> | <attempt summary> |

## Debate Trace
<Only include in debate mode. Capture round-by-round deltas, rationale changes, withdrawals, and position shifts before synthesis. For each disputed decision point, record each model's current position, why it held that position that round, whether it changed, and what would change its mind.>

## Individual Responses

### <Primary model name>
<Summary of primary reasoning>

### Claude (if responded)
<Summary of Claude's response>

### Gemini (if responded)
<Summary of Gemini's response>

### Codex (if responded)
<Summary of Codex's response>

## Synthesis

### Agreement
<What all responding models agreed on>

### Divergence
<Where they disagreed and why>

### Unique Insights
<Anything only one model raised>

### Decision Ledger
| Decision Point | Primary | Claude | Gemini | Codex | Agreement | Key Why / Movement |
|---|---|---|---|---|---|---|
| <point 1> | <position> | <position> | <position> | <position> | Yes/No | <main rationale and any round-to-round movement> |

### Unresolved Deltas
<Only include if disagreement remains after synthesis/debate>

## Final Recommendation
<Synthesized conclusion with reasoning>
```

Always fill in the Swarm table completely, including models that were not installed or failed. The user should always know which models contributed, which models were only inferred, and how many attempts each peer required.

---

## Configuration

If the user asks to set a default model version for a peer CLI (e.g. "always use Opus for Claude in consensus runs"), save that preference and apply it as a flag on future dispatches. Document what flag was used in the consensus report so the run is reproducible.

Even when a saved preference exists, if the current run did not explicitly pin the model, preflight must still show the planned model and give the user a chance to override it before dispatch.
