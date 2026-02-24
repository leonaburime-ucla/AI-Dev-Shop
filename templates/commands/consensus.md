# Swarm Consensus Command (/consensus)

## Purpose
To invoke the multi-model Swarm Consensus skill to solve a complex problem using the combined reasoning of available CLI LLM tools (Gemini, Claude, Codex).

## Usage
Provide the problem or question you need analyzed. The active agent will dispatch this prompt to all available LLM CLIs in the background, collate their responses, and synthesize a final `consensus-report.md`.

## Arguments
- `[prompt]`: The detailed question or architectural problem to analyze.

---

**Directive:**
Act as a Swarm Consensus Coordinator.

1.  Load the Swarm Consensus skill from `skills/swarm-consensus/SKILL.md`.
2.  Follow its prerequisite checks to verify which CLIs (`claude`, `codex`) are installed and determine their model versions. Check your memory for any user-saved model version preferences.
3.  Execute the swarm dispatch for the following prompt: "$ARGUMENTS"
4.  Capture the `stdout` from all tools, including your own internal reasoning.
5.  Synthesize a final recommendation and output it. Explicitly list the model versions that contributed to the consensus (e.g., Gemini 1.5 Pro, Claude 3.5 Sonnet, Codex 0.2).