# Speckit Compatibility Flow

This file is the canonical AI Dev Shop-local compatibility contract for the `speckit` provider.

It owns the strict package shape, provider-local asset paths, validation command, and the read sets that core workflow files must apply when `speckit` is active.

It is not upstream Spec Kit documentation.

## Asset Paths

- Compatibility root: `<AI_DEV_SHOP_ROOT>/framework/spec-providers/speckit/`
- Strict package templates: `<AI_DEV_SHOP_ROOT>/framework/spec-providers/speckit/templates/spec-system/`
- Mechanical validator: `python3 <AI_DEV_SHOP_ROOT>/framework/spec-providers/speckit/validators/validate_spec_package.py <spec_path>`

## Strict Package Files

All files below are created in the user-owned spec folder. Template files live under `templates/spec-system/`.

| File | Required? | Notes |
|---|---|---|
| `feature.spec.md` | Always | Primary requirements entrypoint |
| `api.spec.md` | Conditional | Needed when the feature exposes or consumes an API |
| `state.spec.md` | Conditional | Needed when the feature manages durable or stateful data |
| `orchestrator.spec.md` | Conditional | Needed when the feature has coordinator or orchestration logic |
| `ui.spec.md` | Conditional | Needed when the feature has a UI surface |
| `errors.spec.md` | Conditional | Needed when the feature defines error codes or recovery paths |
| `behavior.spec.md` | Conditional | Needed when ordering, precedence, or deduplication rules matter |
| `traceability.spec.md` | Always | Must include every REQ, AC, INV, and EC id |
| `spec-manifest.md` | Always | Package index listing present and omitted files plus stage read sets |
| `spec-dod.md` | Always | Hard gate before `/plan` |

## Spec Package Flow

When `speckit` is the active provider:

1. Ask the user where to save the spec package if the target folder is not already known.
2. Ask whether spec files should use `prefixed` or `standard` naming.
3. Create the feature folder and the matching pipeline report folder.
4. Record `spec_provider`, `spec_path`, `spec_entrypoint_path`, `spec_readiness_artifact`, `spec_support_paths`, and `spec_naming` in `pipeline-state.md`.
5. Determine which conditional files apply and record omissions in `spec-manifest.md` with concrete reasons.
6. Write `feature.spec.md` and every applicable contract file from the provider-local template root.
7. Seed `traceability.spec.md` from every REQ, AC, INV, and EC in `feature.spec.md`, plus any error or behavior rows already defined.
8. Fill `spec-manifest.md` with actual filenames, applicability, and stage read sets for Architect, TDD, and Programmer.
9. Fill `spec-dod.md`. Every item must be `PASS` or `NA` with justification.
10. Inline at most 3 `[NEEDS CLARIFICATION: ...]` markers while drafting, then resolve all of them before handoff.
11. Compute the content hash for `feature.spec.md`.
12. Run the provider-local validator and repair any failures before declaring readiness.

## Clarification Rules

- Read `spec-manifest.md` first.
- Read the actual feature spec file named there, plus any other `PRESENT` files that contain the ambiguity.
- If `spec-manifest.md` is missing, treat that as a package defect. Fall back to `feature.spec.md` only long enough to request repair.
- After clarification answers land, update every affected file, including `traceability.spec.md`, `spec-manifest.md`, and `spec-dod.md` when applicability or stage read sets changed.
- Recompute the content hash and rerun the provider-local validator.

## Architect Read Set

Before ADR work begins:

- read `spec-manifest.md`
- read every file marked `PRESENT`
- do not treat `feature.spec.md` as sufficient by itself
- run the provider-local validator when Python is available

## Task Generation Read Set

Before generating `tasks.md`:

- read `spec-manifest.md`
- read `traceability.spec.md`
- ensure every P1 AC, invariant, edge case, and present contract file has explicit task coverage or an ADR-backed deferral

## Planning Surface Gate

The Speckit compatibility gate is satisfied only when all of the following are true:

- `spec-manifest.md` exists and lists all 10 logical files with `PRESENT` or `OMITTED`
- all always-required files exist on disk
- every file marked `PRESENT` in `spec-manifest.md` exists on disk
- `spec-dod.md` contains only `PASS` or `NA`
- zero unresolved `[NEEDS CLARIFICATION]` markers remain
- traceability has no known gaps
- the implementation-readiness gate passed
- the provider-local validator exits successfully when Python is available

## Maintainer Rule

If Speckit-specific workflow behavior changes, update this file and the provider-local assets here first. Core workflow files should only reference this contract, not become a second source of truth for Speckit behavior.
