# Project Knowledge

Committed template and repo-local mirror of the external `ADS-project-knowledge/` workspace.

## How To Use This Mirror

- Keep `project-knowledge/` pristine and committed. Treat it as the shipped template and example surface for downstream users.
- Create a writable `ADS-project-knowledge/` workspace from this mirror when using the toolkit in a real repo. The normal layout is a sibling directory next to `AI-Dev-Shop-speckit/`.
- In exceptional local setups, a repo-root `ADS-project-knowledge/` is acceptable as long as it stays ignored by git.
- Put retained project-owned artifacts, memory, and workflow notes in `ADS-project-knowledge/`, not back into this committed mirror unless you are intentionally updating the template itself.

## Folders

- `governance/`: live project-governance surface, currently the repo-local constitution mirror and future project-specific overrides
- `memory/`: live project memory files only (`project_memory.md`, `learnings.md`, `project_notes.md`, `memory-store.md`)
- `reports/`: retained writable artifacts, benchmarks, audits, continuity logs, and pipeline outputs
- `.local-artifacts/`: ignored local-only scratch output for toolkit maintenance and local runs
- `meta/`: workspace metadata, workflow notes, and future migration/version markers
- `tmp/`: peer-readable temporary dispatch copies and other short-lived transport files

Static toolkit-control docs no longer belong here. They live under:

- `framework/` for runtime rules, routing, governance, operations, templates, and examples
- `harness-engineering/` for validators, maintainer docs, quality policies, and skills-inbox curation machinery
