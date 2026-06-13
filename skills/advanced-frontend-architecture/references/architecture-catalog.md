# Frontend Architecture Catalog

Condensed profiles for architecture evaluation. Each entry provides enough to score against the 14 core dimensions — not enough to implement. For implementation details, load the cross-referenced skill.

---

## Macro Architecture Candidates

### 1. Static / SSG

**Examples:** Astro, 11ty, Hugo, vanilla HTML/CSS

**Characterization:** Pre-built HTML served from CDN. Zero runtime JS unless explicitly added. Maximum performance, minimum interactivity.

| Dimension | Profile |
|---|---|
| Rendering | Excellent — pre-built, CDN-served, sub-100ms TTFB |
| State | Minimal — no client state beyond form inputs |
| Data-fetching | Build-time only; content changes require rebuild |
| Performance | Excellent — smallest possible bundle, best LCP/CLS |
| Component boundaries | Weak — no runtime composition model |
| Delivery | Simple — static hosting, CDN invalidation |
| Migration | Easy to migrate FROM; hard to migrate TO from interactive apps |
| Resilience | Excellent — no server to fail, CDN redundancy |
| Cost | Lowest — static hosting is near-free |

**Sweet spot:** Content sites, blogs, docs, marketing pages. Team 1-5. Any lifetime.
**Anti-pattern:** User-generated content, real-time features, personalization, dashboards.
**Transitions:** → SSR/Hybrid when interactivity needs grow. ← from any pattern for content-only sections.

---

### 2. SPA (Client-Side Rendered)

**Examples:** React CRA, Vue CLI, Angular CLI, Vite + React/Vue

**Characterization:** Single HTML shell, full app rendered in browser via JS. Rich interactivity, poor initial load and SEO.

| Dimension | Profile |
|---|---|
| Rendering | Weak initial load (white screen); excellent runtime reactivity |
| State | Strong — full client state management (Redux, Zustand, Pinia) |
| Data-fetching | Client-side; waterfall risk without careful orchestration |
| Performance | Poor LCP without optimization; good INP once loaded |
| Component boundaries | Framework-native (React components, Vue SFCs) |
| Delivery | Simple — static bundle to CDN |
| Migration | Easy to start; expensive to add SSR later |
| Resilience | Weak — JS failure = blank page; no graceful degradation |
| Cost | Low infra; high bundle-optimization effort at scale |

**Sweet spot:** Internal tools, dashboards, admin panels. Team 2-15. Medium lifetime (2-5 years).
**Anti-pattern:** SEO-critical, content-heavy, low-powered devices, slow networks.
**Transitions:** → SSR/Hybrid for SEO/performance. → Modular Monolith for team scaling. ← from MVC/server-rendered apps.

---

### 3. SSR / Hybrid (Meta-framework)

**Examples:** Next.js, Nuxt, SvelteKit, Remix, Astro (hybrid mode)

**Characterization:** Server-renders initial HTML, hydrates on client. Mixes static, server-rendered, and client-rendered per route. Best balance of performance + interactivity.

| Dimension | Profile |
|---|---|
| Rendering | Excellent — SSR eliminates white screen; RSC reduces JS shipped |
| State | Moderate complexity — server/client state boundary management |
| Data-fetching | Server-side fetching eliminates client waterfalls; streaming support |
| Performance | Good LCP/CLS; INP depends on hydration strategy |
| Component boundaries | Framework-opinionated (app router, file-based routing) |
| Delivery | More complex — requires server/edge runtime, not just CDN |
| Migration | Moderate — hydration boundary requires explicit client/server split |
| Resilience | Moderate — server failure degrades to loading state, not blank page |
| Cost | Higher — server compute for SSR; edge functions for low-latency |

**Sweet spot:** E-commerce, SaaS marketing, content + interactivity mix. Team 3-30. Long lifetime.
**Anti-pattern:** Pure internal tools (overkill), offline-first apps, extremely dynamic real-time UIs.
**Transitions:** → Modular Monolith or MFE for org scaling. ← from SPA needing SEO/perf. ← from SSG needing interactivity.

---

### 4. Modular Frontend Monolith

**Examples:** Domain-sliced Next.js/Nuxt app, Nx/Turborepo workspace with one deployable, FSD-structured app

**Characterization:** Single deployed application with strict internal domain boundaries. Teams own modules but share a deploy pipeline. Enforced via linting, module boundaries, and code ownership.

| Dimension | Profile |
|---|---|
| Rendering | Inherits from underlying framework (SSR/CSR/hybrid) |
| State | Requires discipline — global state leaks across boundaries easily |
| Component boundaries | Strong with enforcement (ESLint boundaries, barrel exports, FSD layers) |
| Delivery | Single deploy — simpler infra, but all-or-nothing releases |
| Ownership | Module-level ownership via CODEOWNERS; shared build pipeline |
| Migration | Natural step from SPA; stepping stone to MFE |
| Resilience | Moderate — one broken module can block the whole deploy |
| Cost | Moderate — single infra, but long build times at scale |

**Sweet spot:** Growing teams (10-50 devs) that aren't ready for MFE complexity. Medium-long lifetime.
**Anti-pattern:** Truly independent teams needing autonomous deploy. Very small teams (unnecessary overhead).
**Transitions:** → Micro-frontends when deploy independence becomes critical. ← from SPA when boundaries are needed.

---

### 5. Micro-frontends

**Examples:** Module Federation (Webpack/Rspack), single-spa, Piral, iframe composition, Vercel multi-zone

**Characterization:** Independent frontend applications composed at runtime into a single user experience. Each team owns, builds, deploys independently. Shell provides shared concerns (auth, routing, design tokens).

| Dimension | Profile |
|---|---|
| Rendering | Complex — cross-app hydration, shared layout negotiation |
| State | Isolated per MFE; shared state via shell injection or event bus |
| Data-fetching | Per-MFE BFFs; risk of duplicate requests without coordination |
| Performance | Overhead — runtime composition, duplicate dependencies, version skew |
| Component boundaries | Maximum — enforced by deploy boundary |
| Delivery | Excellent independence — each team deploys on own schedule |
| Ownership | Maximum autonomy — vertical slices with full FE+BE ownership |
| Migration | Expensive to adopt; strangler fig from monolith over 6-18 months |
| Resilience | Good isolation — one MFE failure doesn't crash others (with error boundaries) |
| Design system | Critical — visual cohesion requires shared token/component library |
| Cost | Highest — multiple build pipelines, shell maintenance, coordination overhead |

**Sweet spot:** Large orgs (50-500+ FE devs), multiple product teams, enterprise platforms. Long lifetime (5+ years).
**Anti-pattern:** Small teams (<10 devs), startups, MVPs, apps with tightly coupled features.
**Transitions:** ← from Modular Monolith when deploy independence is needed. Rarely transitions to something else (hard to reverse).

---

### 6. BFF + GraphQL (Data Architecture Layer — Complementary)

**Examples:** Apollo Server, Hasura, Pothos, tRPC (BFF variant), Relay

**Characterization:** Dedicated backend-for-frontend aggregation layer. Owned by FE team. Single query replaces multiple REST calls. Can sit in front of microservices. **Not a competing macro architecture** — layers on top of any candidate above (SPA, SSR, MFE). Include in the candidate set only when the evaluation is specifically about data-fetching strategy, not rendering/deployment topology.

| Dimension | Profile |
|---|---|
| Data-fetching | Excellent — eliminates underfetching/overfetching, single round-trip |
| Performance | Reduces client waterfalls; server-side resolution is fast |
| Ownership | FE-team owned; decouples from backend service release cycles |
| Delivery | Adds infra (BFF server); but front+back can iterate independently |
| Resilience | Single point of failure if BFF goes down; needs redundancy |
| Cost | Moderate — BFF hosting + GraphQL expertise |
| Security | Centralizes auth/rate-limiting; but exposes full schema surface |

**Sweet spot:** Multi-service backends, mobile + web sharing data layer, complex data requirements. Team 5-50.
**Anti-pattern:** Simple CRUD with one backend, very small teams, prototypes.
**Transitions:** Complementary to any macro architecture above. Often added to SPA or SSR apps.

---

## Internal Component Patterns

These are internal structuring approaches, not macro deployment architectures. They determine how code is organized within a deployed application.

| Pattern | Core Idea | Strength | Weakness | When to Use |
|---|---|---|---|---|
| **MVC** | Model-View-Controller separation | Simple mental model | Fat controllers, not SPA-native | Legacy/simple server-rendered apps |
| **MVP** | Passive view, presenter handles logic | Better testability than MVC | Fat presenter, boilerplate | Apps needing strict view/logic separation |
| **MVVM** | Two-way binding, ViewModel for UI state | Natural for reactive frameworks | Implicit state flow, debugging complexity | Vue/Knockout apps with complex UI state |
| **Hexagonal** | Ports & adapters, business logic at center | Framework-independent core, testable | Ceremony overhead, over-engineering risk | Long-lived apps, multiple I/O channels |
| **Vertical Slices** | Self-contained feature units (own model/logic/UI) | Team autonomy, parallel development | Cross-slice inconsistency, duplication risk | Large apps, cross-functional teams |
| **FSD** | Strict layer hierarchy (app→pages→widgets→features→entities→shared) | Predictable imports, clear boundaries | Learning curve, framework-specific adaptation | Medium-large React/Vue/Svelte apps |

**Progression:** MVC → MVP → MVVM (increasing UI logic sophistication) → Hexagonal (framework independence) → Vertical Slices (feature autonomy) → FSD (strict compositional hierarchy).

**Decision heuristic:** If the framework is already opinionated (Next.js, Nuxt), start with its conventions + FSD for boundaries. Only reach for hexagonal/clean arch when the business logic layer is substantial enough to justify the abstraction.

---

## Quick Candidate Selection

Given constraints, narrow to 2-4 candidates:

| If... | Start with... |
|---|---|
| Content-heavy, SEO-critical, low interactivity | Static/SSG or SSR/Hybrid |
| Interactive dashboard, internal tool | SPA + Modular Monolith |
| E-commerce, mixed content + interaction | SSR/Hybrid + BFF |
| Multiple teams, independent deploy needed | Micro-frontends |
| Complex data from many services | BFF + GraphQL (layer on top of any macro arch) |
| Greenfield, small team, fast iteration | SPA (upgrade path to SSR/Hybrid later) |
| Long-lived, large team, growing | Modular Monolith → Micro-frontends progression |

---

## Scoring Baseline by Dimension

Default scores (1-5) when no project-specific evidence overrides. Use as starting point, not as final answer. This table is authoritative for all 14 dimensions — narrative profiles above highlight only differentiating dimensions.

| Candidate | Render | State | Data | Perf | Boundaries | Delivery | Migration | Ownership | Resilience | Observe | Design-Sys | Test | Security | Cost |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Static/SSG | 5 | 1 | 2 | 5 | 2 | 5 | 4 | 2 | 5 | 3 | 2 | 4 | 4 | 5 |
| SPA | 2 | 4 | 3 | 2 | 3 | 4 | 3 | 3 | 2 | 3 | 3 | 4 | 3 | 4 |
| SSR/Hybrid | 4 | 3 | 4 | 4 | 4 | 3 | 3 | 3 | 3 | 4 | 3 | 3 | 3 | 3 |
| Modular Mono | 3 | 3 | 3 | 3 | 4 | 3 | 3 | 4 | 3 | 3 | 4 | 4 | 3 | 3 |
| Micro-FE | 3 | 3 | 3 | 2 | 5 | 5 | 2 | 5 | 4 | 3 | 5 | 3 | 3 | 2 |
| BFF+GraphQL | — | — | 5 | 4 | — | 3 | 3 | 4 | 3 | 3 | — | 3 | 4 | 3 |

These are unweighted baselines. The evaluation procedure applies context-specific weights and adjusts scores based on evidence.
