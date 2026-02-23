---
name: enterprise-spec
version: 1.0.0
last_updated: 2026-02-23
description: Overlay skill that activates on top of spec-writing for enterprise contexts. Adds cross-repository orchestration, work-management integration, role-based approval gating, shift-left specialist harnesses, closed-loop outcome feedback, and program-level spec rollup. Do NOT use this skill alone — load it alongside skills/spec-writing/SKILL.md.
overlay: true
base_skill: spec-writing
---

# Skill: Enterprise Spec (Overlay)

This skill is an overlay. It activates on top of the `spec-writing` skill when the project is classified as an enterprise context. It does not repeat what `spec-writing` already defines. Everything in `spec-writing` applies unchanged. This skill only adds concerns that do not exist at the standard spec-writing level.

**Load order**: `spec-writing/SKILL.md` first, then `enterprise-spec/SKILL.md`. Rules in this file extend and specialize — they do not override.

---

## 1. When to Activate This Skill

Activate this skill when ANY of the following is true:

- **Multi-repository scope**: The feature requires changes in more than one repository or service to be complete.
- **Work-management system in use**: A system such as Jira, Linear, Azure DevOps, or GitHub Issues at the org level tracks work items, and tickets exist or must be created for this work.
- **Multi-role approval required**: More than one organizational role (PM, Architect, Engineering, QA, Security, Infrastructure) must sign off before the feature can advance through the pipeline.
- **Portfolio-level visibility required**: The feature is part of a named program, initiative, or OKR that is tracked above the team level.
- **Compliance or audit requirement**: A formal approval trail is required by regulation, internal policy, or customer contract — e.g., SOC 2, HIPAA, PCI-DSS change management, or a customer-facing SLA.

If none of these conditions is met, use `spec-writing` alone. Do not apply enterprise process to single-team, single-repo, non-regulated work — the overhead is not justified.

---

## 2. Cross-Repository Spec Orchestration

### Scope

When a feature cannot be delivered by changes to a single repository, it is a program-level feature. Program-level features require orchestrated specs.

### Program-Level Feature Spec

The `feature.spec.md` lives at the program level. It describes the full end-to-end capability: what the system does from the user's perspective, the cross-service acceptance criteria, and the integration contracts between services. It does not describe how any individual service implements its part.

Program-level spec location: `<OUTPUT_ROOT>/specs/programs/<program-id>/<feature-spec-id>/feature.spec.md`

### Architect Agent Decomposition

After the program-level spec is approved, the Architect Agent decomposes it into repository-specific sub-specs — one per affected repository or service. The decomposition is the Architect's first deliverable, and it is itself a gated checkpoint: the Coordinator must confirm the decomposition is complete and non-overlapping before sub-spec work begins.

Each sub-spec:
- Uses the same strict-mode spec package format defined in `spec-writing` (feature.spec.md, api.spec.ts, state.spec.ts, etc.) but scoped to that repository's boundary
- Covers only what that repository owns; behavior owned by another repository is referenced, not redefined
- References the program-level spec by `SPEC-ID` — it does not duplicate requirements, only imports them by reference

Sub-spec naming convention:

```
<OUTPUT_ROOT>/specs/programs/<program-id>/<feature-spec-id>/<repo-name>/feature.spec.md
```

Example:

```
specs/programs/PROG-004/SPEC-042/payments-service/feature.spec.md
specs/programs/PROG-004/SPEC-042/notifications-service/feature.spec.md
specs/programs/PROG-004/SPEC-042/api-gateway/feature.spec.md
```

### Traceability at Program Level

The program-level spec package includes a `traceability.spec.md` that maps across repository boundaries:

```
REQ-ID | Repo | Sub-Spec File | Implementation Reference | Test Reference | Status
REQ-01 | payments-service | SPEC-042/payments-service/feature.spec.md | src/payments/InvoiceService.ts | tests/invoice.test.ts | Verified
REQ-02 | notifications-service | SPEC-042/notifications-service/feature.spec.md | src/notify/EmailDispatcher.ts | tests/notify.test.ts | Verified
```

No requirement at the program level is considered verified until its traceability row is complete and the referenced test is passing in CI.

### Integration Contracts

Integration contracts between repositories are explicit typed interfaces defined in the program-level spec, not in any individual sub-spec. They live in:

```
<OUTPUT_ROOT>/specs/programs/<program-id>/<feature-spec-id>/integration-contracts.ts
```

Example:

```typescript
// integration-contracts.ts — program-level, owned by no single repo

export interface PaymentInitiatedEvent {
  eventId: string;
  invoiceId: string;
  amountInCents: number;
  currency: string;           // ISO 4217
  initiatedAt: string;        // ISO-8601 UTC
  customerId: string;
}

export interface NotificationRequest {
  recipientId: string;
  templateId: 'PAYMENT_CONFIRMED' | 'PAYMENT_FAILED';
  payload: Record<string, string>;
  idempotencyKey: string;
}
```

Sub-specs import from `integration-contracts.ts` — they do not redefine the shapes. If a sub-spec team needs to change a shared contract, that change is a program-level spec change, requiring program-level version increment and re-approval.

### Coordinator Cross-Repo Tracking

The Coordinator tracks pipeline state per repository, not just per feature:

```
PROG-004 / SPEC-042
  payments-service       → Implementation: In Progress (iteration 2/5)
  notifications-service  → TDD: Complete, awaiting Programmer dispatch
  api-gateway            → Spec: Approved, awaiting Architect decomposition
  program-level          → Integration contracts: Approved
```

A program-level feature is complete only when every repository's sub-spec has passed Code Review and all integration contract tests are green.

---

## 3. Work-Management Integration

### Requirement-to-Work-Item Mapping

Every `REQ-*` in the spec maps to exactly one work item in the work-management system. This mapping is tracked in a `work-items.md` file that is part of the spec package.

File location: alongside `feature.spec.md` for that spec.

```markdown
# Work Items

| REQ-ID | Work Item ID | System | URL | Status | Owner |
|--------|--------------|--------|-----|--------|-------|
| REQ-01 | PROJ-1423    | Jira   | https://jira.example.com/browse/PROJ-1423 | In Progress | @alice |
| REQ-02 | PROJ-1424    | Jira   | https://jira.example.com/browse/PROJ-1424 | To Do | @bob |
| REQ-03 | GH-892       | GitHub Issues | https://github.com/org/repo/issues/892 | Open | @carol |
```

Rules:
- A requirement with no work item mapping is a blocker — it cannot advance past spec approval.
- A work item may cover multiple REQ-IDs only when those requirements form an inseparable unit of delivery. Document the reason in the work-items.md note column.
- New bugs or scope changes discovered during pipeline execution must produce new work items. Scope must not be silently absorbed into an existing item.

### Pipeline-to-Status Synchronization

Pipeline state transitions map to work item status transitions. The Coordinator is responsible for declaring these transitions in its handoff contract at each stage.

| Pipeline Transition | Work Item Status |
|---|---|
| Spec approved | In Progress (or equivalent: Active, In Dev) |
| TDD complete, tests committed | In Review (or: Code Review, PR Open) |
| Implementation complete, PR merged | Done (or: Closed, Resolved) |
| Bug found, routed back | Reopened (or: In Progress with regression label) |
| Spec rejected, needs revision | Blocked (or: On Hold, Needs Spec) |

### MCP Integration

If an MCP server for the work-management system is available in the agent's tool context, the Coordinator uses it to apply status transitions automatically at each handoff. The Coordinator must:
1. Read the current work item status before assuming state
2. Apply the transition only if the current state is the expected predecessor state (do not blindly overwrite)
3. Log the transition in the Coordinator's handoff contract output

If no MCP integration is available, the Coordinator outputs the required transitions as a structured block in its handoff contract so a human can apply them:

```
WORK ITEM TRANSITIONS REQUIRED:
  PROJ-1423 → In Progress (trigger: spec approved)
  PROJ-1424 → In Progress (trigger: spec approved)
```

---

## 4. Role-Based Approval Matrix

### Overview

In an enterprise context, "human approval" is not sufficient. Each pipeline gate requires sign-off from specific organizational roles. The Coordinator cannot advance a stage until the required approvals for that transition are recorded.

### Approval Gate Table

| Phase Transition | Required Approvers | Blocking Effect |
|---|---|---|
| Discover → Spec | Product Manager AND Tech Lead | Spec Agent dispatch is blocked |
| Spec → Design | Architect AND Security Lead | Architect Agent dispatch is blocked |
| Design → Tasks | Engineering Lead | TDD Agent dispatch is blocked |
| Tasks → Implementation | Tech Lead | Programmer Agent dispatch is blocked |
| Implementation → Review | QA Lead | Code Review dispatch is blocked |
| Review → Ship | Security Lead AND Engineering Manager | Merge and deployment are blocked |

"Blocked" means the Coordinator halts and outputs a human checkpoint — it does not attempt to proceed, guess an approval, or assume approval is implicit from prior actions.

### Tracking Approvals: approvals.md

The spec package includes an `approvals.md` file. Every approval gate that has been reached must have a corresponding row.

File location: alongside `feature.spec.md`.

```markdown
# Approvals

| Phase | Role | Approver | Date | Decision | Notes |
|-------|------|----------|------|----------|-------|
| Discover → Spec | Product Manager | Jane Doe | 2026-02-18 | Approved | |
| Discover → Spec | Tech Lead | Ali Hassan | 2026-02-18 | Approved | |
| Spec → Design | Architect | Marco Ricci | 2026-02-20 | Needs Revision | See comment: ADR-007 not referenced |
| Spec → Design | Architect | Marco Ricci | 2026-02-21 | Approved | Revision satisfied |
| Spec → Design | Security Lead | Priya Singh | 2026-02-21 | Approved | |
```

Rules:
- A "Needs Revision" decision must include a reason in the Notes column.
- A rejected decision routes back to the agent responsible for the prior stage (e.g., Spec Agent for Discover → Spec rejections, Architect Agent for Spec → Design rejections).
- The Coordinator records the rejection reason, routes back with context, and re-presents the result for approval after revision. The prior approval rows are not deleted — the full history is preserved.
- Approved rows are immutable once recorded. Do not edit them.

### Coordinator Behavior at a Gate

When the Coordinator reaches an approval gate:
1. Output a human checkpoint notification that lists: the gate name, the required approvers (by role), and the artifact requiring review (spec file path, ADR path, etc.)
2. Halt pipeline execution
3. Resume only when `approvals.md` contains approved rows for all required roles at this gate, with dates populated
4. Validate that dates are not in the future and that all required roles are present before proceeding

---

## 5. Shift-Left Role Harnesses

### Purpose

Specialist concerns — security, infrastructure, performance — are injected BEFORE tasks are generated, not discovered in code review. This is shift-left in practice: constraints are encoded early enough to prevent the need for rework.

### When the Coordinator Triggers Harness Injection

After the ADR is approved and before `tasks.md` is generated, the Coordinator evaluates the spec and ADR against three questions:

1. Does this feature touch security-sensitive paths? (authentication, authorization, input validation, external data ingestion, secrets handling, PII, financial transactions)
2. Does this feature require new or modified infrastructure? (new service, new database, new queue, new caching layer, new third-party integration, changes to deployment topology)
3. Does this feature have explicit latency, throughput, or availability requirements in the spec?

If any answer is yes, the corresponding harness is triggered. Harness outputs are appended to `tasks.md` as a "Constraints" section. The Programmer Agent cannot begin work until this section exists and is populated.

### Security Harness

**Trigger**: Feature touches security-sensitive paths as defined above.

**Process**: Security Agent reviews the spec and the ADR now — before tasks are generated. The Security Agent produces constraint annotations for specific tasks, in the format:

```
## Constraints — Security (injected by Security Agent, <date>)

TASK-03 MUST use parameterized queries. Direct string interpolation into SQL is prohibited.
TASK-05 MUST implement rate limiting at the API gateway level, not inline in the handler.
  Limit: 100 requests per minute per authenticated user.
  Violation: return HTTP 429 with header Retry-After.
TASK-07 requires auth middleware on the route. Do not implement authorization inline in the handler.
  Permitted roles: ['admin', 'billing-manager'].
TASK-09: PII fields (email, phone, address) must be masked in all log output. Use the existing LogSanitizer utility.
```

**Prohibition**: The Security Agent does not write implementation code in this phase. It writes constraint annotations on tasks. Implementation happens in the Programmer phase, constrained by these annotations.

### Infrastructure Harness

**Trigger**: Feature requires new infrastructure resources or changes to existing infrastructure topology.

**Process**: Infrastructure constraints are declared in `tasks.md` before any code is written. The Architect Agent, in coordination with the infrastructure owner, produces:

```
## Constraints — Infrastructure (injected by Architect Agent, <date>)

New resources required:
  - PostgreSQL table: payments.invoice_line_items (migration MIGS-042 must run before deployment)
  - SQS queue: payment-events-dlq (dead-letter queue for payment-events; must exist in all environments)
  - IAM role: payments-service-role with permissions: s3:GetObject on arn:aws:s3:::invoices-bucket/*

Deployment requirements:
  - Deployment tier: production-standard (2 replicas minimum, auto-scaling enabled)
  - Environment promotion order: dev → staging → production (no direct-to-production deploys)
  - Health check endpoint: GET /healthz must return 200 within 2s before traffic is routed

Environment-specific configuration:
  - PAYMENT_GATEWAY_URL is environment-specific; do not hardcode. Read from secrets manager key: /payments/gateway-url
```

**Prohibition**: The Programmer Agent must not provision infrastructure. Infrastructure resources must exist (or be declared as pre-conditions in the deployment runbook) before the Programmer Agent is dispatched.

### Performance Harness

**Trigger**: Feature has one or more latency, throughput, or availability requirements in the spec (typically expressed as p99 latency targets, requests-per-second minimums, or uptime SLAs).

**Process**: Benchmark targets are extracted from the spec and declared in `tasks.md`. The TestRunner Agent must validate against them, not merely pass/fail the functional tests.

```
## Constraints — Performance (injected from spec REQ-01, REQ-06, <date>)

Benchmark targets (TestRunner must validate):
  REQ-01: POST /invoices — p99 latency ≤ 500ms under 100 concurrent requests over 60 seconds
  REQ-06: GET /invoices/:id — p99 latency ≤ 100ms under 500 concurrent requests over 60 seconds

Measurement requirements:
  - Tests must use a load testing tool (k6, autocannon, or equivalent) — not unit test timing assertions
  - Results must be captured as artifacts in CI and attached to the PR
  - A result that exceeds the target by more than 10% is a hard failure — it blocks merge
  - A result between 0-10% over target is a warning — requires Engineering Lead acknowledgment before merge
```

**Prohibition**: Performance requirements may not be deferred to post-launch monitoring. If the benchmark target cannot be validated in CI, the target must be renegotiated in the spec before the Implementation phase begins. The target does not silently disappear.

---

## 6. Closed-Loop Outcome Feedback

When a bug, production incident, or user-reported defect is discovered after a feature has shipped, the pipeline must treat it as a structured feedback event — not an ad-hoc patch.

### Step 1 — Categorise the Gap

Every post-ship defect falls into one of two categories. Determining the correct category determines the correct fix path.

**Intent-to-spec gap**
The use case was real — a real user did something real — but the spec did not describe it. The spec was incomplete. The code did exactly what the spec said; the spec just didn't say enough.

Signs: the failing scenario is not covered by any REQ, AC, or edge case in the spec. No test exists for it because no one wrote a requirement for it.

Fix path: route to Spec Agent to add the missing requirement, acceptance criterion, and edge case. Once the spec is updated (new version, new hash), route to TDD Agent to generate the missing test. Then route to Programmer Agent to implement. Do not write code first.

**Spec-to-implementation gap**
The spec described the behavior correctly, but the code diverged from the spec. A test may or may not exist.

Signs: the failing scenario is covered by a REQ or AC in the spec. Either no test was written for it (test gap) or a test exists and it is now failing (regression).

Fix path: route to Programmer Agent with the failing test (or, if no test exists, to TDD Agent first). The implementation must be brought into alignment with the spec. Do not patch the spec to match the broken code — the spec is ground truth.

**Rule: never manually patch code to fix a bug.** A manual code patch that bypasses the spec and test cycle will be overwritten by the next AI-driven implementation run on that code path. All fixes must be expressed first as specs or tests, then as implementation. No exceptions.

### Step 2 — Record in learnings.md

Every post-ship defect is recorded in `<OUTPUT_ROOT>/project-knowledge/learnings.md` using this structure:

```
[FAILURE] <ISO-8601 date> | Gap type: intent-to-spec | spec-to-implementation
Spec: <SPEC-ID and version at time of failure>
Symptom: <What the user observed. Be specific: what they did, what they expected, what they got.>
Root cause: <Which spec section was missing (for intent-to-spec) OR which implementation diverged from which requirement (for spec-to-implementation).>
Fix applied: <For intent-to-spec: which REQ/AC/EC was added, new spec version and hash. For spec-to-implementation: which test was added or fixed, new implementation reference.>
Harness improvement: <If applicable: what constraint was added to which agent's skills.md to prevent this class of error at generation time.>
```

Example entry:

```
[FAILURE] 2026-02-19T09:14:00Z | Gap type: intent-to-spec
Spec: SPEC-042 v1.1
Symptom: User submitted an invoice with a line item quantity of -5. The API accepted it and created an invoice with a negative total. User expected a validation error.
Root cause: SPEC-042 REQ-04 specified that quantity must be > 0 in the interface comment, but no AC or edge case covered the negative-quantity rejection scenario. No test existed for it.
Fix applied: Added EC-07 (negative quantity), AC-09 (422 with INVALID_QUANTITY error), updated spec to v1.2 (hash updated). TDD Agent generated test. Programmer brought implementation into alignment.
Harness improvement: Added to spec-writing SKILL.md quality standards: "quantity and price fields must have an explicit edge case for zero and negative values with rejection behavior defined."
```

### Step 3 — Harness Improvement Threshold

If the same gap type recurs twice — two separate defects of the same category (same spec section, same class of omission) — it becomes a harness rule. A harness rule is a constraint added to the relevant agent's `skills.md` so the pattern is prevented at generation time, not caught in review or post-ship.

The Coordinator is responsible for detecting recurrence. The detection criterion: two entries in `learnings.md` with the same gap type and substantially the same root cause description.

When the threshold is met, the Coordinator opens a harness improvement task:
- Identify which agent's skills.md should receive the new constraint
- Draft the constraint in the format used in that skills.md
- Present to Engineering Lead for approval
- On approval, add to skills.md and reference the improvement in both learnings.md entries

---

## 7. Portfolio / Program-Level Spec Rollup

### When to Use

Use the program-level rollup when a feature is part of a named initiative (an OKR, a product program, a regulatory compliance program) that spans multiple feature specs, multiple teams, or multiple quarters.

### Program Spec Location and Structure

Program spec location: `<OUTPUT_ROOT>/specs/programs/<program-id>/program.spec.md`

The program spec is not a feature spec. It does not define REQ-level requirements. It defines initiative-level goals and tracks the features that collectively fulfill them.

Required contents of `program.spec.md`:

```markdown
# Program Spec: <Program Name>

Program ID:    PROG-004
Version:       1.0
Last Edited:   <ISO-8601 UTC>
Hash:          sha256:<hash>
Owner:         <Program Manager name and role>
Initiative:    <Name of parent OKR or strategic initiative>
Target Date:   <ISO-8601 date>

## Initiative Goal
<One to three sentences: what business or user outcome does this program achieve?>

## Feature Inventory

| Feature Spec ID | Feature Name | Owner Team | Status | Completion % | Blocking Issues |
|-----------------|--------------|------------|--------|--------------|-----------------|
| SPEC-042 | Invoice Creation V2 | Payments Team | In Progress | 40% | None |
| SPEC-043 | Notification Overhaul | Platform Team | Spec Approved | 0% | Waiting on SPEC-042 integration contract |
| SPEC-044 | Reporting Dashboard | Analytics Team | Discover | 0% | Spec not yet written |

## Cross-Feature Dependencies

| Dependency | Source Spec | Target Spec | Type | Status |
|------------|-------------|-------------|------|--------|
| PaymentInitiatedEvent contract | SPEC-042 | SPEC-043 | Integration contract | Approved |
| invoice_line_items schema | SPEC-042 | SPEC-044 | Shared data model | Pending |

## Shared Contracts

All shared contracts between features are defined at program level:
- integration-contracts.ts (typed event and API interfaces)
- shared-data-models.ts (shared database schema types, if applicable)

## Overall Status
<Summary: on track / at risk / blocked, with reason if not on track>
```

### Coordinator Rollup View

On request (from a program manager, Engineering Manager, or observer), the Coordinator produces a rollup view in the following format:

```
PROGRAM ROLLUP — PROG-004 — <date>

Feature              | Status          | Completion | Blocking Issues
---------------------|-----------------|------------|----------------
SPEC-042             | In Progress     | 40%        | None
SPEC-043             | Spec Approved   | 0%         | Waiting: SPEC-042 integration contract
SPEC-044             | Discover        | 0%         | Spec not written

Overall: 13% complete. SPEC-043 blocked on SPEC-042. Critical path: SPEC-042 → SPEC-043.
Target date: 2026-04-01. Current trajectory: AT RISK (SPEC-042 at 40% with 5 weeks remaining).
```

### Feature-to-Program Reference

Every individual `feature.spec.md` that is part of a program must include a Program Reference in its header metadata:

```
Spec ID:      SPEC-042
Program:      PROG-004
Version:      1.2
Last Edited:  2026-02-21T14:00:00Z
Hash:         sha256:<hash>
```

The Program field is the link that allows the Coordinator to include this feature in the rollup. A feature spec without a Program field is treated as a standalone feature and is not included in any rollup.

### Program Spec Versioning

The program spec is versioned and hashed using the same rules as feature specs. A version increment is required when:
- A feature is added to or removed from the feature inventory
- A cross-feature dependency is added, removed, or changes status
- A shared contract changes
- The target date changes

Individual feature spec changes do not require a program spec version increment — they are reflected via the status and completion fields in the feature inventory.

---

## What Belongs Where (Enterprise Additions)

This table extends the "What Belongs Where" table in `spec-writing`. Enterprise-specific artifacts only:

| Content | Location |
|---|---|
| Program-level goals, feature inventory, cross-feature dependencies | `specs/programs/<program-id>/program.spec.md` |
| Integration contracts between repositories or services | `specs/programs/<program-id>/<feature-spec-id>/integration-contracts.ts` |
| Repository-specific sub-specs | `specs/programs/<program-id>/<feature-spec-id>/<repo-name>/feature.spec.md` |
| Program-level cross-repo traceability | `specs/programs/<program-id>/<feature-spec-id>/traceability.spec.md` |
| Work item to requirement mapping | `<spec-package>/work-items.md` |
| Approval trail | `<spec-package>/approvals.md` |
| Shift-left harness constraints (appended before Programmer dispatch) | `<spec-package>/tasks.md` — "Constraints" section |
| Post-ship defect records and harness improvements | `project-knowledge/learnings.md` |

---

## Enterprise Spec Package: Required Files

An enterprise spec package extends the strict-mode spec package defined in `spec-writing`. In addition to all files required by strict mode, an enterprise spec package requires:

| File | Purpose | Required When |
|---|---|---|
| `work-items.md` | Maps every REQ-* to a work item ID, system, status, and owner | Work-management system is in use |
| `approvals.md` | Records role-based approvals at each gate, with dates and decisions | Multi-role approval is required |
| `integration-contracts.ts` | Typed interfaces for all cross-service event and API contracts | Feature spans multiple repositories |
| `traceability.spec.md` (program-level) | Cross-repo requirement-to-test mapping | Feature spans multiple repositories |
| `program.spec.md` | Initiative goal, feature inventory, shared contracts | Feature is part of a program |

A strict-mode enterprise spec package is not approved until all required files for the applicable conditions are present, complete, and internally consistent.
