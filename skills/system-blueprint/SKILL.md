---
name: system-blueprint
version: 1.0.0
last_updated: 2026-03-03
description: Use when shaping a project at macro level before feature specs: define domains/components, ownership boundaries, integration map, and spec decomposition plan.
---

# Skill: System Blueprint

This skill produces a macro-level architecture planning artifact before detailed feature specs.

## Purpose

Provide a high-level system layout so Spec Agent knows what to spec and at what granularity.

- This is problem-space and system-shape planning.
- This is not a feature-level ADR.
- This does not make binding micro-level implementation decisions.

## When to Use

Run before Spec when one or more are true:

- Multi-domain system or unclear bounded contexts.
- Unclear ownership of data or integration boundaries.
- Expected parallel team/slice delivery.
- Greenfield product with uncertain system decomposition.

## Inputs

- Product vision / vibe output / discovery notes.
- Constraints: compliance, latency, reliability, budget, timeline.
- Existing architecture context (if extending an existing system).

## Required Output

Write one artifact using `<AI_DEV_SHOP_ROOT>/templates/system-blueprint-template.md` to:

`<AI_DEV_SHOP_ROOT>/reports/pipeline/<NNN>-<project-or-feature>/system-blueprint.md`

The output must include:

1. Macro components/domains and responsibilities.
2. Ownership boundaries and integration map.
3. High-level runtime/data topology.
4. Explicit risks and unknowns.
5. Spec decomposition plan (what spec packages to write next).

## Guardrails

- Do not produce a feature-level ADR.
- Do not lock low-level implementation patterns.
- Keep stack direction non-binding unless a hard constraint already exists.
- Use `[OWNERSHIP UNCLEAR]` markers where needed; unresolved markers block Spec decomposition approval.

## Handoff Contract

- Inputs used
- Blueprint summary
- Risks/open unknowns
- Recommended next assignee: Spec Agent
