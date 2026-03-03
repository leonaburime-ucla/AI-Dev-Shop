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

This skill applies to any module containing decision logic, data transformation, or side effects — regardless of what architectural layer or pattern name it carries.

**UI / Presentation Layer Exemption:** Declarative rendering code (React components, templates, view helpers) is exempt from the strict branch-extraction rules, CC limit, and named-predicate requirements. Simple conditional rendering (`isLoaded && !error && <Component />`) is idiomatic and should not be refactored into helper functions. UI coverage is governed by the lower threshold in `<AI_DEV_SHOP_ROOT>/skills/test-design/SKILL.md` (70%+ line, or documented E2E coverage) — not by the stricter rules in this skill.

The risk-weighted coverage thresholds in `<AI_DEV_SHOP_ROOT>/skills/test-design/SKILL.md` and the scope rules here are co-designed: strict rules + high thresholds for logic-bearing code; lighter rules + lower thresholds for UI. Both must be applied together.

- Do not duplicate framework-specific composition rules here.

## Coverage-Friendly Design

The following rules apply to all in-scope modules (see Scope Boundary above). They exist to make branch, statement, function, and line coverage achievable without combinatorial test effort.

### Branch-Friendly
- Replace complex boolean chains with named predicate functions: `if (age >= 18 && hasAccount && !isSuspended)` becomes `if (isEligible(user))`.
- Use guard clauses for simple preconditions — do not extract every guard into a separate function. `if (!user) return null` stays inline.
- Reserve function extraction for complex multi-variable decisions, not single-condition checks.
- Cyclomatic complexity > 4 in any in-scope function is a hard refactor trigger. CC > 4 means full branch coverage requires combinatorial tests — this is a design defect, not a test problem.

### Statement / Line-Friendly
- No side effects in conditionals or ternaries: `const x = condition ? sideEffect() : value` is banned.
- No implicit fallthrough paths — every branch must resolve to an explicit return value or throw.
- Functions should be short enough that every statement is reachable by a focused test.

### Function-Coverage-Friendly
- Export pure decision helpers for core business rules so they can be unit-tested in isolation.
- Separate orchestration from business rules: orchestrators coordinate calls; business logic functions decide outcomes.
- Use exhaustive handling for discriminated unions: TypeScript `switch` on a union type must include a `default: const _exhaustive: never = value; throw new Error(...)` check so unhandled variants are compile errors and test signals.

### Test Seam Rules
- Every non-trivial branch must have an injectable seam (parameter-injected dependency, not global access).
- Error paths must return typed outcomes or throw typed errors — no raw `Error` or opaque string messages at module boundaries.
- Avoid instantiating singletons or service objects inside functions; inject them via parameters.

### Third-Party SDK / Opaque Error Exception
When integrating third-party SDKs (AWS, Stripe, Twilio, etc.) that throw generic or untyped errors:
- Isolate the SDK call inside a single adapter function.
- Catch the opaque error at the adapter edge only.
- Map it to a typed internal error before it leaves the adapter.
- Business logic and orchestrators must never catch raw SDK errors directly.

This preserves the broad-catch ban for all internal code while providing a contained, testable pattern for opaque external boundaries.

---

## Coverage Anti-Patterns (Banned)

These patterns prevent achieving high branch/statement/function coverage and are banned in all in-scope modules (see Scope Boundary above).

| Anti-Pattern | Why It Kills Coverage | Correct Alternative |
|---|---|---|
| Broad `catch` without typed internal error contract | Error path is untestable — no specific outcome to assert | Adapter wraps SDK call; internal errors are typed and rethrown |
| Side effects inside conditional expressions or ternaries | Branch not isolable — side effect fires on evaluation | Extract side effect; use guard clause or named function |
| Dead defensive branches (`if (x) { /* should never happen */ }`) | Branch is unreachable in tests by definition | Assert as invariant violation with typed error, or remove |
| Business logic inside framework lifecycle wrappers | Logic trapped in `useEffect`, Express middleware, or Next.js data-fetching cannot be unit tested | Extract to pure function; lifecycle wrapper calls it |
| Complex boolean chain without named predicate | Branch intent is opaque; testing requires understanding the full chain | Extract to named predicate function |
| CC > 4 without documented justification | Requires combinatorial test effort; signals mixed concerns | Extract decision logic into smaller, focused functions |

---

## Refactor Triggers (Immediate)

Refactor when any of these appear:

- Hidden dependencies (global clock/random/singletons/network).
- Functions with mixed concerns (business rule + side effect + formatting).
- Tests requiring excessive mocks or deep internal probing.
- Cyclomatic complexity > 4 in any in-scope function (see Scope Boundary above).

## Test Mapping

- Pure logic -> unit tests (`__tests__/unit/*.unit.test.ts`)
- Boundary adapters (API/storage) -> integration tests (`__tests__/integration/*.integration.test.ts`)

## References

- `references/function-signature-patterns.md`
- `references/testability-patterns-example.md`
