---
name: code-review
version: 1.0.0
last_updated: 2026-02-22
description: Use when reviewing code for spec alignment, architecture violations, test quality, security surface, and non-behavioral improvement opportunities.
---

# Skill: Code Review

Tests answer "does this work?" Code review answers "is this the right change, done the right way, safe to live in the codebase long-term?" These are different questions. Passing tests are necessary but not sufficient.

Code review is the last quality gate before human sign-off. It catches what tests cannot: wrong problem solved, architectural violations, non-functional issues, and code that is correct but unmaintainable.

## What Tests Cannot Catch

This is the core value of code review. Never use it to check things the test suite already checks.

**Wrong problem solved**: Tests can pass while implementing the wrong requirement. Code review validates that what was built is what was asked for — by checking against the spec, not just the tests.

**Architectural violations**: An agent will take the path of least resistance. Putting business logic in a route handler is easier than creating a service. Code review enforces the architecture the Architect Agent defined.

**Non-functional issues**: Performance characteristics, memory leaks, missing indexes, unbounded list fetches, synchronous operations that should be async. These often don't show up in unit tests but will show up in production.

**Security surface changes**: New endpoints, new data flows, new external calls. Code review flags these for the Security Agent to review.

**"Bad but passing" code**: Code that is too complex, inconsistent with project conventions, or hard for the next agent/developer to understand. Correct code is not automatically good code.

**Missing observability**: No logging on error paths, no metrics on critical operations, no correlation IDs on distributed calls.

## Review Dimensions

Evaluate every change across all dimensions. Do not skip any.

### 1. Spec Alignment
- Does the implementation match the requirements in the active spec?
- Does every acceptance criterion have a corresponding implementation path?
- Are invariants enforced in code (not just in tests)?
- Are edge cases handled as the spec defines?
- Is any out-of-scope behavior implemented? (Scope creep)

### 2. Architecture Adherence
- Does code respect the architecture boundaries defined by the Architect Agent?
- Are dependencies pointing in the right direction (no core logic importing from infrastructure)?
- Are modules only accessed through their public API?
- Are repository/port interfaces used for external dependencies?
- Does folder structure match the chosen architecture pattern?

### 3. Test Quality
- Do tests cover the spec requirements, not just implementation details?
- Is the test certification record present and current (spec hash matches)?
- Are there tests for the unhappy paths defined in the spec?
- Are any tests asserting implementation internals instead of behavior?

### 4. Code Quality and Maintainability
- Is each function doing one thing?
- Are names accurate and domain-aligned?
- Is there duplication that should be extracted?
- Is the complexity justified by the problem?
- Will the next agent be able to understand this without reading git history?

### 5. Security Surface
- Does this change introduce new endpoints, data flows, or external calls?
- Is user input validated at the boundary?
- Are there new authorization checks required?
- Are secrets handled correctly?
- Flag for Security Agent if any of these apply.

### 6. Non-Functional Characteristics
- Are there unbounded queries (SELECT * with no LIMIT on a growing table)?
- Are expensive operations cached where appropriate?
- Are external calls timeout-protected?
- Are error paths logged with enough context to diagnose production failures?
- Are there missing database indexes for new query patterns?

## Finding Classification

Every finding must be classified. This determines whether it blocks progression.

**Required**: Must be fixed before this work can proceed. Spec misalignment, architecture violations, security surface changes, correctness issues.

**Recommended**: Should be fixed but does not block. Code quality, naming, duplication, minor complexity debt. Route to Refactor Agent.

**Optional**: Nice to have. Style preferences, minor readability. Log in project notes if worth tracking.

Never mix required and optional findings in the same severity level. The Programmer Agent must know unambiguously what blocks progression.

## Finding Report Format

```
ID:          CR-001
Severity:    Required
Dimension:   Architecture Adherence
File:        src/routes/invoices.ts:89

Finding:
Invoice total calculation logic is implemented directly in the route handler.
This violates the Clean Architecture boundary — business logic must live in the
service layer, not in HTTP handlers.

Evidence:
The Architect ADR-002 defines: "All business logic lives in service classes.
Route handlers are responsible only for parsing input, calling services,
and formatting output."

Impact:
This logic will be duplicated if invoice totals are needed in another context
(e.g., a background job). Tests for the route handler are tightly coupled to
HTTP concerns, making the business logic harder to test in isolation.

Required Action:
Move calculation to InvoiceService.calculateTotal(). Route handler calls
the service method and returns the result.

Suggested Next Route:
Programmer Agent to move logic. TestRunner to verify tests remain green.
```

## Interaction with Other Agents

**Receives from**: Coordinator, after Programmer Agent completes implementation

**Calls**: Refactor Agent to analyze Recommended findings

**Routes to Coordinator**:
- Required findings → Programmer Agent
- Architecture violations → Architect Agent (for pattern clarification or ADR update)
- Security surface changes → Security Agent
- Spec misalignment → Spec Agent

**Outputs**: Findings ordered by severity with file-level references, required vs recommended distinction, and route recommendation for each finding.

## Review Anti-Patterns

**Rubber stamping**: Approving without reviewing each dimension. The value of code review is proportional to the rigor of the review.

**Style nitpicking as blockers**: Personal style preferences are not Required findings. If the code is readable and consistent with project conventions, style differences are at most Optional.

**Reviewing without reading the spec**: Code review without the spec is just checking that the code looks reasonable, not that it does what it was supposed to do.

**Ignoring non-functional characteristics**: Correctness is necessary. So is not fetching 10,000 rows into memory on every request.

**Conflating review with refactor**: Code review identifies problems and routes them. It does not implement fixes. Fixes go back to Programmer or Refactor Agent via Coordinator.
