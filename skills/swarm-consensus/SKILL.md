# Swarm Consensus Skill

## Goal
To orchestrate a multi-model swarm (Gemini, Claude, Codex) via their respective CLIs to analyze a complex problem, collate their independent reasoning, and synthesize a unified, superior solution.

## When to Use This Skill
- When the user explicitly requests a "consensus", "swarm analysis", or uses the `/consensus` command.
- When an architecture decision (ADR) has profound consequences and requires rigorous, multi-perspective validation.
- When Red-Team needs to aggressively probe a Spec for vulnerabilities.
- When the Coordinator is faced with an ambiguous or highly complex directive.

## Prerequisites & State Check
Before executing a swarm query, you MUST verify which CLI tools are available and what versions/models they are configured to use.

1.  **Check Availability:** Run `which claude` and `which codex` via shell to determine if the tools are installed.
2.  **Determine Model Versions:**
    *   **Gemini:** State your current model version.
    *   **Claude:** Check the configured model (e.g., via `claude --version` or checking `.claude/settings.local.json`).
    *   **Codex:** Check the configured model (e.g., via `codex --version` or configuration files).
3.  **Remember User Preferences:** If the user has explicitly requested to use a specific model version (e.g., "Use Claude 3.5 Sonnet"), use your global memory tool to save this preference. When starting a consensus task, check your memory for any saved model overrides and apply them via CLI flags if necessary.

## The Consensus Workflow

1.  **Prompt Formulation:** Create a single, highly specific prompt encapsulating the user's problem, constraints, and required output format.
2.  **Swarm Dispatch (Parallel Execution):**
    *   **Self (Gemini):** Generate your own internal reasoning for the prompt.
    *   **Claude (if available):** Execute `claude -p "<prompt>"` (or equivalent command) via shell.
    *   **Codex (if available):** Execute `codex "<prompt>"` (or equivalent command) via shell.
3.  **Collation:** Capture the `stdout` from all external tools.
4.  **Synthesis:** Analyze all responses. Identify areas of agreement (strong signals), areas of divergence (requires deeper analysis), and unique insights from individual models.
5.  **Reporting:** Output a structured `consensus-report.md` (or inline response if requested) detailing:
    *   **The Swarm:** Explicitly list the models and exact versions used (e.g., "Gemini 1.5 Pro, Claude 3.5 Sonnet, Codex 0.2").
    *   **Individual Findings:** Brief summaries of each model's independent conclusion.
    *   **The Consensus:** The final, synthesized recommendation or solution.

## Configuration Updates
If a user asks to change the default model for a specific CLI tool (e.g., "Always use Opus for consensus"), you should attempt to update that tool's configuration file (e.g., `.claude/settings.local.json`) or save the flag requirement to your global memory to append to future shell commands.