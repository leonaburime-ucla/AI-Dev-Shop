# OpenSpec Provider

- provider: `openspec`
- status: `scaffolded`
- default: `false`

## User Note

This provider profile has not been tested end-to-end in this repo yet.

## Scope

This provider adapts OpenSpec's native planning artifacts into the AI Dev Shop pipeline.

AI Dev Shop core still owns:
- constitution enforcement
- red-team review
- architecture ADR output
- downstream TDD, implementation, review, and security stages

## Source Basis

This profile is based on OpenSpec's published docs and README, not on an in-repo validated feature run yet.

## Command Surface

Common OpenSpec entrypoints:
- `/opsx:propose`
- `/opsx:apply`
- `/opsx:archive`

Project bootstrap:
- `openspec init`
- `openspec update`

## Native Artifact Contract

| Role | OpenSpec Surface |
|---|---|
| `spec_entrypoint` | `openspec/changes/<change-id>/proposal.md` |
| `spec_supporting_artifacts` | `openspec/changes/<change-id>/specs/**` |
| `clarification_surface` | iterative edits to `proposal.md` and `specs/**`; no fixed AI Dev Shop marker syntax assumed |
| `readiness_artifact` | approved `proposal.md` + `specs/**` bundle, with `design.md` and `tasks.md` present when the project uses the full OpenSpec flow |
| `hash_anchor` | `proposal.md` |
| `architecture_inputs` | `proposal.md`, `specs/**`, optional `design.md` |
| `delivery_plan_inputs` | `tasks.md` when present; otherwise AI Dev Shop Coordinator derives a plan from approved specs/design |
| `parallelism_syntax` | no native `[P]` equivalent assumed in this profile; Coordinator may annotate parallel-safe tasks during translation |

## Translation Notes

To fit AI Dev Shop:
- record `proposal.md` as `spec_entrypoint_path`
- record the matching `specs/**` paths as supporting planning artifacts
- if `design.md` exists, treat it as provider-native architecture input before writing AI Dev Shop `adr.md`
- if `tasks.md` exists, treat it as provider-native delivery-plan input before writing or validating AI Dev Shop `tasks.md`

If this provider is activated, keep any supplemental AI Dev Shop retained artifacts under `framework/reports/pipeline/<NNN>-<feature-name>/` instead of mutating OpenSpec's folder layout.

## Known Gaps

- Not tested end-to-end in this repo yet
- Clarification marker format is not normalized to AI Dev Shop's `[NEEDS CLARIFICATION]` syntax
- Translation from OpenSpec-native tasks to AI Dev Shop `[P]` markers is still a maintainer decision, not an automated rule
