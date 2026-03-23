# Swarm Consensus Command (/consensus)

## Purpose
To invoke the multi-model Swarm Consensus skill to solve a complex problem using the combined reasoning of available CLI LLM tools (Gemini, Claude, Codex).

## Usage
Provide a mode and question. The active agent will dispatch this prompt to available LLM CLIs, collate independent responses, and synthesize a final `consensus-report.md`.

## Arguments
- `[mode] [controls] [prompt]`
- `mode`: `single-pass` (default) or `debate`
- `controls` (optional): `max_rounds=<int>` and/or `min_confidence=<0.0-1.0>`
- `prompt`: the detailed question or architectural problem to analyze

---

**Directive:**
Act as a Swarm Consensus Coordinator.

1. Parse `$ARGUMENTS`:
   - Detect mode from first token when it is `single-pass` or `debate`; otherwise default to `single-pass`.
   - Detect optional controls anywhere in args: `max_rounds=<int>` and `min_confidence=<0.0-1.0>`.
   - Remaining text is the prompt.
   - Defaults if omitted: `max_rounds=3`, `min_confidence=0.90`.
2. Load the Swarm Consensus skill from `<AI_DEV_SHOP_ROOT>/skills/swarm-consensus/SKILL.md`.
3. Follow prerequisite checks to verify which CLIs (`claude`, `gemini`, `codex`) are installed and determine exact version/model strings.
4. Before asking any model, print preflight:
   `Asking question to Gemini <version>, Codex <version>, Claude <version>`
5. Run consensus in the chosen mode:
   - `single-pass`: independent first pass + one synthesis.
   - `debate`: independent first pass + bounded debate rounds until `min_confidence` agreement or `max_rounds`.
6. Capture tool outputs from `stdout` only (no fabricated peer responses).
7. Output final recommendation with: mode, model/version table, agreement summary, divergences, unresolved deltas, and decision ledger.
