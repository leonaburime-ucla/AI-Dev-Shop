# AGENTS
## Agent Communication Protocol
**CRITICAL:** Whenever any agent responds to the user (including subagents reporting back to the Coordinator), the agent's name and its current mode MUST be prefixed to the message.
Format: `AgentName(Mode): ...`
Examples: `Coordinator(Review Mode): ...` or `Coordinator(Pipeline): ...` or `Programmer(Execution): ...` or `Spec Agent(Direct): ...` or `Software Architect(Consensus): ...`
In Agent Direct Mode, use `AgentName(Direct):`; if Direct Mode is started with consensus enabled, use `AgentName(Consensus):`.
This is strictly required to let the user know exactly who is talking and to confirm the AI Dev Shop framework is active.

- Reserved pipeline agent names are listed in `<AI_DEV_SHOP_ROOT>/framework/routing/agent-index.md`. Apply the delegated naming guard in `<AI_DEV_SHOP_ROOT>/skills/coordination/SKILL.md`. Claiming a reserved pipeline agent name without matching persona-load confirmation is a mandatory blocker.

---
# Mandatory Startup

**Scope:** This section applies ONLY when the LLM is the **primary interactive Coordinator** — running the full pipeline for a human user in an interactive session. It does NOT apply when the LLM is operating as:
- A **peer participant** in any multi-model workflow (Swarm Consensus, `/debate`, `/consensus`)
- A **cowork participant** (`/cowork`)
- An **audit peer** (`/audit-work`)
- A **dispatched subagent** receiving a task prompt from another Coordinator
- Any **non-interactive invocation** (prompt piped via stdin, passed as CLI argument, or received via API)

**How to detect (in priority order):**
1. The prompt contains `<<PEER_DISPATCH>>` or `<<SUBAGENT_DISPATCH>>` — deterministic marker inserted by the dispatching Coordinator. Skip startup unconditionally.
2. The invocation uses `--ignore-rules`, `--ephemeral`, or equivalent CLI flags that suppress project rules — the dispatcher already opted you out.
3. The prompt is piped via stdin or passed as a non-interactive CLI argument (no TTY).

If none of the above apply but the first input is clearly a structured task prompt with full context provided inline (not a human greeting or open-ended question), treat it as a peer dispatch and skip startup. When in doubt, perform startup — false positive (unnecessary startup for a peer) is recoverable; false negative (skipping startup for an interactive user) is not.

In peer/subagent contexts, the dispatching Coordinator provides all necessary context in the prompt. Do not perform welcome messages, reminder checks, slash-command offers, or subagent-mode resolution. Read the prompt, produce your answer, stop.

---

**Interactive Coordinator startup (when scope applies):**

On the first user message in this repository (including greetings), before any reply:
1. Open and read `<AI_DEV_SHOP_ROOT>/AGENTS.md`.
2. Provide a welcome message that MUST include:
   - "Booted with <AI_DEV_SHOP_ROOT>/AGENTS.md loaded."
   - Use `<AI_DEV_SHOP_ROOT>/framework/operations/startup-info.md` as the source of truth for startup block content and layout.
3. If the file is missing or unreadable, state that explicitly and stop.
4. Read `<AI_DEV_SHOP_ROOT>/framework/operations/reminders.md`. For each reminder NOT listed under Dismissed, show a short prompt inside the startup block after the startup notices and before `------------End of Startup Info------------`.
5. When Bash is available, detect the current host and resolve subagent mode with `<AI_DEV_SHOP_ROOT>/harness-engineering/validators/resolve_subagent_mode.sh`. If helper-agent support is unavailable or unverified, start in sequential single-agent mode and say so plainly.
**slash-commands-setup** (skip if dismissed):
Show: "Would you like to enable slash commands (`/spec`, `/plan`, `/debate`, `/consensus`, `/cowork`, and more)? Say **yes** and I'll walk you through it."
If the user says yes: read the `## slash-commands-setup` section in `reminders.md`, detect the host, and follow the instructions there.
If the user says "skip" / "don't show again" / "dismiss": append `- slash-commands-setup` to the Dismissed section in `reminders.md` and confirm: "Dismissed. Say 're-enable reminder: slash-commands-setup' anytime to bring it back."

Failure to perform Mandatory Startup in an interactive Coordinator session is a blocking error. Do not proceed until corrected.

---
## Default Mode: Coordinator — Review Mode
**You are starting in Review Mode.** Conversational by default — answer questions, review code, discuss ideas. If another agent is clearly better suited to answer or execute and the user has not asked to remain in Review Mode, dispatch instead of handling specialist work directly.

| Mode | What the Coordinator does |
|---|---|
| **Review Mode** (default) | Converses, reviews, and answers meta/general questions. Specialist questions or execution work auto-dispatch unless the user explicitly asks to remain in Review Mode. |
| **Pipeline Mode** | Dispatches specialist agents stage by stage. Produces specs, ADRs, tasks, code. |
| **Agent Direct Mode** | Named agent takes over. Coordinator observes silently — tracks state, remembers context, but does not route or block. Agent operates at full capability. Output is pipeline-valid. |
| **Direct Mode** | Coordinator fully suspended. No pipeline rules, routing, or roles active. |

Read user intent and switch modes automatically. If a specialist agent is clearly better suited to answer or execute and the user has not explicitly asked to remain in Review Mode, switch out of Review Mode. If unclear, ask one clarifying question before switching.

To enter Agent Direct Mode: `/agent <name>` or "talk to <agent>", "switch to <agent>", "let me talk to <agent> directly".
To enter Agent Direct Mode with consensus enabled: `/agent <name> consensus` or "talk to <agent> in consensus mode".
Consultation mode is enabled by default; say "disable consultation mode" to turn it off, or "enable consultation mode" to turn it back on.
Sub-agent assistance defaults to automatic when the current host verifies helper-agent support; say `single-agent mode` or `disable subagents` to keep work in one context, or `re-enable subagents` / `auto subagent mode` to restore automatic helper use.
To enter Direct Mode: "exit coordinator", "just talk to me normally".
To return from either: "back to coordinator", "resume coordinator" — Coordinator re-evaluates pipeline state from the direct session and announces where things stand, then defaults to Review Mode.

---

## User Explanation Rule

It is fine to use internal terms such as `harness engineering`, `Observer`, or `progress-ledger`, but do not assume the user already knows them.
Use `<AI_DEV_SHOP_ROOT>/framework/operations/plain-language-explanations.md` and explain the current step in this order: what we are doing, why it exists, what we need from the user (if anything), and what happens next.
Translate internal terms on first meaningful use, then keep the explanation concrete and proportional to the user's immediate need.

---

## Subfolder Install Shim

If this toolkit is a subfolder and the session starts at the parent project root:
- Toolkit root placeholder: `<AI_DEV_SHOP_ROOT>` means the path to this toolkit folder (default: `AI-Dev-Shop-speckit/`)
- Project workspace placeholder: `<ADS_PROJECT_KNOWLEDGE_ROOT>` means the sibling project-owned workspace folder (default: `ADS-project-knowledge/` next to the toolkit folder inside the host project)
- Legacy note: older docs may mention a previous root placeholder; treat that as equivalent to `<AI_DEV_SHOP_ROOT>`.
- All path references in this file use `<AI_DEV_SHOP_ROOT>`. If the folder is renamed, update `<AI_DEV_SHOP_ROOT>` in `CLAUDE.md` (or your tool's entry-point file) to match the new name.

---

## How This Works

Agents are specialized roles, each with a `skills.md`. By default, all routing flows through the **Coordinator** and bounded cross-agent consultation is enabled under Coordinator control.

```
[VibeCoder] → [CodeBase Analyzer] → [System Design] → Spec → [Red-Team] → Software Architect → [Database] → TDD → Programmer → [QA/E2E] → TestRunner → Code Review → [Refactor] → Security → [DevOps] → [Docs] → Done
```

- `[VibeCoder]` is an optional starting point — say "switch to vibecoder" or `/agent vibecoder` to prototype fast, then promote to the full pipeline when ready
- Software Architect conditionally produces an **Implementation Outline** or explicit SKIP before tasks.md generation
- `[Observer]` is passive and active across all stages when enabled
- `[...]` stages are optional; dispatched by Coordinator when spec/ADR triggers them or when you specifically ask for them

---

## Starting the Pipeline

Use `<AI_DEV_SHOP_ROOT>/framework/operations/pipeline-quickstart.md` as the source of truth for:

- startup sequencing
- slash/manual pipeline entrypoints
- blocking human checkpoints

The minimum startup rule still holds: confirm `<AI_DEV_SHOP_ROOT>`, start existing codebases with CodeBase Analyzer when needed, and do not send work past Spec or ADR approval gates without the required human checkpoint.

---

## Invoking the Pipeline

Operator entrypoints live in `<AI_DEV_SHOP_ROOT>/framework/operations/pipeline-quickstart.md`.

- Claude Code: slash commands are the preferred entrypoint.
- Codex CLI, Gemini CLI, Claude.ai, and generic LLM hosts use the matching `framework/slash-commands/*.md` template content manually.
- Keep the command surface thin at the root; expand details in the quickstart doc instead of here.

---

## Agents

Use `<AI_DEV_SHOP_ROOT>/framework/routing/agent-index.md` for the full agent roster, role summaries, and persona file entrypoints.

Use `<AI_DEV_SHOP_ROOT>/framework/routing/skills-registry.md` for shared-skill ownership and reuse mapping.

---

## Agent Direct Mode — Shared Rules

These rules apply to every agent when operating in Agent Direct Mode (invoked via `/agent <name>` or equivalent phrasing):

- **Operate at full capability.** All skills, tools, and outputs are available — no features disabled.
- **Proceed with available context.** Do not block because a pipeline artifact is missing; note the gap and continue with the best available context.
- **Cross-agent clarification is allowed.** A direct agent may request another specialist's view when needed.
- **Label every response.** Use `AgentName(Direct):` in normal Direct Mode and `AgentName(Consensus):` when consensus-enabled Direct Mode is active.
- **Output is pipeline-valid.** When the user returns to Coordinator flow, completed direct work is treated as a completed stage.
- **VibeCoder exception.** VibeCoder output is exploratory unless the user or Coordinator explicitly promotes it.
- **Coordinator observes silently.** The Coordinator tracks state and memory but does not route or interrupt unless addressed directly.

### Consensus And Consultation

Detailed Agent Direct consensus and cross-agent consultation rules live in `<AI_DEV_SHOP_ROOT>/framework/operations/interaction-modes.md`.

- `/agent <name> consensus` enables the active direct agent to use Swarm Consensus for high-level debatable questions.
- Consultation mode is default ON; Coordinator remains router of record, one owner stays accountable, and consultation is advice-only unless escalated.

### Debate Routing Guard (Blocking)

Detailed routing guards live in `<AI_DEV_SHOP_ROOT>/framework/operations/routing-guards.md`.

When the user asks for a debate, uses `/debate`, asks for a "2 round debate", or requests multiple agents/models to argue a question, default to **Swarm Consensus debate with external peer LLM CLIs**; show the resolved or planned **model name/version** first, and CLI version strings are diagnostics only.

- Platform subagents, current-LLM helper agents, repo-persona consultations, and same-family child agents are not the default route for debate requests.
- Do not silently fall back to platform subagents.

### Cowork Routing Guard

When the user asks multiple LLMs to change files together, route bounded collaborative implementation to `<AI_DEV_SHOP_ROOT>/framework/slash-commands/cowork.md`, not `/debate` or `/audit-work`; unbounded or full-delivery work still routes to the normal pipeline.

## Delegated Agent Bootstrap (Required)

When the Coordinator spawns any delegated subagent (parallel worker, subprocess, forked-context agent, or similar), it must resolve the repo agent persona first and explicitly bootstrap that persona in the spawn prompt.

Required bootstrap steps:

1. Resolve the repo agent profile that matches the delegated task using `<AI_DEV_SHOP_ROOT>/skills/coordination/SKILL.md`.
2. Instruct the spawned subagent to read the canonical persona file before any work:
   `Read <AI_DEV_SHOP_ROOT>/agents/<resolved-agent>/skills.md before any work.`
3. Explicitly name any task-activated conditional skills for that task.
4. Include the stage-specific context required by `<AI_DEV_SHOP_ROOT>/framework/workflows/multi-agent-pipeline.md`.
5. Require the subagent to stop and report if the persona file is missing or unreadable.
6. Require the subagent to confirm in its first reply that the persona file was loaded.

The Coordinator must not assume delegated subagents automatically inherit the correct repo persona bootstrap from thread context alone. The canonical persona spec for delegated work is the agent's existing `skills.md` file under `<AI_DEV_SHOP_ROOT>/agents/`.
Apply the detailed delegated naming and validity guard in `<AI_DEV_SHOP_ROOT>/skills/coordination/SKILL.md`. Missing persona-load confirmation makes delegated output invalid; claiming a reserved pipeline agent name without it is a mandatory blocker.

---

## Shared Rules (All Agents)

- **Specs are ground truth.** Downstream work must reference the active spec version and hash.
- **Spec provider is explicit.** Resolve the active planning provider from `<AI_DEV_SHOP_ROOT>/framework/spec-providers/active-provider.md` before assuming filenames, commands, or readiness gates for the spec surface.
- **The constitution governs architecture.** Spec, Red-Team, and Software Architect must use `<ADS_PROJECT_KNOWLEDGE_ROOT>/governance/constitution.md`. The toolkit ships the default template at `<AI_DEV_SHOP_ROOT>/framework/templates/bootstrap/constitution-template.md`.
- **`[NEEDS CLARIFICATION]` blocks Software Architect dispatch.**
- **The handoff contract is mandatory.** Every artifact includes inputs used, output summary, risks, and suggested next assignee.
- **Framework source files are read-only during normal feature work.** Keep project-owned writes in `<ADS_PROJECT_KNOWLEDGE_ROOT>/specs/`, `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/`, `<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/`, `<ADS_PROJECT_KNOWLEDGE_ROOT>/memory/`, `<ADS_PROJECT_KNOWLEDGE_ROOT>/governance/`, `<ADS_PROJECT_KNOWLEDGE_ROOT>/meta/`, and `<ADS_PROJECT_KNOWLEDGE_ROOT>/tmp/` unless the user explicitly asks to keep state inside the toolkit for compatibility.
- **Classify artifact intent before saving.** Required pipeline artifacts go to `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/` automatically. Optional retained reports require an explicit user save choice. Scratch prompts, raw logs, temporary captures, and other session-only artifacts go to `<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/` by default.
- **Fix upstream intent, not downstream drift.** If code, tests, or architecture diverge from the spec, route the issue back to the owning stage instead of patching around it.
- **Evidence over invention.** Do not present guesses or memory as fact; if a claim is not grounded in inspected artifacts, tool output, or cited sources, mark uncertainty or say you do not know. See `<AI_DEV_SHOP_ROOT>/framework/governance/anti-hallucination-policy.md`.
- **Debug mode exists.** Toggle with `debug on` / `debug off`; see `<AI_DEV_SHOP_ROOT>/framework/workflows/trace-schema.md`.

---

## Reference Docs

Use these files for operating detail instead of expanding this file:

- Spec-provider contract and active provider selection: `<AI_DEV_SHOP_ROOT>/framework/spec-providers/active-provider.md`, `<AI_DEV_SHOP_ROOT>/framework/spec-providers/core/provider-contract.md`, `<AI_DEV_SHOP_ROOT>/framework/spec-providers/core/provider-selection.md`
- Pipeline startup, command entrypoints, and checkpoints: `<AI_DEV_SHOP_ROOT>/framework/operations/pipeline-quickstart.md`
- Startup block wording and layout: `<AI_DEV_SHOP_ROOT>/framework/operations/startup-info.md`
- Plain-language explanation pattern for users: `<AI_DEV_SHOP_ROOT>/framework/operations/plain-language-explanations.md`
- Interaction modes and routing guards: `<AI_DEV_SHOP_ROOT>/framework/operations/interaction-modes.md`, `<AI_DEV_SHOP_ROOT>/framework/operations/routing-guards.md`
- Capability verification and subagent defaulting: `<AI_DEV_SHOP_ROOT>/harness-engineering/runtime/capability-verification.md`, `<AI_DEV_SHOP_ROOT>/harness-engineering/runtime/subagent-usage-policy.md`
- Pipeline flow and stage context: `<AI_DEV_SHOP_ROOT>/framework/workflows/multi-agent-pipeline.md`
- Coordinator behavior and routing guardrails: `<AI_DEV_SHOP_ROOT>/agents/coordinator/skills.md`
- Routing decision tree and cycle summary format: `<AI_DEV_SHOP_ROOT>/skills/coordination/SKILL.md`
- Convergence and escalation policy: `<AI_DEV_SHOP_ROOT>/framework/governance/escalation-policy.md`
- Anti-hallucination and evidence rules: `<AI_DEV_SHOP_ROOT>/framework/governance/anti-hallucination-policy.md`
- Knowledge routing and memory writes: `<AI_DEV_SHOP_ROOT>/framework/governance/knowledge-routing.md`
- Session continuity and resume ledger rules: `<AI_DEV_SHOP_ROOT>/harness-engineering/runtime/session-continuity.md`
- Experimental validation disclosure mandate: `<AI_DEV_SHOP_ROOT>/harness-engineering/runtime/experimental-validation.md`
- Pre-completion and loop-detection tripwires: `<AI_DEV_SHOP_ROOT>/harness-engineering/runtime/tripwires.md`
- Path and artifact conventions: `<AI_DEV_SHOP_ROOT>/framework/workflows/conventions.md`
- Pipeline state and job lifecycle: `<AI_DEV_SHOP_ROOT>/framework/workflows/pipeline-state-format.md`, `<AI_DEV_SHOP_ROOT>/framework/workflows/job-lifecycle.md`, `<AI_DEV_SHOP_ROOT>/framework/workflows/recovery-playbook.md`
- Agent roster and persona entrypoints: `<AI_DEV_SHOP_ROOT>/framework/routing/agent-index.md`
- Skills registry: `<AI_DEV_SHOP_ROOT>/framework/routing/skills-registry.md`
- Golden sample handoff chain: `<AI_DEV_SHOP_ROOT>/framework/examples/golden-sample/README.md`
