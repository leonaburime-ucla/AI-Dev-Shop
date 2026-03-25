# Framework

This folder groups the toolkit-owned framework surface that used to sit at the repo root.

## Layout

- `spec-providers/` defines the active planning provider boundary and provider profiles
- `templates/` holds framework templates consumed by agents and workflows
- `workflows/` defines pipeline rules, state formats, and conventions
- `slash-commands/` holds reusable command templates for hosts that support or emulate slash commands
- `reports/` holds retained framework artifacts and pipeline outputs

## Write Rules

- Treat `spec-providers/`, `templates/`, `workflows/`, and `slash-commands/` as read-only during normal feature work.
- Treat `reports/` as writable retained output.
- Use `.local-artifacts/` for disposable local-only scratch output.
