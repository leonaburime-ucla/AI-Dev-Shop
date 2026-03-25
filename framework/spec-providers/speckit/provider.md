# Speckit Provider

- provider: `speckit`
- status: `validated`
- default: `true`

## Scope

This provider owns the upstream planning surface for the current default AI Dev Shop flow.

Its native artifacts are already implemented in this repo, so no translation layer is needed for day-to-day use.

## Command Surface

- `/spec`
- `/clarify`
- `/plan`
- `/tasks`
- `/implement`

## Native Artifact Contract

| Role | Speckit Surface |
|---|---|
| `spec_entrypoint` | `feature.spec.md` |
| `spec_supporting_artifacts` | `api.spec.md`, `state.spec.md`, `orchestrator.spec.md`, `ui.spec.md`, `errors.spec.md`, `behavior.spec.md`, `traceability.spec.md`, `spec-manifest.md` |
| `clarification_surface` | inline `[NEEDS CLARIFICATION: ...]` markers in the spec package |
| `readiness_artifact` | `spec-dod.md` |
| `hash_anchor` | `feature.spec.md` |
| `architecture_inputs` | approved spec package + constitution + red-team findings |
| `delivery_plan_inputs` | approved ADR + spec priorities |
| `parallelism_syntax` | `[P]` markers in `tasks.md` |

## Current Implementation Assets

The current validated assets for this provider still live in the grouped toolkit compatibility paths:

- `framework/templates/spec-system/`
- `framework/templates/adr-template.md`
- `framework/templates/research-template.md`
- `framework/templates/tasks-template.md`
- `framework/slash-commands/spec.md`
- `framework/slash-commands/clarify.md`
- `framework/slash-commands/plan.md`
- `framework/slash-commands/tasks.md`

Those paths remain valid compatibility shims while the toolkit finishes moving provider-specific implementation details under `framework/spec-providers/`.

## Readiness Rule

Architecture work cannot begin until:
- all required spec-package files are present
- `spec-dod.md` is PASS or NA throughout
- zero unresolved `[NEEDS CLARIFICATION]` markers remain

## Translation Notes

None required. This provider is native to the current toolkit behavior.
