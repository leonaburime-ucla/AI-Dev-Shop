# AI Dev Shop Foundation

Drop this folder into any project. Point Claude Code, Codex, or Gemini at it. Tell the Coordinator what to build.

## Dropping This Into a New Project

Copy the `AI-Dev-Shop/` folder into your project root:

```bash
cp -r AI-Dev-Shop/ your-project/
```

All internal paths are already prefixed with `AI-Dev-Shop/` — nothing breaks as a subfolder.

Each tool has a file it reads automatically on startup. Add the following to the right one:

**Claude Code** — add to `CLAUDE.md` at your project root (create if missing):
```
Read `AI-Dev-Shop/AGENTS.md` for the AI Dev Shop multi-agent pipeline.
```

**Gemini CLI / OpenAI Codex** — add to `GEMINI.md` (Gemini) or `AGENTS.md` (Codex) at your project root. Paste the following into your root file:
```
Read `AI-Dev-Shop/AGENTS.md` for the AI Dev Shop multi-agent pipeline.

# Mandatory Startup

On the first user message in this repository (including greetings), before any reply:
1. Open and read `AI-Dev-Shop/AGENTS.md`.
2. Confirm compliance in the first response with: "Booted with AI-Dev-Shop/AGENTS.md loaded.", briefly list the 3 available Coordinator modes (Review Mode, Pipeline Mode, Direct Mode), and provide a short summary of what each mode does.
3. If the file is missing or unreadable, state that explicitly and stop.

Failure to perform Mandatory Startup is a blocking error. Do not proceed with task work until corrected.
```

**Cursor** — add to `.cursor/rules/ai-dev-shop.mdc` (create if missing):
```
Multi-agent pipeline: see AI-Dev-Shop/AGENTS.md
```

**GitHub Copilot** — add to `.github/copilot-instructions.md` (create if missing):
```
Multi-agent pipeline: see AI-Dev-Shop/AGENTS.md
```

**Other** — add the same one-liner to whatever file your tool reads on startup, or include `AI-Dev-Shop/AGENTS.md` manually at the start of your first session.

Then:
1. Fill in `AI-Dev-Shop/project-knowledge/project_memory.md` with your project's conventions and gotchas
2. Start with: *"Act as Spec Agent. Here's what I want to build: [description]"*
3. Approve the spec, then let the pipeline run

The Coordinator will route between agents, enforce convergence, and stop at human checkpoints.

## How It Works

A structured multi-agent pipeline converts product intent into production code through specialized agents, each with a defined role, versioned operating procedure, and handoff contract.

```
[CodeBase Analyzer] → [Architecture Migration Plan] → Spec → [Red-Team] → Architect → TDD → Programmer → TestRunner → Code Review (+Refactor) → Security → Done
```

`[...]` stages are optional but recommended when dropping into an existing codebase. The Coordinator owns all routing. Agents never talk to each other directly. Specs are ground truth — everything downstream is traceable to a spec version and hash.

Full operating manual: **`AI-Dev-Shop/AGENTS.md`**

## Repository Layout

```
CLAUDE.md                    ← Claude Code entry point (reads AGENTS.md)
AGENTS.md                    ← Full operating manual for all agents and pipeline
├── agents/                  ← One folder per agent — lean SOP referencing skills/
│   ├── codebase-analyzer/   ← Pre-pipeline: analyzes existing codebases
│   ├── coordinator/
│   ├── spec/
│   ├── red-team/
│   ├── architect/
│   ├── tdd/
│   ├── programmer/
│   ├── testrunner/
│   ├── code-review/
│   ├── refactor/
│   ├── security/
│   └── observer/
├── codebase-analysis/       ← Analysis reports and migration plans (generated, starts empty)
├── skills/                  ← SKILL.md format — each skill is a self-contained folder
│   ├── spec-writing/SKILL.md
│   ├── test-design/SKILL.md
│   ├── architecture-decisions/SKILL.md
│   ├── code-review/SKILL.md
│   ├── security-review/SKILL.md
│   ├── refactor-patterns/SKILL.md
│   ├── coordination/SKILL.md
│   ├── context-engineering/SKILL.md
│   ├── memory-systems/SKILL.md
│   ├── tool-design/SKILL.md
│   ├── agent-evaluation/SKILL.md
│   ├── codebase-analysis/SKILL.md
│   ├── architecture-migration/SKILL.md
│   └── design-patterns/     ← 19+ patterns with TypeScript examples
│       ├── SKILL.md          ← index + pattern selection guide
│       └── references/       ← individual pattern files
├── project-knowledge/       ← Fill these in per project
│   ├── project_memory.md    ← Conventions, gotchas, tribal knowledge
│   ├── learnings.md         ← Failure log (append-only)
│   ├── project_notes.md     ← Open questions, deferred decisions
│   └── foundation.md        ← Source philosophy (read-only reference)
├── specs/                   ← Versioned specs and ADRs go here (starts empty)
├── templates/
│   ├── spec-template.md
│   ├── test-certification-template.md
│   └── adr-template.md
└── workflows/
    └── multi-agent-pipeline.md  ← Stage-by-stage pipeline with context injection rules
```

## The Twelve Agents

| Agent | Role |
|---|---|
| CodeBase Analyzer | Pre-pipeline: analyzes existing codebases, produces findings reports and migration plans |
| Coordinator | Routes between agents, owns convergence, escalates to human |
| Spec | Converts product intent into precise, versioned, testable specs |
| Red-Team | Adversarially probes approved specs for ambiguity, contradictions, untestable requirements, and missing failure modes — runs after human approval, before Architect |
| Architect | Selects architecture patterns, writes ADRs, defines module boundaries |
| TDD | Writes tests against the spec before any implementation |
| Programmer | Implements code to make certified tests pass |
| TestRunner | Executes tests and reports evidence — no interpretation |
| Code Review | Reviews spec alignment, architecture, test quality, security surface |
| Refactor | Proposes (never implements) non-behavioral improvements |
| Security | Analyzes threat surface; Critical/High findings require human sign-off |
| Observer | Watches the pipeline, surfaces systemic patterns, recommends improvements |

## Methodology

This pipeline is built on Meta-Coding (ASTRA: AI + Specs + TDD + Reference Architecture). Full source reading and philosophy: `AI-Dev-Shop/project-knowledge/foundation.md`.
