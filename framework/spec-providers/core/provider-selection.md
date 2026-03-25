# Provider Selection

Use this file when deciding whether a feature run should stay on the default provider or switch to another one.

## Default Rule

Use `speckit` unless one of the following is true:
- the project already uses OpenSpec natively
- the project already uses BMAD natively
- the user explicitly asks to switch providers
- the repo is standardizing on a different upstream planning framework

## Selection Heuristic

Choose `speckit` when:
- you want the strict multi-file spec package already native to this repo
- you want the least migration risk
- you need the most validated path in this toolkit today

Choose `openspec` when:
- the project already works from proposal/specs/design/tasks folders
- you want a lighter native planning surface and are comfortable translating it into AI Dev Shop downstream stages

Choose `bmad` when:
- the project already works from PRD/architecture/story artifacts
- story-driven planning is the natural handoff surface

## Mid-Feature Switching Rule

Do not silently switch providers mid-run.

If a feature already has approved planning artifacts:
1. decide whether to translate or regenerate
2. record the change in `.pipeline-state.md`
3. treat the switch as a human checkpoint

## Validation Rule

Only `speckit` is validated end-to-end in this repo today.

`openspec` and `bmad` are intentionally scaffolded here as reusable provider profiles, but they should be treated as untested in this repo until a maintainer completes a real feature run with each one.
