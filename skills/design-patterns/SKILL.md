---
name: design-patterns
version: 1.0.0
last_updated: 2026-02-22
description: Use when selecting or implementing architecture patterns including hexagonal, clean architecture, CQRS, event sourcing, event-driven, microservices, resilience, DDD tactical patterns, multi-tenant, caching, repository pattern, and more — each with TypeScript examples, tradeoffs, and when-to-use guidance.
---

# Design Patterns Library

19+ production architecture patterns with TypeScript examples, tradeoffs, testing guidance, and failure modes. Load the specific pattern file(s) relevant to the current decision — do not load all at once.

## Pattern Selection Decision Guide

| Situation | Load |
|---|---|
| Greenfield product, small team | `AI-Dev-Shop/skills/design-patterns/references/modular-monolith.md` |
| Complex domain logic, long-lived product | `AI-Dev-Shop/skills/design-patterns/references/clean-architecture.md` or `hexagonal-architecture.md` |
| Multiple I/O channels (HTTP + CLI + events) | `AI-Dev-Shop/skills/design-patterns/references/hexagonal-architecture.md` |
| Feature teams, autonomous delivery | `AI-Dev-Shop/skills/design-patterns/references/vertical-slice-architecture.md` |
| Asymmetric read/write workloads | `AI-Dev-Shop/skills/design-patterns/references/cqrs.md` |
| Audit trail, financial, compliance | `AI-Dev-Shop/skills/design-patterns/references/event-sourcing.md` (pair with CQRS) |
| Async cross-service side effects | `AI-Dev-Shop/skills/design-patterns/references/event-driven-architecture.md` |
| Multi-service business transactions | `AI-Dev-Shop/skills/design-patterns/references/reliability-patterns.md` (Saga) |
| Reliable event publishing | `AI-Dev-Shop/skills/design-patterns/references/reliability-patterns.md` (Outbox) |
| Independent team deployment at scale | `AI-Dev-Shop/skills/design-patterns/references/microservices.md` |
| Migrating a legacy system | `AI-Dev-Shop/skills/design-patterns/references/strangler-fig.md` |
| Multiple client types (mobile, web, API) | `AI-Dev-Shop/skills/design-patterns/references/api-patterns.md` (BFF) |
| Centralized auth, rate limiting at edge | `AI-Dev-Shop/skills/design-patterns/references/api-patterns.md` (API Gateway) |
| Preventing cascade failures | `AI-Dev-Shop/skills/design-patterns/references/resilience-patterns.md` |
| Bursty traffic, ops-light team | `AI-Dev-Shop/skills/design-patterns/references/serverless-architecture.md` |
| Offline batch / ML pipelines | `AI-Dev-Shop/skills/design-patterns/references/pipeline-batch-architecture.md` |
| Simple CRUD, familiar team structure | `AI-Dev-Shop/skills/design-patterns/references/layered-architecture.md` |
| Domain layer needs data access without DB coupling | `AI-Dev-Shop/skills/design-patterns/references/repository-pattern.md` |
| Modeling complex domain with entities, aggregates, value objects | `AI-Dev-Shop/skills/design-patterns/references/ddd-tactical-patterns.md` |
| SaaS product with multiple isolated customers | `AI-Dev-Shop/skills/design-patterns/references/multi-tenant-architecture.md` |
| Read-heavy workloads, expensive repeated queries, latency reduction | `AI-Dev-Shop/skills/design-patterns/references/caching-patterns.md` |

## Common Pattern Combinations

**Event-driven modular monolith** (recommended starting point for most products):
`modular-monolith` + `event-driven-architecture` + `reliability-patterns` (Outbox)

**Audit-ready enterprise system**:
`clean-architecture` + `cqrs` + `event-sourcing`

**High-scale distributed system**:
`microservices` + `event-driven-architecture` + `reliability-patterns` + `resilience-patterns` + `api-patterns`

**Legacy migration path**:
`strangler-fig` → `modular-monolith` → `microservices` (if needed)

## All Pattern Files

See `AI-Dev-Shop/skills/design-patterns/references/` for the full set.
