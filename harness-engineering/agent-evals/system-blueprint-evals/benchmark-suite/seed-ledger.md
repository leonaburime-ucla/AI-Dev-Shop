# Seed Ledger - System Blueprint Benchmark Suite

This hidden ledger describes the expected seeded issues for post-run scoring.
The System Blueprint agent under test does not see this file.

## system-blueprint-eval-1-scope-boundaries

`SBP-SEED-01`
- Seeded issue: Scope is too contradictory to decompose safely.
- Expected signal: System Blueprint escalates or asks clarification instead of inventing a hybrid solution.

`SBP-SEED-02`
- Seeded issue: Blueprint omits non-goals and explicit exclusions.
- Expected signal: System Blueprint records MVP boundary, deferred work, and exclusions.

`SBP-SEED-03`
- Seeded issue: Deferred marketplace or AI chatbot enters MVP.
- Expected signal: System Blueprint preserves declared non-goals.

`SBP-SEED-04`
- Seeded issue: Billing and Entitlements share subscription ownership without boundary decision.
- Expected signal: System Blueprint chooses an owner or marks `[OWNERSHIP UNCLEAR]`.

`SBP-SEED-05`
- Seeded issue: CRM onboarding handoff exists but is missing from integration map.
- Expected signal: System Blueprint maps required external/domain integrations.

`SBP-SEED-06`
- Seeded issue: Output turns into feature-level acceptance criteria.
- Expected signal: System Blueprint stays macro-level and avoids writing feature specs.

`SBP-SEED-07`
- Seeded issue: Offline-only and real-time centralized sync constraints conflict.
- Expected signal: System Blueprint surfaces the conflict as an unresolved blocker.

`SBP-SEED-08`
- Seeded issue: Regression guard for blueprint mentioning prior-project domains absent from the brief.
- Expected signal: System Blueprint does not import unrelated session context.

`SBP-SEED-09`
- Seeded issue: User mandates a single-app monolith for MVP.
- Expected signal: System Blueprint does not flag absence of microservices as a defect.

`SBP-SEED-10`
- Seeded issue: Admin/reporting domains are explicitly deferred in control variant.
- Expected signal: System Blueprint does not force deferred domains into MVP.

## system-blueprint-eval-2-topology-tradeoffs

`SBP-SEED-11`
- Seeded issue: Agent commits to one stack without presenting 2-3 directions and asking preference.
- Expected signal: System Blueprint runs the exploratory tradeoff checkpoint before finalizing.

`SBP-SEED-12`
- Seeded issue: Blueprint names more than three dominant quality attributes or scores them.
- Expected signal: System Blueprint names max three dominant qualities and does not score them.

`SBP-SEED-13`
- Seeded issue: Background worker/runtime path is missing from topology.
- Expected signal: System Blueprint includes high-level worker/job runtime where required.

`SBP-SEED-14`
- Seeded issue: Shared subscription data model has unresolved ownership but no marker.
- Expected signal: System Blueprint surfaces data ownership uncertainty.

`SBP-SEED-15`
- Seeded issue: Order-to-fulfillment event boundary is absent or mislabeled.
- Expected signal: System Blueprint maps API/event/batch contract type for cross-domain boundaries.

`SBP-SEED-16`
- Seeded issue: Output writes a binding ADR-style decision.
- Expected signal: System Blueprint keeps stack direction non-binding unless hard constraint already exists.

`SBP-SEED-17`
- Seeded issue: Hard no-SaaS constraint is violated by an external SaaS stack choice.
- Expected signal: System Blueprint respects hard constraints or escalates.

`SBP-SEED-18`
- Seeded issue: Regression guard for 1-5 quality-attribute scoring matrix.
- Expected signal: System Blueprint does not score quality attributes at blueprint stage.

`SBP-SEED-19`
- Seeded issue: Only two dominant quality attributes are named.
- Expected signal: System Blueprint does not force exactly three attributes.

`SBP-SEED-20`
- Seeded issue: Control variant has clear ownership for all data.
- Expected signal: System Blueprint does not invent `[OWNERSHIP UNCLEAR]`.

## system-blueprint-eval-3-decomposition-handoff

`SBP-SEED-21`
- Seeded issue: Spec decomposition has no P0 Core/Foundation package.
- Expected signal: System Blueprint defines a required P0 Core/Foundation package.

`SBP-SEED-22`
- Seeded issue: P0 includes feature-owned billing tables or business logic.
- Expected signal: System Blueprint keeps P0 thin and free of feature-specific logic/schema.

`SBP-SEED-23`
- Seeded issue: Reporting depends on Billing-owned invoice foreign key but is scheduled in the same phase.
- Expected signal: System Blueprint sequences dependent package after owner domain.

`SBP-SEED-24`
- Seeded issue: Package has API/event dependency but empty Depends on field.
- Expected signal: System Blueprint records dependencies and avoids unsafe parallelization.

`SBP-SEED-25`
- Seeded issue: Blueprint omits cross-domain critical user journeys.
- Expected signal: System Blueprint captures journeys for QA/E2E handoff.

`SBP-SEED-26`
- Seeded issue: Blueprint uses frontend/api/db horizontal slices without justification.
- Expected signal: System Blueprint defaults to vertical/domain slicing or justifies horizontal slicing.

`SBP-SEED-27`
- Seeded issue: Handoff lacks approved boundaries and open decisions for Spec.
- Expected signal: System Blueprint includes handoff contract and Spec routing guidance.

`SBP-SEED-28`
- Seeded issue: Regression guard for writing detailed feature specs instead of decomposition packages.
- Expected signal: System Blueprint produces spec package plan, not feature specs.

`SBP-SEED-29`
- Seeded issue: Horizontal Core/Foundation platform slice is explicitly justified.
- Expected signal: System Blueprint accepts justified foundation/platform slice.

`SBP-SEED-30`
- Seeded issue: Control P0 contains no feature schema.
- Expected signal: System Blueprint does not invent missing business logic in P0.
