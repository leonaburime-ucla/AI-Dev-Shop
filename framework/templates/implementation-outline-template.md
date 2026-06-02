# Implementation Outline: <feature-name>

- Spec: SPEC-<id> v<version> (hash: <sha256>)
- ADR: ADR-<id>
- Status: PRODUCED | SKIPPED
- Trigger result: <trigger names OR "No triggers matched">
- Date: <ISO-8601 UTC>
- Author: Software Architect

> Use this artifact only for post-ADR, pre-tasks structure. It defines module boundaries, public/exported contracts, wiring, data boundaries, and critical invariants. It must not contain pseudo-code, private helper inventories, or task sequencing.

## Skip Record

Complete this section only when `Status: SKIPPED`.

`Implementation Outline: SKIP - <reason and triggers checked>`

Reason:
- <Why the ADR alone is enough for Coordinator to generate tasks safely>

Triggers checked:
- Boundary Cross: no
- Contract Change: no
- System Wiring: no
- Data And Persistence: no
- Brownfield Dependency: no
- Reverse-Spec Or Migration: no
- Critical Cross-Boundary Invariant: no
- Parallelization Ambiguity: no

## Trigger Decision Matrix

Complete this section when `Status: PRODUCED`.

| Trigger | Applies? | Evidence | Source Trace |
|---|---:|---|---|
| Boundary Cross | yes/no | <module/domain boundary evidence> | <AC/ADR/blueprint/ref> |
| Contract Change | yes/no | <public/exported/API/event contract evidence> | <AC/ADR/ref> |
| System Wiring | yes/no | <queue/webhook/job/service/package wiring evidence> | <AC/ADR/ref> |
| Data And Persistence | yes/no | <schema/ownership/migration/reconciliation evidence> | <AC/ADR/ref> |
| Brownfield Dependency | yes/no | <legacy contract/consumer evidence> | <analysis/reverse-spec/ref> |
| Reverse-Spec Or Migration | yes/no | <source behavior to target mapping evidence> | <manifest/coverage/ref> |
| Critical Cross-Boundary Invariant | yes/no | <invariant evidence> | <AC/ADR/ref> |
| Parallelization Ambiguity | yes/no | <why task phases/[P] need extra structure> | <ADR/ref> |

## Module Map

| Module/Domain | Owns | Responsibility | Public Contracts | Dependencies | Notes |
|---|---|---|---|---|---|
| <name> | <team/domain/system> | <single responsibility> | <contract IDs> | <allowed dependencies> | <constraints> |

## File Map

List files that establish a module boundary or house public/exported contracts. Do not list incidental private helper files.

| File Path | Module | Creates / Changes | Public Contracts Housed | Responsibility | Why This Separation Exists | Notes |
|---|---|---|---|---|---|---|
| `src/.../<file>` | <module> | creates/changes | <contract IDs> | <file-level responsibility> | <boundary/contract reason> | <constraints> |

## Contract Map

Include public/exported functions, interfaces, APIs, events, webhooks, SDK/CLI surfaces, and provider-facing contracts. Do not list private helpers unless tagged `[internal-invariant]`.

| Contract ID / Name | File | Owner Module | Kind | Why Needed | Job | Inputs | Outputs | Validation | Errors | Side Effects | Spec/ADR Trace | Test Expectation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C-001 <name> | `src/.../<file>` | <module> | API/exported function/event/etc. | <why this contract must exist> | <one job> | <shape/type> | <shape/type> | <preconditions/rules> | <typed errors/failure modes> | <I/O, writes, events, external calls, or none> | <AC/ADR/ref> | <contract/integration/unit expectation> |

## Wiring Map

| Flow ID | Source | Transport/Call Type | Target | Payload/Contract | Ordering/Retry/Idempotency | Failure Handling | Trace |
|---|---|---|---|---|---|---|---|
| W-001 | <module> | <direct call/event/queue/webhook/job/etc.> | <module/system> | <contract ID> | <constraints> | <expected behavior> | <AC/ADR/ref> |

## Data And Side-Effect Boundaries

| Boundary | Owner | Reads | Writes | Side Effects | Consistency / Transaction Rule | Migration / Dual-Write Path |
|---|---|---|---|---|---|---|
| <table/store/external system> | <module/domain> | <who may read> | <who may write> | <events/webhooks/logs/etc.> | <atomicity/idempotency/order rule> | <N/A or path> |

## Critical Invariants

| Invariant ID | Scope | Rule | Reason | Enforcement Surface | Test Expectation | Trace |
|---|---|---|---|---|---|---|
| INV-001 | <modules/records/tenants/etc.> | <must always hold> | <corruption/security/parity reason> | <contract/module/boundary> | <test type> | <AC/ADR/ref> |
| INV-002 | `[internal-invariant]` <unit/scope> | <load-bearing internal rule> | <why internal detail is justified> | <module/function boundary> | <test type> | <AC/ADR/ref> |

## Brownfield / Migration Mapping (if applicable)

| Source Behavior / Contract | Target Module / Contract | Preserve / Change | Characterization Evidence | Migration Safety Note |
|---|---|---|---|---|
| <legacy behavior> | <target module/contract> | <preserve/change with reason> | <test/report/ref> | <rollback/compatibility/backfill note> |

## Test Expectations

- Contract tests: <required suites and contract IDs>
- Integration tests: <flows, transports, persistence boundaries>
- Property/invariant tests: <invariant IDs>
- Characterization tests: <if applicable>
- Explicitly N/A suites with reason: <suite -> reason>

## Downstream Handoff Notes

- Coordinator task-generation constraints: <phase, dependency, or parallelization notes>
- TDD focus: <outcome matrix, contract tests, or invariant tests to prioritize>
- Programmer architecture audit focus: <contracts, wiring, or data boundaries that must be checked>
- Open risks or ambiguities: <none or list>
