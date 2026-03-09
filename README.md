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
- `.cursor/rules/*.mdc` for Cursor
- `.github/copilot-instructions.md` for GitHub Copilot

## Slash Commands

Claude Code can load the built-in slash command templates:

```bash
cp -r AI-Dev-Shop-speckit/slash-commands/ .claude/commands/
```

Other hosts do not support native slash commands. For those, open the matching file in `slash-commands/` and paste its contents manually.

## First-Time Project Setup

- Customize [constitution.md](project-knowledge/governance/constitution.md).
- Fill in [project_memory.md](project-knowledge/memory/project_memory.md).
- Start with the Coordinator in Review Mode, or run `/spec` once slash commands are installed.
- Expect pipeline artifacts under `reports/` and spec packages at the user-specified location outside the toolkit.

## Key Files

- [AGENTS.md](AGENTS.md): runtime contract, modes, routing rules
- [workflows/multi-agent-pipeline.md](workflows/multi-agent-pipeline.md): detailed stage execution rules
- [workflows/conventions.md](workflows/conventions.md): file placement and writable/read-only rules
- [templates/spec-system/feature.spec.md](templates/spec-system/feature.spec.md): canonical spec entry point
- [templates/adr-template.md](templates/adr-template.md): ADR template used by Architect

Agent roster note: the toolkit is extensible. `AGENTS.md` lists the current default agents, not a fixed maximum count.

## Architecture Defaults

- Default macro shape: modular monolith.
- Feature ownership: vertical slices when boundaries matter.
- Use hexagonal boundaries where external I/O or business-critical logic justify them.
- Use Orc-BASH for React frontends.
- Do not force architecture ceremony onto trivial CRUD, scripts, or short-lived work.

## Maintainers

- Normal feature work should not edit `agents/`, `skills/`, `templates/`, or `workflows/`.
- If the user explicitly asks to maintain or upgrade the toolkit itself, treat that as framework maintainer work.
- Maintainer-only rollout notes and design history live under [project-knowledge/maintainers/README.md](project-knowledge/maintainers/README.md).
- Bootstrap-only scaffolding lives under [templates/bootstrap/README.md](templates/bootstrap/README.md).
- Archived audit artifacts live under [project-knowledge/archive/README.md](project-knowledge/archive/README.md).
