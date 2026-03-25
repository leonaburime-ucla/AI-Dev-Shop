# Spec Provider Contract

This document defines the boundary between an upstream planning framework and the AI Dev Shop pipeline.

The goal is simple:
- keep provider-specific rules in one place
- keep the rest of the pipeline reusable
- let the repo default to `speckit` without hardcoding Speckit assumptions everywhere

---

## Canonical Roles

Every provider must describe the same core roles, even if the native file names differ.

| Role | Meaning |
|---|---|
| `spec_entrypoint` | The primary requirements artifact downstream stages should treat as the source of truth |
| `spec_supporting_artifacts` | Additional provider-owned planning files that complete the spec surface |
| `clarification_surface` | Where unresolved scope or behavior questions live |
| `readiness_artifact` | The artifact or decision that proves the planning surface is ready for architecture work |
| `hash_anchor` | The file whose content hash should be tracked for resume and drift detection |
| `architecture_inputs` | Which provider artifacts the Architect must read before writing AI Dev Shop architecture outputs |
| `delivery_plan_inputs` | Which provider artifacts the Coordinator uses to generate or validate implementation work breakdown |
| `parallelism_syntax` | Native syntax for independent work, if the provider has one |

---

## Required Provider Fields

Each `framework/spec-providers/<provider>/provider.md` should define:

- provider id
- status: `validated` | `scaffolded` | `experimental`
- scope: what this provider owns vs what AI Dev Shop core still owns
- command surface
- spec entrypoint path pattern
- supporting artifact path patterns
- readiness gate definition
- hash anchor
- translation notes into AI Dev Shop stages
- known gaps and risks

---

## AI Dev Shop Core Ownership

The provider does not replace the whole toolkit.

AI Dev Shop core still owns:
- Coordinator routing
- Constitution enforcement
- Red-Team and Architect stages
- TDD, Programmer, TestRunner, Code Review, Security, and Docs stages
- pipeline state, retry policy, and recovery rules

Providers only own the upstream planning/spec surface and how that surface is mapped into the core pipeline.

---

## State Recording

When a run uses a provider, `.pipeline-state.md` should record at least:

- `spec_provider`
- `spec_entrypoint_path`
- `spec_readiness_artifact`

Optional but recommended:

- `spec_support_paths`
- `provider_native_root`

Existing Speckit-oriented fields such as `spec_path` remain valid compatibility fields while the toolkit finishes migration.

---

## Consumer Rules

Coordinator:
- resolve the active provider before `/spec`, `/clarify`, `/plan`, resume validation, or artifact gate checks
- do not assume `feature.spec.md` unless the active provider says so

Spec Agent:
- produce the provider-defined planning surface
- record the resolved entrypoint and readiness artifact in pipeline state

Architect:
- read the provider-defined planning surface first
- then emit the AI Dev Shop architecture artifacts required by the core pipeline

TDD and Programmer:
- consume the approved planning and architecture artifacts recorded in pipeline state
- do not guess filenames from Speckit defaults
