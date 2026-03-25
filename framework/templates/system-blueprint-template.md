# System Blueprint: <project-name>

- Status: DRAFT | APPROVED
- Date: <ISO-8601 UTC>
- Author: System Blueprint Agent
- Scope: Greenfield | Existing codebase extension
- Next Action: Human reviews and approves blueprint boundaries before Spec decomposition

---

> Why this artifact exists: writing detailed specs before macro system shape is clear frequently creates wrong boundaries and wrong spec granularity. This blueprint aligns scope, ownership, and decomposition before spec writing.

## 1) System Goal

- Problem statement:
- Intended users:
- Business outcome:
- Non-goals:

## 2) Scope and MVP Boundary

- In-scope for MVP:
- Deferred to later phases:
- Explicit exclusions:

## 3) Macro Components / Domains

| Domain / Component | Responsibility | Owner Suggestion | Notes |
|---|---|---|---|
| | | | |

## 4) Domain Boundaries and Ownership

- Bounded contexts:
- Data ownership by domain:
- Boundary rules (what cannot be shared directly):
- [OWNERSHIP UNCLEAR] markers (if any):

## 5) Integration Map

| From | To | Contract Type (API/Event/Batch) | Criticality | Notes |
|---|---|---|---|---|
| | | | | |

## 6) Data and Runtime Topology (High-Level)

- Data shape direction (relational/document/stream + why):
- Runtime topology (frontend/backend/workers/jobs):
- External systems (payments, auth, CRM, etc.):

## 7) Technology Direction

- Suggested stack direction (optional):
- Why this direction is plausible:
- Unknowns requiring later ADR validation:

## 8) Risks and Unknowns

| Risk | Type (scope/ownership/integration/scale) | Severity | Mitigation / Next Step |
|---|---|---|---|
| | | | |

## 9) Core/Foundation Spec (P0, required)

Define the required shared foundation that must be built and merged before parallel domain slices begin.

- Required core scope:
  - repository/project shell setup
  - global routing/layout shell
  - shared runtime primitives (config/env/logging)
  - shared clients/adapters (for example DB/auth client initialization)
  - CI/test harness bootstrap needed by downstream slices
- Why this must block parallel slices:

> Hard boundary: `P0` must stay thin. It may include shared shell/runtime primitives and shared clients only. It must not include feature-specific business logic or feature-owned schema/tables.

## 10) Critical User Journeys (Cross-Domain)

List end-to-end user journeys that cross domain boundaries and must be validated after slices converge.

| Journey ID | Flow (example: Signup -> Browse -> Checkout) | Domains Touched | Criticality | QA/E2E Priority |
|---|---|---|---|---|
| | | | | |

## 11) Spec Decomposition Plan

Define which specs should be written next and at what granularity.

| Spec Package | Domain | Priority (P0/P1/P2/P3) | Why separate | Depends on |
|---|---|---|---|---|
| | | | | |

> Rule: include one explicit `Core/Foundation` package at `P0`. Domain slices (P1+) depend on it.
> Rule: if `Depends on` is non-empty, the package must be sequenced after its dependency and cannot be in the same parallel wave.
> Rule: if a package requires a foreign key or contract dependency on another domain-owned resource, list that owner in `Depends on` and place this package in a later phase.

## 12) Handoff to Spec Agent

- Approved boundaries to preserve:
- Open decisions that Spec should mark with `[NEEDS CLARIFICATION]` if unresolved:
- Recommended sequencing for spec creation:

## 13) Approval

- Human reviewer:
- Decision: APPROVED | REVISE
- Notes:
