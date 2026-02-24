---
name: swarm-consensus
version: 1.1.0
last_updated: 2026-02-23
description: Orchestrate a multi-model swarm by dispatching a prompt to all available LLM CLIs (whichever ones are installed), collating independent responses, and synthesizing a consensus. Model-agnostic — the primary model is whoever is currently running this skill. OFF by default.
---

# Skill: Swarm Consensus

**This skill is OFF by default.** Only invoke it when explicitly instructed by the user or the Coordinator.

## When to Use

- User explicitly requests "consensus", "swarm analysis", or uses the `/consensus` command
- Coordinator directs a specific agent to use Swarm Consensus for a single hard task
- An ADR has profound architectural consequences and requires multi-perspective validation
- Red-Team is probing a spec for blind spots that a single model might miss

## Model-Agnostic Design

**You are the primary model.** Whatever LLM is currently running this skill is the primary reasoner. You generate your own response first, then dispatch the same prompt to any other available CLI tools, and synthesize the combined output.

The peer CLIs are external — they run as subprocesses via shell and return `stdout`. You do not know in advance which ones are installed. The prerequisite check determines this at runtime.

Supported peer CLIs:

| CLI | Invocation | Notes |
|---|---|---|
| `claude` | `claude -p "<prompt>"` | Claude Code CLI |
| `gemini` | `gemini -p "<prompt>"` | Gemini CLI |
| `codex` | `codex "<prompt>"` | OpenAI Codex CLI |

If you are Claude Code, you dispatch to `gemini` and `codex`. If you are Gemini, you dispatch to `claude` and `codex`. The skill works identically regardless of who is primary.

---

## Step 1 — Prerequisite Check

Before dispatching anything, run these checks via shell:

```bash
which claude && claude --version 2>/dev/null || echo "claude: not installed"
which gemini && gemini --version 2>/dev/null || echo "gemini: not installed"
which codex  && codex  --version 2>/dev/null || echo "codex: not installed"
```

From the output:
- Record which CLIs are available (installed and returning a version)
- Record the exact model version string for each available CLI — this goes in the consensus report
- Skip any CLI that is not installed — do not error, just note it as absent in the report
- Check for any user-saved model version preferences (e.g. from a prior "always use Opus for consensus" instruction) and apply them via CLI flags if the tool supports it

A minimum viable swarm is **primary model + 1 peer**. If no peers are available, tell the user and stop — running consensus with only one model produces no value.

---

## Step 2 — Prompt Formulation

Write one focused prompt that contains:
- The problem or question to analyze
- All relevant constraints and context
- The required output format (e.g. "structured recommendation with reasoning")

Keep it self-contained. The peer CLIs have no project context — everything they need must be in the prompt itself.

---

## Step 3 — Swarm Dispatch

**CRITICAL ANTI-HALLUCINATION RULE:** You MUST NOT fake, imagine, or hallucinate the responses from other models. If a CLI tool is not installed, or if the shell command fails or times out, you must strictly report that it failed or is unavailable. Do not invent a consensus or make up quotes from peer models. You are only allowed to synthesize the actual text captured from the `stdout` of the shell commands.

Run in parallel where possible:

1. **Self (primary model):** Generate your own full response to the prompt internally. Do not anchor on what you expect others to say.
2. **Each available peer CLI:** Execute via shell, capture `stdout`. Use a timeout of 60 seconds per call — if a tool hangs, mark it as timed out in the report and continue.

```bash
# Example — adapt flags to whatever the tool actually supports
claude -p "<prompt>" 2>/dev/null
gemini -p "<prompt>" 2>/dev/null
codex "<prompt>"     2>/dev/null
```

If a peer CLI returns a non-zero exit code or empty output, mark it as failed in the report and exclude it from synthesis.

---

## Step 4 — Synthesis

With all responses collected:

1. **Areas of agreement** — where 2+ models reached the same conclusion independently. These are strong signals. Weight them heavily.
2. **Areas of divergence** — where models disagreed. Do not average them out. Explain *why* they diverged (different assumptions, different risk weighting, different information). Present both positions clearly.
3. **Unique insights** — something only one model raised. Flag it as unverified but worth considering.
4. **Final recommendation** — your synthesized conclusion. Be explicit about which inputs drove it and why.

---

## Step 5 — Output

Produce a `consensus-report.md` (or inline if the user prefers) with this structure:

```markdown
# Consensus Report

**Date:** <ISO-8601>
**Prompt:** <the prompt used>

## The Swarm
| Role | Model | Version | Status |
|---|---|---|---|
| Primary | <your model name> | <version> | Responded |
| Peer | claude | <version or "not installed"> | Responded / Failed / Not installed |
| Peer | gemini | <version or "not installed"> | Responded / Failed / Not installed |
| Peer | codex  | <version or "not installed"> | Responded / Failed / Not installed |

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

## Final Recommendation
<Synthesized conclusion with reasoning>
```

Always fill in the Swarm table completely, including models that were not installed or failed. The user should always know which models contributed.

---

## Configuration

If the user asks to set a default model version for a peer CLI (e.g. "always use Opus for Claude in consensus runs"), save that preference and apply it as a flag on future dispatches. Document what flag was used in the consensus report so the run is reproducible.
