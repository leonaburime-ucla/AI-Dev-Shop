---
name: test-design
version: 1.0.0
last_updated: 2026-02-22
description: Use when designing tests, building requirement-to-test matrices, selecting test types, certifying test coverage against a spec, or detecting test drift after spec changes.
---

# Skill: Test Design

Tests in this system are not just verification — they are a second encoding of the spec. The TDD Agent's job is not to check that code works; it is to translate each requirement, invariant, and edge case into an executable assertion before any implementation exists. Tests are the spec made runnable.

## The Two Roles Tests Play

**Specification role (TDD Agent)**: Write tests before code. Each test is a precise statement of what the system must do, derived directly from the spec. Tests are written against a specific spec version and hash — they certify what they were written against.

**Verification role (TestRunner Agent)**: Execute tests after implementation. Report pass/fail evidence. Identify failure clusters. Route results to Coordinator.

These are distinct jobs. The TDD Agent does not run tests against finished code. The TestRunner Agent does not write new tests.

## Requirement-to-Test Matrix

Before writing a single test, build the matrix:

| Spec Ref | Type | Test Description | Priority |
|---|---|---|---|
| REQ-01 | Acceptance | Invoice creation p99 latency ≤ 500ms under 100 concurrent requests | High |
| REQ-02 | Acceptance | 422 + CUSTOMER_NOT_FOUND when customer ID does not exist | High |
| INV-01 | Invariant | Invoice total always equals sum of line item subtotals | High |
| INV-02 | Invariant | Paid invoice cannot transition to pending | High |
| EC-01 | Edge Case | Line item with quantity 0 is rejected with validation error | Medium |
| EC-02 | Edge Case | Duplicate submission with same idempotency key returns original, not duplicate | High |

Every requirement must have at least one test. Every test must trace to a requirement. No orphan tests. No untested requirements.

## Test Types and When to Use Each

**Unit Tests**
- Target: single function, class, or module in isolation
- Cover: logic invariants, computation correctness, state transitions
- Mock: all external dependencies
- Priority: invariants first, then core business logic
- Goal: fast, deterministic, no I/O

**Integration Tests**
- Target: boundary contracts between modules or services
- Cover: API contracts, database interactions, event publishing/consuming
- Mock: third-party external services only (not internal boundaries)
- Priority: high-risk integration points, auth flows, data persistence
- Goal: verify modules work together as specified

**Regression Tests**
- Target: previously failing behavior that was fixed
- Cover: exact scenario that caused the failure
- Never delete: regression tests are permanent guards
- Add immediately when a bug is found, before fixing

**Acceptance Tests**
- Target: user-visible behavior from the outside
- Cover: acceptance criteria in the spec, happy path + critical failures
- Written in behavior terms, not implementation terms
- These are what the Convergence Threshold is measured against

## Test File Naming Convention (Required)

## Test Directory Convention (Required)

Place tests in type-specific directories:

- Unit tests: `__tests__/unit/`
- Integration tests: `__tests__/integration/`
- E2E tests: `__tests__/e2e/`

Examples:

- `__tests__/unit/req-001.submit-order.unit.test.ts`
- `__tests__/integration/req-004.model-selection.integration.test.ts`
- `__tests__/e2e/chat-sidebar.e2e.test.ts`

If a repository has an approved existing convention that differs, the override must be documented in `project-knowledge/memory/project_memory.md` and referenced in the certification output. Without an explicit override, this directory rule is mandatory.

Use explicit test-type suffixes in filenames:

- Unit tests: `*.unit.test.ts`
- Integration tests (including internal contract/integration boundary checks): `*.integration.test.ts`
- E2E/browser tests: `*.e2e.test.ts`

Examples:

- `req-001.submit-order.unit.test.ts`
- `req-004.model-selection.integration.test.ts`
- `chat-sidebar.e2e.test.ts`

If a repository has an approved existing convention that differs, the override must be documented in `project-knowledge/memory/project_memory.md` and referenced in the certification output. Without an explicit override, this naming rule is mandatory.

## Test Certification Protocol

Every test suite must include a certification record. This is the mechanism that prevents "green tests, wrong behavior." Use `<AI_DEV_SHOP_ROOT>/templates/test-certification-template.md` as the starting point.

```
# Test Certification
Spec ID:      SPEC-001
Spec Version: 1.2
Spec Hash:    sha256:<hash>
Certified by: TDD Agent
Certified at: 2026-02-21T15:00:00Z
Coverage gaps: EC-03 (currency conversion failure) — deferred, awaiting product decision
```

The spec hash in the certification must match the hash in the spec file. CI enforces this. If the spec changes and the hash changes, all tests certified against the old hash are flagged as stale and require recertification before the next merge.

## Coverage Targets

### Coverage Terminology

- **Big Four**: `% Stmts | % Branch | % Funcs | % Lines` (in this exact order)
- **Big Five**: Big Four + `Uncovered Line #s`

### Hard Coverage Gates (non-negotiable; takes precedence over all other coverage guidance)

The following suite-level gates are mandatory and evaluated per metric, not as an average:

- **Unit test coverage:** `lines >= 98%`, `branches >= 98%`, `functions >= 98%`, `statements >= 98%`
- **Integration test coverage:** `lines >= 90%`, `branches >= 90%`, `functions >= 90%`, `statements >= 90%`
- **E2E test coverage:** `lines >= 80%`, `branches >= 80%`, `functions >= 80%`, `statements >= 80%`

If any one metric is below its gate, coverage is considered failing.

### Coverage Profile Initialization (configurable with safe defaults)

At pipeline start, Coordinator should ask the human whether to keep defaults or set custom minimums for each suite across all four metrics (lines, branches, functions, statements).

- Default Unit minimums: `98/98/98/98`
- Default Integration minimums: `90/90/90/90`
- Default E2E minimums: `80/80/80/80`

If no custom profile is provided, defaults apply automatically. Persist the active profile in `tasks.md` constraints and reference it in TestRunner output.

### Uncovered Lines Policy

- Target state is **no uncovered lines** in changed or high-priority runtime code paths.
- If uncovered lines remain, they require explicit written justification before stopping the cycle.
- Acceptable justifications are limited to concrete technical constraints (for example: unreachable defensive branch tied to runtime/environment, vendor boundary that cannot be deterministically simulated, or deprecated path pending approved removal).
- "Not enough time" or "too hard to test" are not valid justifications.

Coverage targets are risk-weighted by module class. Apply the correct threshold based on what the file does, not where it lives in the directory tree.

| Module Class | Examples | Line Coverage | Branch Coverage |
|---|---|---|---|
| Core business logic | Domain services, calculation engines, validators, state machines | 95%+ | 90%+ |
| API adapters / controllers | HTTP handlers, event consumers, queue processors | 90%+ | 85%+ |
| Orchestrators | Use-case orchestrators, pipeline controllers | 85%+ | 80%+ |
| Infrastructure adapters | Repositories, DB clients, external API clients | 80%+ | 75%+ |
| View / UI components | React components, templates, presentational-only code | 70%+ OR documented E2E coverage | — |
| Configuration / type definitions | Constants, enums, pure type files, interface-only files | Exempt | Exempt |

**Touched-file non-regression rule:** Once a file reaches its threshold, a subsequent change to that file cannot drop coverage below that threshold. A PR that regresses a file must either add tests (route to TDD) or explicitly document the regression justification in the certification record.

**Project-level override:** If the risk profile of a project justifies globally higher or lower thresholds (e.g., a payment processor requiring 100% branch coverage on business logic, or a prototype where 70% is acceptable across the board), document the override in `<AI_DEV_SHOP_ROOT>/project-knowledge/memory/project_memory.md` and reference it in the test certification record. Without a documented override, the table above governs.

**Integration and acceptance coverage (non-negotiable regardless of module class):**
- All public API contracts and database boundaries: covered by integration tests
- All acceptance criteria in the spec: covered by acceptance tests
- All concrete edge cases listed in the spec: covered by explicit scenario tests

**Blocking rule takes precedence:** failing any hard coverage gate (unit/integration/e2e) blocks progression to Code Review. High-priority gaps in core business logic or API adapters also block progression regardless of module-class discretion. In all cases, uncovered requirements and uncovered lines must be explicitly listed with rationale in the certification record.

## Writing Good Assertions

**Behavior-level, not implementation-level**
Bad: `expect(invoiceService._calculateTotal).toHaveBeenCalled()`
Good: `expect(invoice.total).toBe(150.00)`

**Clear failure messages**
Bad: `expect(result).toBe(true)`
Good: `expect(result.status).toBe('422'), 'Expected 422 when customer does not exist'`

**Deterministic**
No timing-dependent assertions (`setTimeout`, `Date.now()` without mocking). No assertions that depend on ordering of unordered collections. No assertions that depend on external network calls without mocking.

**Grouped by requirement**
```
describe('REQ-02: Invalid customer ID', () => {
  it('returns 422 when customer does not exist', ...)
  it('includes CUSTOMER_NOT_FOUND error code in response body', ...)
  it('does not create a partial invoice record on failure', ...)
})
```

## Drift Detection

CI must run the following check on every pull request:
1. Read the spec hash from the current spec file
2. Read the certified hash from the test certification record
3. If they differ: block merge, flag tests as stale, route to TDD Agent for recertification

This is the connective tissue that keeps specs, tests, and code in provable alignment.

## Anti-Patterns

**Writing tests after implementation**: Defeats the specification purpose. Tests written after code tend to test what the code does, not what it should do.

**Over-prescriptive internals**: Testing private methods, internal state, or implementation details creates brittle tests that break on refactoring without any behavior change.

**Missing negative paths**: Every requirement that defines error behavior needs a test for that error. Untested error paths are where production failures live.

**Flaky tests**: A test that sometimes passes and sometimes fails is worse than no test — it erodes trust in the entire suite. Investigate immediately; do not leave flaky tests in the suite.

**Copying spec hash manually**: Automate hash generation and certification. Manual copy-paste is how hashes go stale silently.

**Tests that test the mock**: If your test only verifies that a mock was called with certain arguments, you're not testing behavior — you're testing that you wrote the mock correctly.

**Inconsistent test organization**: Mixing type-specific directories with flat/misc test locations reduces discoverability and breaks suite routing. Use `__tests__/unit/`, `__tests__/integration/`, and `__tests__/e2e/` unless a documented project override exists.

**Inconsistent test suffixes**: Mixing `.test.ts`, `.spec.ts`, and type-specific suffixes hides test intent and breaks automation/reporting. Use the required suffixes (`.unit.test.ts`, `.integration.test.ts`, `.e2e.test.ts`) unless a documented project override exists.

**Overly complex tests as a suppressed signal**: A test that requires an unusually long setup block, many mocks, or convoluted arrange logic is not a test problem — it is a design signal. The function under test is doing too many things. When a test is hard to write, flag it: surface the complexity to the Coordinator and recommend the function be broken into smaller units before proceeding. Do not write a complex test to cover a complex function and move on. The difficulty is the feedback.

## Contract Testing

The ADR defines API and event contracts. Contract tests verify the implementation actually honors those contracts. These are distinct from acceptance tests (which test user-visible behavior) and unit tests (which test logic).

**When to write contract tests:**
- Any interface defined in the ADR's API/Event Contract Summary section
- Any event published or consumed across a module boundary
- Any external service integration where you control the schema

**Testing approach by contract type:**

| Contract Type | Recommended Approach | Tool Examples |
|--------------|---------------------|---------------|
| HTTP/REST API | Schema validation against OpenAPI spec | Schemathesis, Dredd |
| Consumer-driven (provider must satisfy consumer) | Consumer-driven contract tests | Pact |
| Internal event contracts | Integration test: publish event, assert consumer behavior | native test framework |
| GraphQL | Schema + query validation | graphql-inspector |

**Contract test requirements:**
- Each contract in the ADR must have at least one contract test
- Contract tests verify the shape and behavior of the interface, not the implementation behind it
- If the Architect flagged a contract as "consumer-driven," generate a Pact contract file
- If the Architect flagged "schema validation," generate tests against the OpenAPI schema
- For cross-domain boundaries, do not rely on freehand mocks as the primary signal; prefer contract fixtures/schemas derived from the ADR contract source
- If a mock is used at a boundary, validate it against the contract shape (schema/type/fixture) so tests fail on contract drift

**In the certification record**, list contract tests separately:
```
Contract Tests:
- IInvoiceRepository: integration test (see tests/contracts/invoice-repository.test.ts)
- InvoiceCreated event: schema validation (see tests/contracts/invoice-created.schema.test.ts)
```

**Gap rule:** If a contract cannot be tested (e.g., third-party API with no sandbox), document it as a High-risk gap in the certification record with justification.

**Cross-domain reliability signal:** If unit/integration suites are passing but QA/E2E repeatedly fails on cross-domain journeys, treat this as probable contract drift or over-mocking and escalate to Coordinator for contract/test redesign before continuing cycles.

---

## Property-Based Testing

Example-based tests verify specific inputs. Property-based tests verify that a *property* holds across a large range of automatically generated inputs.

**When to use property tests:**
- ACs involving ranges, bounds, or numeric computation (e.g., "total must never be negative")
- Input validation logic (e.g., "any string over 255 chars must be rejected")
- Collections: sorting, deduplication, ordering invariants
- Parsers, serializers, encoders — any round-trip guarantee ("parse(serialize(x)) === x")
- Business logic invariants that must hold regardless of input shape

**When to stick with example tests:**
- Happy path and named failure scenarios (use example tests — property tests don't read as documentation)
- Behavior defined by a fixed contract (HTTP status codes, specific error messages)
- Integration and acceptance tests — use concrete, readable examples

**How to derive a property from a spec AC:**

| AC Pattern | Property to Test |
|------------|-----------------|
| "total equals sum of line items" | For any set of line items, total === sum(items.map(i => i.price * i.qty)) |
| "quantity must be positive" | For any quantity ≤ 0, the system rejects with a validation error |
| "idempotent submission" | For any valid request, submitting it twice returns the same result |
| "no partial writes on failure" | For any input that triggers a failure, the database state is unchanged |

**Recommended libraries:**
- TypeScript/JavaScript: `fast-check` — model-based testing, arbitrary generators, shrinking
- Python: `Hypothesis` — strategy-based generation, database examples, stateful testing

**In the certification record**, list property tests separately:
```
Property Tests:
- INV-01 (invoice total invariant): fast-check property test (see tests/properties/invoice-total.property.ts)
- EC-01 (quantity validation): Hypothesis strategy test (see tests/properties/quantity.property.py)
```

---

## Coverage Gaps

When a requirement cannot be tested (missing architecture contract, unresolved spec ambiguity, external dependency not yet available):
1. Add the gap explicitly to the certification record with reason
2. Assign a risk level (High / Medium / Low)
3. Escalate to Coordinator — High-risk gaps block progression to Programmer
4. Do not proceed with implementation against untested High-risk requirements
