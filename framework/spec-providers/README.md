# Spec Providers

This folder separates the upstream planning/spec framework from the rest of the AI Dev Shop pipeline.

Use it when you want:
- `speckit` as the default planning surface
- the option to swap to another planning surface such as `openspec` or `bmad`
- provider-specific docs, commands, naming, and artifact assumptions contained in one place instead of scattered through core workflow files

## Layout

```text
framework/spec-providers/
  active-provider.md
  core/
    provider-contract.md
    provider-selection.md
  speckit/
    provider.md
  openspec/
    provider.md
  bmad/
    provider.md
```

## Core Rule

The AI Dev Shop pipeline consumes provider roles, not provider branding.

At minimum, every provider must define:
- what artifact acts as the spec entrypoint
- what supporting planning artifacts are part of the spec surface
- where unresolved clarification decisions live
- what artifact proves planning readiness
- how that provider maps into AI Dev Shop's downstream Architect, TDD, and Programmer stages

## Default

The active provider is recorded in `framework/spec-providers/active-provider.md`.

Current default:
- `speckit`

## Current Status

- `speckit` is the only provider exercised end-to-end in this repo today.
- `openspec` is scaffolded here but not yet tested end-to-end in this repo.
- `bmad` is scaffolded here but not yet tested end-to-end in this repo.

## Compatibility Shims

This refactor introduces a provider boundary first. Existing Speckit-oriented files under `framework/templates/` and `framework/slash-commands/` remain in place as compatibility shims while the rest of the toolkit is migrated to read from this folder.
