---
name: testable-design-patterns
version: 1.0.0
last_updated: 2026-03-03
description: Use when designing or implementing micro-level code so functions and side-effect boundaries are composable, modular, and easy to test without fragile mocks.
---

# Skill: Testable Design Patterns (Micro-Level)

Apply this skill whenever writing or reviewing code internals. This is the highest-priority micro-level rule set across Architect, Programmer, Refactor, and TDD.

## Priority Model

1. Macro architecture first: boundaries, ownership, and contracts from ADR.
2. Micro testability second: every unit inside those boundaries must be modular, composable, and easy to assert.

If macro and micro conflict, adjust the micro design while preserving macro boundaries.

## Required Design Rules

1. Use explicit boundaries: separate pure logic from side-effect adapters.
2. Inject all side effects (I/O, time, random, storage, network) through parameters.
3. Return assertion-friendly contracts: named fields and explicit actions.
4. Prefer pure deterministic logic for business rules.
5. Keep units small enough to test with focused fixtures.
6. Treat hard-to-test code as a design defect.

## Parameter Convention (Required)

Use a two-object signature for exported functions:

- First parameter: required values object
- Second parameter: optional values object with defaults (`= {}`)

```typescript
export const evaluatePolicy = (
  { policy, context }: { policy: Policy; context: RequestContext },
  { now = new Date(), traceId }: { now?: Date; traceId?: string } = {},
): PolicyDecision => {
  // ...
};
```

## Contracts and Types

- Declare explicit return types for exported boundaries.
- Document public functions with TypeDoc/TSDoc (`@param`, `@returns`, and thrown errors when applicable).
- Keep return contracts stable; avoid ambiguous nested structures.

## Scope Boundary

This skill is intentionally framework-agnostic and function-focused.

- Do not duplicate framework-specific composition rules here.

## Refactor Triggers (Immediate)

Refactor when any of these appear:

- Hidden dependencies (global clock/random/singletons/network).
- Functions with mixed concerns (business rule + side effect + formatting).
- Tests requiring excessive mocks or deep internal probing.

## Test Mapping

- Pure logic -> unit tests (`__tests__/unit/*.unit.test.ts`)
- Boundary adapters (API/storage) -> integration tests (`__tests__/integration/*.integration.test.ts`)

## References

- `references/function-signature-patterns.md`
- `references/testability-patterns-example.md`
