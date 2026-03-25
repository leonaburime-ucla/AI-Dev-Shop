# Design: Spec Provider Extraction

- Date: 2026-03-25
- Status: IMPLEMENTED

## Problem

Speckit assumptions had spread across workflow docs, command templates, validation text, and maintainer guidance. That made the toolkit harder to reuse with other planning frameworks and made Speckit look like a hidden hard dependency instead of a default provider.

## Decision

Introduce a provider boundary under `framework/spec-providers/`.

Core pipeline files now resolve:
1. the active provider
2. the shared provider contract
3. the provider-specific profile

This keeps the AI Dev Shop pipeline reusable while letting the repo default to Speckit.

## Provider Model

- `speckit` is the validated default provider
- `openspec` is scaffolded as an adapter profile
- `bmad` is scaffolded as an adapter profile

OpenSpec and BMAD are intentionally marked untested in this repo until they complete real feature runs here.

## Important Boundary

Providers own the upstream planning surface.

AI Dev Shop core still owns:
- constitution and governance
- routing
- architecture ADR output
- downstream delivery, validation, and review stages

## Migration Strategy

This change does not delete the current Speckit-oriented files under `framework/templates/` and `framework/slash-commands/`.

Instead:
- `framework/spec-providers/` becomes the source of truth for provider identity and mapping
- legacy Speckit paths remain as compatibility shims
- core docs are updated to resolve the provider boundary first

## Follow-Up Work

- move more Speckit-only implementation details physically under `framework/spec-providers/speckit/`
- validate one end-to-end OpenSpec run
- validate one end-to-end BMAD run
- add automated translator helpers if provider switching becomes common
