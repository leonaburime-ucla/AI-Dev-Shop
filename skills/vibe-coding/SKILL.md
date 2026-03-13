---
name: vibe-coding
version: 1.0.0
last_updated: 2026-02-27
description: Fast prototyping mode for rough, exploratory builds without full spec-first ceremony.
---

# Skill: Vibe Coding

Use this when the user wants quick-and-dirty output, is still discovering requirements, or explicitly asks to skip structured pipeline overhead.

## Purpose

Ship a rough prototype fast. Optimize for momentum and learning, not production quality.

## Operating Style

- Ask at most one clarifying question if needed to start.
- Keep scope to a single focused prototype — one idea, one slice.
- Prefer minimal files and direct implementation.
- Avoid heavy architecture, templates, and documentation unless requested.
- Work on a scratch branch or scratch directory — do not commit exploratory code to main.

## Output Expectations

- Deliver runnable code or a concrete scaffold quickly.
- Include a short "known rough edges" list.
- Mark output as exploratory and non-production by default.
- If the prototype is meant to validate product demand or usability, read `references/product-validation.md` and add the smallest possible feedback and success-signal hooks.

## Guardrails

- Do not claim production readiness.
- Do not modify security-critical auth/payment flows unless explicitly requested.
- Do not use real secrets or real PII in examples, fixtures, or config — reference `<AI_DEV_SHOP_ROOT>/project-knowledge/governance/data-classification.md` for what counts as PII.
- If the prototype should be hardened, promote to the structured pipeline: run `/spec` with the prototype as reference context. The prototype becomes input for the Spec Agent, not the spec itself.
