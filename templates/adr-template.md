# ADR-<id>: <short title>

- Status: PROPOSED | ACCEPTED | SUPERSEDED | DEPRECATED
- Date: <ISO-8601 UTC>
- Spec: <SPEC-id> v<version> (hash: <sha256>)
- Author: Architect Agent / <human reviewer>

## Context

What problem are we solving? What forces are acting on this decision?

Describe the situation that makes this decision necessary. Include:
- The relevant system drivers (scale, complexity, coupling, release cadence, team size)
- Constraints that cannot be changed (latency SLAs, regulatory, existing infrastructure)
- What happens if we do nothing

## Decision

What have we decided to do?

State the decision in one or two sentences. Be direct — no "we are considering" or "we might." This is a decision record, not a discussion document.

**Pattern(s) selected:** e.g., Clean Architecture + CQRS

## Rationale

Why this decision and not the alternatives?

Map the decision to the system drivers:
- Driver 1 (e.g., complex domain logic) → addressed by Clean Architecture's explicit Entities ring
- Driver 2 (e.g., asymmetric read/write load) → addressed by CQRS read model separation
- Driver 3 (e.g., audit trail required) → addressed by...

## Pattern Evaluation

All candidate patterns evaluated before selection. Adaptability score reflects how easily this choice can be replaced or extended as requirements and technology evolve. When two patterns score within 10 points, the higher-adaptability pattern is preferred per the Adaptability First principle.

| Pattern | Match % | Adaptability | Pros | Cons | Key Tradeoffs | Verdict |
|---------|---------|--------------|------|------|---------------|---------|
| Clean Architecture + CQRS | 88% | High | Business logic isolated from deps; read/write concerns separated; highly testable | Higher initial structure; CQRS projection lag requires UI handling | Eventual consistency in read models; justified by long-term swap flexibility | **SELECTED** |
| Layered Architecture | 60% | Low | Familiar pattern; low upfront effort | Business logic coupled to layers; framework lock-in | Costly migration when stack changes; poor long-term adaptability | Not selected — low adaptability despite lower initial cost |
| Vertical Slice | 72% | Medium | Feature-focused; clean feature addition and deletion | Overhead not justified for team size | Cross-slice duplication expected; shared logic extraction required at scale | Not selected — team size doesn't justify feature ownership model |
| Microservices | 45% | Medium | Independent deployment per service | Distributed systems complexity pre-PMF | Operational overhead slows delivery; complexity not justified at current stage | Not selected — pre-PMF; 43 points below selected pattern |

## Consequences

**Positive:**
- Testable business logic without database or framework dependencies
- Read models can be optimized independently of write throughput
- ...

**Negative / Tradeoffs:**
- Higher initial complexity; steeper onboarding for developers unfamiliar with CQRS
- Eventual consistency in read models requires UI handling strategy
- ...

**Risks:**
- Risk: Projection rebuild time not tested early → plan: include rebuild time in acceptance criteria for first projection
- Risk: ...

## Module / Service Boundaries

What are the explicit boundaries this decision creates?

```
src/
  domain/         # Ring 1: Entities — no external dependencies
  application/    # Ring 2: Use Cases — depends on domain only
  adapters/       # Ring 3: Interface Adapters
  infrastructure/ # Ring 4: Frameworks & Drivers
```

## API / Event Contract Summary

What interfaces does this decision define that other agents must respect?

- `IInvoiceRepository` — interface defined in Ring 2, implemented in Ring 3
- `InvoiceCreated` integration event — published by Order Service, consumed by Notification and Analytics
- ...

## Enforcement

How do we prevent violations?
- CI lint rule: no imports from `infrastructure/` in `domain/` or `application/`
- Code Review Agent must flag any direct ORM usage in use cases
- Architecture compliance is a Required finding in Code Review

## Related Decisions

- Supersedes: ADR-<id> (if applicable)
- Relates to: ADR-<id> (if applicable)
