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

## Test Certification Protocol

Every test suite must include a certification record. This is the mechanism that prevents "green tests, wrong behavior." Use `AI-Dev-Shop/templates/test-certification-template.md` as the starting point.

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

- Unit tests: 95%+ line and branch coverage on business logic
- Integration tests: all public API contracts and database boundaries
- Acceptance tests: all acceptance criteria in the spec
- Edge cases: all concrete edge cases listed in the spec

Coverage below these thresholds is not a merge blocker by itself — but uncovered requirements must be explicitly listed as gaps in the certification record with a risk assessment.

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

**In the certification record**, list contract tests separately:
```
Contract Tests:
- IInvoiceRepository: integration test (see tests/contracts/invoice-repository.test.ts)
- InvoiceCreated event: schema validation (see tests/contracts/invoice-created.schema.test.ts)
```

**Gap rule:** If a contract cannot be tested (e.g., third-party API with no sandbox), document it as a High-risk gap in the certification record with justification.

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
