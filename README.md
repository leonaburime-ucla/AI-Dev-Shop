# AI Dev Shop Foundation

Drop this toolkit into a project and point your coding agent at `AGENTS.md`.

`AGENTS.md` is the runtime authority. `README.md` is setup and maintainer guidance only.

## Install

Copy the toolkit into your project root:

```bash
cp -r AI-Dev-Shop-speckit/ your-project/AI-Dev-Shop-speckit/
```

Add this line to the startup file your tool reads at the project root:

```md
Read `AI-Dev-Shop-speckit/AGENTS.md` for the AI Dev Shop multi-agent pipeline.
```

Common entry points:
- `CLAUDE.md` for Claude Code
- `GEMINI.md` or `CLAUDE.md` for Gemini CLI and Codex CLI
<!-- - `.cursor/rules/*.mdc` for Cursor -->
<!-- - `.github/copilot-instructions.md` for GitHub Copilot -->

## What This Is

AI Dev Shop Foundation is a drop-in multi-agent delivery framework for coding agents. It turns an open-ended "build this feature" request into a structured pipeline with explicit stages for analysis, spec writing, architecture, test design, implementation, review, security, and docs.

In practice, this gives a repo a repeatable way to move from idea to working code without relying on a single giant prompt or ad hoc agent behavior.

```text
[VibeCoder] -> [CodeBase Analyzer] -> [System Blueprint] -> Spec
-> [Red-Team] -> Architect -> [Database] -> TDD
-> Programmer -> [QA/E2E] -> TestRunner -> Code Review
-> [Refactor] -> Security -> [DevOps] -> [Docs] -> Done
```

- `[VibeCoder]` is an optional starting point - say "switch to vibecoder" or `/agent vibecoder` to prototype fast, then promote to the full pipeline when ready
- `[Observer]` is passive and active across all stages when enabled
- `[...]` stages are optional; dispatched by Coordinator when spec/ADR triggers them or when you specifically ask for them

## Spec Providers

The toolkit now treats the upstream planning framework as a provider.

- Default provider: `speckit`
- Swappable provider profiles: `openspec`, `bmad`
- Active provider file: `framework/spec-providers/active-provider.md`
- Provider contract: `framework/spec-providers/core/provider-contract.md`

This keeps provider-specific planning assumptions in one folder instead of spreading Speckit-only rules through the whole toolkit.

Current status:
- `speckit` is validated in this repo
- `openspec` is scaffolded but not yet tested end-to-end in this repo
- `bmad` is scaffolded but not yet tested end-to-end in this repo

## Quick Overview

- **For**: teams and solo builders who want coding agents to work through a defined software-delivery process instead of improvising
- **Does**: routes work through specialized agents like Coordinator, Spec, Architect, TDD, Programmer, Code Review, and Security
- **Produces**: durable artifacts such as specs, ADRs, task lists, test certifications, review findings, and project memory
- **Fits**: existing codebases and greenfield projects; the toolkit lives alongside your app rather than replacing it, while project-owned state lives in a sibling `ADS-project-knowledge/` folder

## Why It Exists

Most agent workflows are strong at generating code but weak at preserving intent, surfacing risks, and keeping decisions auditable. This toolkit adds:

- a runtime contract in `AGENTS.md`
- a standard pipeline from request to implementation
- a clean split between toolkit source and project-owned writable state
- clear human approval points before architecture, implementation, and shipping

## How It Works

1. Install the toolkit into your repository.
2. Point your coding tool at `AI-Dev-Shop-speckit/AGENTS.md`.
3. Confirm or switch the active spec provider in `framework/spec-providers/active-provider.md`.
4. Start in Coordinator mode or invoke a pipeline command.
5. The framework routes work through the right agents and writes project-owned artifacts under a sibling `ADS-project-knowledge/` folder.

## At A Glance

```text
Idea/request
  -> Coordinator routes work
  -> Specialists produce specs, architecture, tests, code, and reviews
  -> Humans approve key checkpoints
  -> Repository gains both implementation and a paper trail
```

## Slash Commands

Claude Code can load the built-in slash command templates:

```bash
cp -r AI-Dev-Shop-speckit/framework/slash-commands/ .claude/commands/
```

Other hosts do not support native slash commands. For those, open the matching file in `framework/slash-commands/` and paste its contents manually.

## First-Time Project Setup

- Confirm the active provider in [framework/spec-providers/active-provider.md](framework/spec-providers/active-provider.md).
- Create or allow AI Dev Shop to create a sibling `ADS-project-knowledge/` folder next to `AI-Dev-Shop-speckit/`.
- Copy [framework/templates/bootstrap/workspace-gitignore.template](framework/templates/bootstrap/workspace-gitignore.template) to `ADS-project-knowledge/.gitignore` so `.local-artifacts/` stays local by default.
- Copy the toolkit constitution template from [framework/templates/bootstrap/constitution-template.md](framework/templates/bootstrap/constitution-template.md) to `ADS-project-knowledge/governance/constitution.md`, then customize it.
- Fill in `ADS-project-knowledge/memory/project_memory.md`.
- Start with the Coordinator in Review Mode, or run `/spec` once slash commands are installed.
- Expect retained pipeline artifacts under `ADS-project-knowledge/reports/`, local scratch under `ADS-project-knowledge/.local-artifacts/`, and spec packages at the user-specified location outside the toolkit.

## Key Files

- [AGENTS.md](AGENTS.md): runtime contract, modes, routing rules
- [framework/spec-providers/active-provider.md](framework/spec-providers/active-provider.md): active planning provider and switch rules
- [framework/spec-providers/core/provider-contract.md](framework/spec-providers/core/provider-contract.md): provider boundary used by the pipeline
- [framework/workflows/multi-agent-pipeline.md](framework/workflows/multi-agent-pipeline.md): detailed stage execution rules
- [framework/workflows/conventions.md](framework/workflows/conventions.md): file placement and writable/read-only rules
- [framework/spec-providers/speckit/provider.md](framework/spec-providers/speckit/provider.md): default provider mapping and current Speckit compatibility shims
- [framework/templates/adr-template.md](framework/templates/adr-template.md): ADR template used by Architect
- [harness-engineering/README.md](harness-engineering/README.md): harness layer, validators, rollout plan, and local source notes

Agent roster note: the toolkit is extensible. `AGENTS.md` lists the current default agents, not a fixed maximum count.

## Repository Architecture

This toolkit keeps its engine files grouped while preserving a clean split between source and writable artifacts:

- **The Engine (Read-Only):** `agents/`, `skills/`, `framework/spec-providers/`, `framework/templates/`, `framework/workflows/`, `framework/slash-commands/`, and the toolkit's own `project-knowledge/` reference material are framework source. They remain read-only during normal feature work to prevent agents from accidentally overwriting pipeline rules. You can safely overwrite these folders when upgrading to a new version of the toolkit.
- **The Project Workspace (Writable):** `ADS-project-knowledge/` is the project-owned sibling workspace. Agents write retained artifacts to `ADS-project-knowledge/reports/`, memory to `ADS-project-knowledge/memory/`, the real constitution to `ADS-project-knowledge/governance/constitution.md`, local scratch to `ADS-project-knowledge/.local-artifacts/`, and future workspace metadata to `ADS-project-knowledge/meta/`.

For the host application itself, keep app-specific product docs in the host repo, not in the toolkit internals. `AI-Dev-Shop-speckit/` ships the engine and templates; `ADS-project-knowledge/` is where the toolkit stores project-owned state that should travel with the host repo.

## Architecture Defaults

- Default macro shape: modular monolith.
- Feature ownership: vertical slices when boundaries matter.
- Use hexagonal boundaries where external I/O or business-critical logic justify them.
- Use Orc-BASH for React frontends.
- Do not force architecture ceremony onto trivial CRUD, scripts, or short-lived work.

## Design Philosophy

This toolkit is a portable, self-contained set of markdown files, templates, and agent instructions that can be dropped into a repository to standardize AI behavior and project governance without external databases or complex setup. The current default planning provider is Speckit, but provider selection is now isolated under `framework/spec-providers/` so the upstream planning surface can be swapped without rewriting the rest of the pipeline.

Furthermore, this framework is built on **Harness Engineering** principles. Rather than relying purely on prompt engineering to make an AI model smarter, this toolkit provides a deterministic "harness" (state machines, durable memory files, strict routing, and validation loops) that wraps the non-deterministic LLM. It treats the agent as the Model + the Harness.

## Maintainers

- Normal feature work should not edit `agents/`, `skills/`, `framework/spec-providers/`, `framework/templates/`, `framework/workflows/`, or `framework/slash-commands/`.
- If the user explicitly asks to maintain or upgrade the toolkit itself, treat that as framework maintainer work.
- Maintainer-only rollout notes and design history live under [project-knowledge/maintainers/README.md](project-knowledge/maintainers/README.md).
- Bootstrap-only scaffolding lives under [framework/templates/bootstrap/README.md](framework/templates/bootstrap/README.md).
- Archived audit artifacts live under [project-knowledge/archive/README.md](project-knowledge/archive/README.md).
