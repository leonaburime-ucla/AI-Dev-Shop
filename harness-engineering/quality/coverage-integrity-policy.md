# Coverage Integrity Policy

Coverage is evidence about exercised behavior. It is not permission to weaken
the system or the measurement until a percentage passes.

## Core Rule

Never satisfy a coverage target by weakening production behavior, contracts,
tests, or coverage scope.

## Prohibited Metric Gaming

Do not take any of these actions merely to make coverage pass or appear stronger:

- add or broaden coverage-ignore directives such as Istanbul/c8 ignores,
  `# pragma: no cover`, or tool equivalents;
- exclude owned, in-scope production source files or required suites from
  coverage collection;
- lower a coverage gate, module-class threshold, or convergence threshold, or
  relabel an in-scope required suite as "not applicable," without a
  human-approved coverage-profile override recorded per
  `<AI_DEV_SHOP_ROOT>/skills/test-design/SKILL.md`;
- delete, weaken, rewrite, or replace tests or assertions;
- remove or narrow reachable defensive behavior, validation, supported wire
  formats, compatibility behavior, recovery paths, fallbacks, retries, or
  idempotency guarantees;
- write implementation-internal tests whose only value is executing lines or
  branches without asserting an observable outcome.

The motivation matters, but so does the result: a change that makes a gate pass
by hiding applicable runtime behavior is invalid even when described as cleanup.

## Required Resolution

- Exercise every reachable, behavior-bearing branch in owned, in-scope runtime
  code through an observable contract or an approved test seam.
- Prefer pure-logic extraction, boundary adapters, dependency injection,
  deterministic fakes, controlled clocks/randomness, fault injection, or a
  narrow integration harness when a path is difficult to exercise.
- Preserve supported behavior and contracts during refactoring. Refactors may
  strengthen structure, testability, and maintainability; they do not strengthen
  or narrow product capabilities.
- Route intentional capability, validation, compatibility, wire-format, or
  recovery changes through the owning spec/architecture decision and Programmer
  workflow with tests for the approved new behavior.
- Prove code is dead or out of scope before removing it. Coverage pressure alone
  is not evidence.

## Narrow Exception Contract

Existing explicit scope exemptions in
`<AI_DEV_SHOP_ROOT>/skills/test-design/SKILL.md` remain valid, including pure
type/interface files and configuration-only files. Generated code, vendored
code, compiler-proven unreachable defenses, runtime/environment-only paths that
cannot be simulated deterministically, and deprecated paths pending approved
removal may also qualify for a narrow exception.

An exception must not hide reachable business logic, a public contract,
validation, compatibility behavior, or a recovery guarantee. Record:

- the exact file and path or directive being excepted;
- why the path is outside owned runtime scope or cannot be exercised safely;
- evidence supporting that claim;
- affected contracts and residual risk;
- approver and approval date;
- owner, expiry or removal condition, and next action.

Record the exception in `tasks.md` constraints or the active test certification,
as appropriate. A specialist agent may recommend an exception but may not
self-approve one. An undocumented, malformed, expired, or over-broad exception
invalidates the coverage evidence.

## Agent Enforcement

- **TDD and QA/E2E:** write behavior-level tests through real seams; do not add
  suppressions or exclusions to make certification pass.
- **Programmer:** redesign hard-to-test boundaries without weakening behavior or
  certified tests.
- **TestRunner:** detect new or broadened suppressions/exclusions and reject
  coverage evidence that lacks a valid exception.
- **Code Inspection:** classify metric gaming or capability loss disguised as
  coverage work as a Required finding.
- **Refactor:** preserve observable behavior; propose seam extraction when
  coupling blocks tests, and route any capability change back to its owner.
- **Coordinator:** require human approval for new exceptions and route
  behavior-changing proposals to the correct upstream owner.
