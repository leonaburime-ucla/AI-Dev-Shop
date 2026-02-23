---
name: architecture-decisions
version: 1.0.0
last_updated: 2026-02-22
description: Use when selecting architecture patterns, writing ADRs, analyzing system drivers, evaluating tradeoffs, or advising on module and service boundaries.
---

# Skill: Architecture Decisions

Architecture is the set of constraints that governs how the system is built. The Architect Agent's job is not to pick the most technically impressive pattern, or even the pattern that best fits today's requirements — it is to pick the pattern that makes future change cheapest.

Technology moves fast. The patterns, libraries, and frameworks considered best practice today will be replaced. An architecture that locks you into today's tech stack is a liability. An architecture that makes it easy to swap a dependency, extract a service, or adopt a new approach is an asset.

**Adaptability First**: When two candidate patterns score within 10 points of each other, always choose the more adaptable one. The cost of flexibility is paid once at design time. The cost of inflexibility is paid on every future change.

There is no "best" architecture. There are only tradeoffs — and adaptability is the most important one.

## System Drivers

Before selecting a pattern, classify the system's primary drivers:

| Driver | Questions to Ask |
|---|---|
| **Complexity** | Is the business logic simple CRUD or rich domain rules? |
| **Scale** | Will read and write loads be symmetric or asymmetric? |
| **Coupling** | How many external systems integrate? Can they be swapped? |
| **Team shape** | One team or many? Feature ownership or layer ownership? |
| **Release cadence** | Deploy everything together or independently? |
| **Audit requirements** | Do you need a full history of state changes? |
| **Longevity** | Prototype or long-lived product? |
| **Adaptability** | How easily can this be replaced in 18 months? Does this pattern trap us in a specific library, framework, or cloud vendor? Can core business logic survive if the database engine, web framework, or messaging layer is swapped? |

## Pattern Selection Guide

### The Clean Architecture Family (Hexagonal / Clean / Onion)

These are 90% the same idea: dependencies point inward, core business logic has zero external dependencies, external systems connect through interfaces (ports) with swappable implementations (adapters).

**Use when**: You need to swap external dependencies (database, payment provider, email service). Long-lived products. Strong domain rules.

**Avoid when**: Simple CRUD where the interface overhead isn't justified.

**Core principle**: Your business logic must not import from your database layer, web framework, or any third-party library. Dependency injection inverts this at the composition root.

**File**: `AI-Dev-Shop/skills/design-patterns/references/clean-architecture.md`, `AI-Dev-Shop/skills/design-patterns/references/hexagonal-architecture.md`

---

### Vertical Slice Architecture

Organize by feature, not by technical layer. Each feature is self-contained: its own handler, validator, and data access in one folder. Add a feature = add a folder. Delete a feature = delete the folder.

**Use when**: Large teams where each team owns features. Feature-focused delivery. Building toward microservices.

**Avoid when**: Small solo or two-person teams where slice duplication overhead isn't worth it.

**Key tradeoff**: Some logic duplication across slices is expected and acceptable. Extract shared code only when three or more slices need it (rule of three).

**File**: `AI-Dev-Shop/skills/design-patterns/references/vertical-slice-architecture.md`

---

### Modular Monolith

A single deployable unit with strongly enforced module boundaries. Modules communicate only through their public API — never by importing internal files from another module. Start here. Extract to microservices only when you actually need independent deployment or scaling, not before.

**Use when**: Starting a new product. Small to medium teams. Proving product-market fit before optimizing for scale.

**Avoid when**: You already need independent deployment per service, or you have multiple company-external teams.

**Key tradeoff**: Simpler ops than microservices. Module boundaries in the monolith become service boundaries later — if boundaries are enforced now, extraction is straightforward.

**File**: `AI-Dev-Shop/skills/design-patterns/references/modular-monolith.md`

---

### CQRS (Command Query Responsibility Segregation)

Separate read and write models completely. Writes validate business rules and maintain consistency. Reads are optimized for the exact shape the UI or API needs, often denormalized.

**Use when**: Read patterns differ significantly from write patterns. Reporting-heavy systems. Complex read models that would pollute the write model.

**Avoid when**: Simple applications where read and write shapes are the same.

**Key tradeoff**: Projection lag — read models may be slightly behind write state in async implementations.

**File**: `AI-Dev-Shop/skills/design-patterns/references/cqrs.md`

---

### Event-Driven Architecture / Pub-Sub

Services communicate through events, not direct calls. Publishers emit events to a topic without knowing who consumes them. Subscribers react independently.

**Use when**: Multiple services need to react to the same occurrence. High throughput async workflows. You want services to be independently deployable and loosely coupled.

**Avoid when**: You need immediate consistency. Debugging complexity isn't justified by the decoupling benefit.

**Key tradeoff**: No direct call stack makes debugging harder. Eventual consistency requires explicit handling.

**File**: `AI-Dev-Shop/skills/design-patterns/references/event-driven-architecture.md`

---

### Event Sourcing

Store events, not state. Derive current state by replaying the event log. Every change is an immutable append to the event store.

**Use when**: Audit trails are required. Financial or compliance systems. You need to answer "what was the state at time X?" Time-travel debugging.

**Avoid when**: You only need current state and the event infrastructure cost isn't justified.

**Key tradeoff**: Storage grows unboundedly. Rebuilding state from millions of events is slow without snapshots. Usually combined with CQRS: event sourcing on the write side, projected read models on the read side.

---

### Microservices

Each service owns its own deployment, database, and release cycle. Teams deploy independently.

**Use when**: Multiple teams need independent deployment. Services have genuinely different scaling requirements. You're past product-market fit and at scale.

**Avoid when**: Starting out. Small team. Distributed systems complexity will slow you down more than it helps you.

**File**: `AI-Dev-Shop/skills/design-patterns/references/microservices.md`

---

### Serverless / Pipeline-Batch

**Serverless**: Bursty workloads where you pay per execution. Ops-light teams.
**Pipeline/Batch**: Offline large-scale data processing with stage isolation.

**Files**: `AI-Dev-Shop/skills/design-patterns/references/serverless-architecture.md`, `AI-Dev-Shop/skills/design-patterns/references/pipeline-batch-architecture.md`

---

### Repository Pattern

Abstract all data access behind a typed interface. The domain layer defines what it needs (`findById`, `save`); the infrastructure layer implements it. Domain is testable without a database; implementations are swappable.

**Use when**: Any Clean/Hexagonal/Layered architecture where domain logic must be unit-tested without a running database. Domain rules span multiple query shapes.

**Avoid when**: Simple CRUD with no domain logic; ORM already provides adequate abstraction and tests are integration-only.

**File**: `AI-Dev-Shop/skills/design-patterns/references/repository-pattern.md`

---

### DDD Tactical Patterns

Entity (identity-based), Value Object (value-based, immutable), Aggregate (consistency boundary with a single root), Domain Event (past-tense fact). Aggregates enforce invariants; repositories load and save them whole.

**Use when**: Complex business rules span multiple objects. State transitions must be enforced regardless of which code path runs. Long-lived product using Clean or Hexagonal architecture.

**Avoid when**: Simple CRUD with no domain rules. Prototype or throwaway code. Team unfamiliar with the concepts — poorly applied DDD is worse than a flat model.

**File**: `AI-Dev-Shop/skills/design-patterns/references/ddd-tactical-patterns.md`

---

### Multi-Tenant Architecture

Three isolation models: shared DB/shared schema (row-level `tenant_id`), shared DB/separate schema (schema-per-tenant), separate DB per tenant. Each trades isolation level against ops complexity and cost.

**Use when**: SaaS product serving multiple organizations where data isolation is required. Compliance requirements mandate a documented data boundary.

**Avoid when**: Single-tenant internal tool. Consumer app with individual users (not organizations). Pre-revenue prototype.

**File**: `AI-Dev-Shop/skills/design-patterns/references/multi-tenant-architecture.md`

---

### Caching Patterns

Cache-aside (lazy load on miss), write-through (populate on write), write-behind (async write). Choice determines consistency guarantees and failure behavior.

**Use when**: Read-heavy workloads with repeated identical queries. Expensive operations with stable results. Reducing DB connection pressure.

**Avoid when**: Data changes faster than it can be cached (near-zero hit rate). Strong consistency required on every read (financial balances, inventory). Scale has not been measured yet — profile first.

**File**: `AI-Dev-Shop/skills/design-patterns/references/caching-patterns.md`

---

## Pattern Evaluation Format

When evaluating candidate patterns, produce this table for every viable candidate before selecting one. **Do not skip patterns because they seem unlikely — score them and let the table justify the decision.**

| Pattern | Match % | Adaptability | Pros | Cons | Key Tradeoffs | Verdict |
|---------|---------|--------------|------|------|---------------|---------|
| Pattern A | 88% | High | ... | ... | ... | **SELECTED** |
| Pattern B | 76% | Medium | ... | ... | ... | Not selected — reason |
| Pattern C | 55% | Low | ... | ... | ... | Not selected — reason |

**Match %** — Holistic score against all active system drivers. Adaptability is a primary driver; weight it at minimum 30% of the total score.

**Adaptability** rating:
- **High**: External dependencies isolated behind interfaces; swapping a library, framework, or service touches only the adapter/infrastructure layer.
- **Medium**: Partial decoupling; migration requires changes across multiple layers but core logic is mostly protected.
- **Low**: Business logic coupled to framework, ORM, or external service; migration requires significant rework throughout the codebase.

**Tiebreaker rule**: When two patterns score within 10 points of each other, the higher adaptability rating wins. Document this in the Verdict column.

---

## DDD Vocabulary Reference

These terms appear throughout architecture discussions. Precision matters.

**Bounded Context**: A boundary inside which terms and rules have a specific, consistent meaning. "Customer" in Sales means something different than "Customer" in Billing. Each bounded context owns its own models.

**Entity**: An object with a unique identity that persists over time. Two instances with different IDs are different entities even if all other fields match. Examples: User, Invoice, Order.

**Value Object**: An object defined entirely by its values. No identity. Two instances with the same values are equal. Immutable — operations return new instances. Examples: Money, Address, DateRange.

**Aggregate**: A cluster of entities and value objects treated as a single unit for data changes. Has one root entity (the Aggregate Root) that controls all access and enforces all invariants. You load and save aggregates whole. Examples: Order (root) + OrderItems.

**Domain Event**: An immutable record of something significant that happened. Named in past tense. Examples: InvoiceCreated, OrderShipped, PaymentFailed. Used to decouple modules.

**Repository**: An interface that hides the database from business logic. Business logic calls `findById`, `save`, `delete`. The implementation handles the SQL/MongoDB. Swap implementations without touching core code.

**Port**: An interface that defines how the application talks to the outside world.

**Adapter**: A concrete implementation of a port. Swappable without changing the port definition.

## Architecture Decision Record (ADR) Format

Every significant architecture choice must be recorded. Use `AI-Dev-Shop/templates/adr-template.md` — it includes all required sections: Context, Decision, Rationale, Pattern Evaluation, Consequences, Module/Service Boundaries, API/Event Contract Summary, Enforcement, and Related Decisions.

ADRs live in `AI-Dev-Shop/specs/`. They are inputs to the Programmer Agent and Code Review Agent — architectural violations are violations of a recorded ADR.

## Principles That Always Apply

1. **Adaptability First.** Choose the architecture that makes future change cheapest, not the one that best fits today's requirements. Technology moves fast — patterns, libraries, and frameworks considered best practice today will be replaced. An architecture that locks you into today's choices is a liability. When two candidates score within 10 points, always prefer the more adaptable one.
2. **Dependencies point inward.** Core business logic must not depend on databases, frameworks, or external services.
3. **Depend on interfaces, not implementations.** Every external dependency should be behind an interface so it can be swapped, mocked in tests, or replaced without touching core code.
4. **Start simple, extract when needed.** Modular monolith before microservices. CRUD before CQRS. Add complexity only when the problem actually demands it.
5. **Match pattern to problem.** Event sourcing for audit trails. CQRS for asymmetric read/write. Vertical slices for large feature teams. One pattern is not universally better.
6. **Enforce boundaries.** Module A must not import internals from Module B. Enforce this with linting, import rules, or package structure — not by trusting developers to remember.
