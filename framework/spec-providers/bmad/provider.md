# BMAD Provider

- provider: `bmad`
- status: `scaffolded`
- default: `false`

## User Note

This provider profile has not been tested end-to-end in this repo yet.

## Scope

This provider adapts BMAD's planning and story workflow into the AI Dev Shop pipeline.

AI Dev Shop core still owns:
- constitution enforcement
- red-team review
- architecture ADR output
- downstream TDD, implementation, review, and security stages

## Source Basis

This profile is based on BMAD's published workflow map and setup docs, not on an in-repo validated feature run yet.

## Command Surface

Common BMAD planning entrypoints:
- `bmad-create-prd`
- `bmad-create-ux-design`
- `bmad-create-architecture`
- `bmad-create-epics-and-stories`
- `bmad-check-implementation-readiness`
- `bmad-create-story`

## Native Artifact Contract

| Role | BMAD Surface |
|---|---|
| `spec_entrypoint` | `PRD.md` |
| `spec_supporting_artifacts` | optional `ux-spec.md`, epic files, story files, and project-context documents when used |
| `clarification_surface` | PRD/story elaboration and workflow follow-up; no fixed AI Dev Shop marker syntax assumed |
| `readiness_artifact` | implementation-readiness decision plus the approved PRD/architecture/story set |
| `hash_anchor` | `PRD.md` |
| `architecture_inputs` | `PRD.md`, optional `ux-spec.md`, `architecture.md`, optional project context |
| `delivery_plan_inputs` | epic files plus story files |
| `parallelism_syntax` | no native AI Dev Shop `[P]` marker assumed; parallel-safe work must be inferred from epic/story boundaries |

## Translation Notes

To fit AI Dev Shop:
- record `PRD.md` as `spec_entrypoint_path`
- treat `ux-spec.md` and project-context material as supporting planning artifacts when present
- treat `architecture.md` as provider-native architecture input before writing AI Dev Shop `adr.md`
- treat epic/story files as provider-native delivery-plan input before writing or validating AI Dev Shop `tasks.md`

If a BMAD install writes artifacts under a provider-owned output area, keep those native artifacts in place and mirror only the AI Dev Shop retained artifacts into `framework/reports/pipeline/<NNN>-<feature-name>/`.

## Known Gaps

- Not tested end-to-end in this repo yet
- Exact BMAD output paths may vary by installation and module configuration
- Translation from epic/story files into AI Dev Shop task phases remains a maintainer decision, not an automated rule
