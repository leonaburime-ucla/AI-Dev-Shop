---
name: advanced-frontend-architecture
version: 1.0.0
last_updated: 2026-06-13
description: Use when evaluating, comparing, or scoring frontend architecture candidates. Produces ADR-shaped reasoning traces with leveled depth (Senior→Staff→Principal→Distinguished). Not for implementation — for architectural decision-making.
---

# Skill: Advanced Frontend Architecture Evaluation

Evaluate frontend architecture candidates against project constraints. Produce a structured reasoning trace that scores each candidate across core dimensions, with depth controlled by engineering level.

## When to Use

- Choosing between rendering strategies, component patterns, or deployment models
- Architecture review or ADR production for frontend systems
- Comparing current architecture against alternatives
- Evaluating frontend system design proposals
- Scoring architecture fitness for team/product evolution

## When NOT to Use

- Writing components or implementing features (use `frontend-react-orcbash` or `feature-slice-design`)
- Backend/infrastructure capacity planning (use `system-design`)
- Choosing between specific design patterns for implementation (use `design-patterns`)

## Load Strategy

Read this file for the evaluation procedure. Load references only when needed:

- `references/architecture-catalog.md` — candidate profiles and scoring baselines
- `references/frontend-implementation-patterns.md` — AI Aesthetic anti-patterns, component architecture rules, state management guide, loading patterns, accessibility implementation
- Cross-reference `<AI_DEV_SHOP_ROOT>/skills/system-design/SKILL.md` for CDN/edge/load-balancing/capacity
- Cross-reference `<AI_DEV_SHOP_ROOT>/skills/design-patterns/SKILL.md` for pattern implementation details
- Cross-reference `<AI_DEV_SHOP_ROOT>/skills/vercel-react-best-practices/SKILL.md` for React performance specifics
- Cross-reference `<AI_DEV_SHOP_ROOT>/skills/feature-slice-design/SKILL.md` for FSD layer implementation

When **reviewing** frontend components or evaluating a frontend architecture decision, load `references/frontend-implementation-patterns.md` for the AI Aesthetic anti-patterns, component architecture rules, and accessibility implementation patterns. For hands-on implementation work, route to `skills/frontend-react-orcbash/SKILL.md` or `skills/feature-slice-design/SKILL.md`.

---

## Core Dimensions

Every evaluation scores candidates across these 14 dimensions. The depth selector controls how deeply each is analyzed.

| # | Dimension | Evaluates |
|---|---|---|
| 1 | Rendering strategy | CSR/SSR/SSG/hybrid/partial/RSC fit given content-vs-interactivity ratio |
| 2 | State architecture | Essential state identification, altitude, reducers, sync complexity |
| 3 | Data-fetching | REST/GraphQL/tRPC, BFF, cache normalization, streaming, mutations |
| 4 | Performance | Bundle splitting, lazy loading, critical CSS, windowing, Core Web Vitals |
| 5 | Component boundaries | Module structure, composition patterns, layer separation |
| 6 | Delivery model | Deploy independence, monorepo, feature flags, canary, rollback |
| 7 | Migration path | From current state to target; strangler fig, coexistence, phased rollout |
| 8 | Ownership topology | Team boundaries, Conway's law, contract ownership, BFF responsibility |
| 9 | Resilience | Failure modes (hydration mismatch, CDN outage, state desync), recovery |
| 10 | Observability | Web Vitals RUM, client errors, synthetic monitoring, replay |
| 11 | Design system | Token strategy, component library ownership, versioning, adoption |
| 12 | Testing strategy | Unit/component/contract/visual/e2e balance, confidence vs cost |
| 13 | Security/privacy | Auth boundary, CSP, third-party risk, PII exposure, supply chain |
| 14 | Cost | Infra per request, build-time, operational burden, team hiring cost |

---

## Depth Selector

Level controls the evaluation bar, not which dimensions are scored. All 14 dimensions are always present; depth determines evidence requirements, time horizon, and stakeholder scope.

### Senior (L5) — "What and Why"

- **Focus:** Viable technical approach, practical tradeoffs, implementation risks, immediate NFR compliance.
- **Trigger:** Default. Use for any bounded architecture decision.
- **Evidence bar:** Project requirements, team size, traffic shape.
- **Time horizon:** Current release cycle.

### Staff (L6) — "How to Get There"

All of Senior, plus:

- **Focus:** Cross-team coordination, migration rollout, platform leverage, failure playbooks, DX metrics.
- **Trigger:** Multiple teams affected, phased migration, shared platform requirements.
- **Evidence bar:** Team topology, existing tech debt, deployment pipeline constraints.
- **Time horizon:** 6-18 months.

### Principal (L7) — "Multi-Year Strategy"

All of Staff, plus:

- **Focus:** Architecture roadmap with breakpoints, governance model, portfolio cost, blast radius, strategic reversibility.
- **Trigger:** Org-wide standardization, high-risk irreversible decisions, executive-facing recommendations.
- **Evidence bar:** Org growth projections, market pressure, compliance roadmap.
- **Time horizon:** 2-4 years.

### Distinguished (L8+) — "Industry Direction"

All of Principal, plus (only when actionable):

- **Focus:** Platform capability forecasting, ecosystem bets, novel operating models from first principles.
- **Trigger:** Only when explicitly requested or when the decision involves betting on unproven platform capabilities.
- **Evidence bar:** W3C/TC39 proposals, browser vendor signals, platform adoption curves.
- **Time horizon:** 4-7 years.

---

## Evaluation Procedure

### Step 1: Establish Decision Context

Gather or clarify:

- **Goal**: what outcome the architecture must enable
- **Constraints**: team size, budget, timeline, existing codebase, compliance
- **Non-goals**: what this decision explicitly does NOT solve
- **Current architecture**: what exists today (or greenfield)
- **Change horizon**: how long until the next architecture inflection
- **Risk tolerance**: startup-move-fast vs regulated-move-carefully
- **Content-vs-interactivity ratio**: static-heavy, interactive-heavy, or mixed
- **Traffic shape**: steady, bursty, seasonal, growing

### Step 2: Select Candidates

Load `references/architecture-catalog.md`. Select 2-4 candidates that plausibly fit the constraints. Discard candidates whose anti-patterns match the context.

**Composition model:** Candidates are often composed stacks, not isolated layers. A candidate like "SSR/Hybrid + Modular Mono + BFF" counts as one entry. Compose by layer: runtime (SSR/SPA/SSG) supplies rendering defaults, topology (Monolith/MFE) supplies delivery/ownership/boundaries, data layer (BFF/GraphQL) modifies data-fetching/security/cost, and internal patterns (FSD/Vertical Slices) inherit host architecture dimensions. Score the resulting composed stack. Use N/A or "inherits from host" where a layer does not independently affect a dimension.

### Step 3: Select Depth

Default to Senior (L5). Escalate to higher depth when:

- Multiple teams will be affected (→ Staff)
- Decision is hard to reverse or has >18-month impact (→ Principal)
- User explicitly requests higher depth
- User explicitly requests Distinguished depth, or the decision involves betting on unproven platform capabilities (→ Distinguished)

### Step 4: Score Each Candidate

For each of the 14 dimensions (all 14 must appear in the Scoring Summary table; argument chains below can be terse for low-weight dimensions):

1. **Evidence**: what facts from the context inform this score
2. **Constraint interaction**: how project constraints affect this dimension
3. **Candidate comparison**: relative strength/weakness across candidates
4. **Failure modes**: what goes wrong at the depth level being evaluated
5. **Tradeoff**: what you gain vs give up
6. **Score**: 1-5 (1=poor fit, 3=adequate, 5=excellent fit)
7. **Confidence**: high/medium/low (based on available evidence)
8. **Missing information**: what would change the score if known

For Internal Component Patterns (MVC, FSD, etc.): dimensions tied to deployment topology (Delivery, Cost, Resilience) should be scored N/A with a note "internal pattern — inherits from host architecture."

Weight dimensions by relevance to the specific decision context. Weights control argument depth and tie-breaking priority, not arithmetic aggregation — do not compute weighted-sum GPAs.

### Step 5: Produce Level Overlay

After scoring at the base level, add the depth overlay:

- **Senior baseline**: practical fit, implementation risks, performance implications
- **Staff additions** (if depth ≥ Staff): migration path, ownership model, guardrails, cross-team risks
- **Principal additions** (if depth ≥ Principal): 2-4 year evolution, governance, cost model, reversibility
- **Distinguished additions** (if depth = Distinguished): ecosystem bets, platform assumptions, novel model justification

### Step 6: Synthesize Recommendation

Produce the final recommendation with:

- **Chosen approach** and one-sentence justification
- **Why not the alternatives** (strongest disqualifier for each runner-up)
- **Preconditions** (what must be true for this to succeed)
- **Reversal triggers** (signals that this decision should be revisited)
- **Follow-up decisions** (what this choice defers or creates)
- **Next level teaser** (one-liner on what deeper evaluation would scrutinize)

---

## Output Format: Reasoning Trace

Produce this structure. All 14 dimensions must appear in the Scoring Summary. Argument chains: full detail for high-weight dimensions, terse rationale for low-weight. Be terse, technical, and decisive.

```markdown
## Decision Context
- Status: [Evaluating | Proposed | Decided]
- Goal:
- Constraints:
- Non-goals:
- Current architecture:
- Change horizon:
- Risk tolerance:
- Evaluation depth: [Senior | Staff | Principal | Distinguished]

## Candidate Set
(list 2-4 candidates)
1. [Candidate] — one-line characterization
2. [Candidate] — one-line characterization

## Scoring Summary
| Dimension | Weight | [Cand 1] | [Cand 2] | ... | Winner | Confidence |
|---|---:|---:|---:|---:|---|---|
(all 14 dimensions must appear; use N/A for internal-pattern-only inapplicable dimensions)

## Argument Chain
### [Dimension Name]
- Evidence:
- Constraint interaction:
- Candidate comparison:
- Failure modes:
- Tradeoff:
- Score: [1-5]
- Confidence:
- Missing information:

(full chain for high-weight dimensions; terse "Score: X — [one-line rationale]" for low-weight dimensions)

## Level Overlay
### Senior Baseline
- Practical fit:
- Implementation risks:
- Performance implications:

### Staff Additions (if applicable)
- Migration path:
- Ownership model:
- Guardrails/tooling:
- Cross-team risks:

### Principal Additions (if applicable)
- 2-4 year evolution:
- Governance model:
- Cost/blast-radius model:
- Strategic reversibility:

### Distinguished Additions (if applicable)
- Ecosystem/platform bets:
- Industry-direction assumptions:
- Novel operating model (if justified):

## Decision
- Chosen approach:
- Why not alternatives:

## Preconditions & Consequences
- Preconditions:
- Consequences:
- Reversal triggers:
- Follow-up decisions:
- Next level teaser:
```

---

## Dimension Weighting Heuristics

Not all dimensions matter equally in every context. Default weights by scenario:

| Scenario | Heavy weight (×2) | Standard (×1) | Light (×0.5) |
|---|---|---|---|
| E-commerce / media | performance, rendering, observability | data-fetching, delivery, design-system | ownership, cost |
| Enterprise SaaS | state, testing, security | component-boundaries, observability, cost | rendering, design-system |
| Platform / many teams | ownership, delivery, design-system | migration, resilience, testing | rendering, performance |
| Startup / greenfield | performance, cost, delivery | state, data-fetching, component-boundaries | migration, ownership, resilience |
| Regulated / compliance | security, testing, observability | resilience, cost, delivery | rendering, design-system |

Override weights when the decision context makes a different prioritization obvious.
