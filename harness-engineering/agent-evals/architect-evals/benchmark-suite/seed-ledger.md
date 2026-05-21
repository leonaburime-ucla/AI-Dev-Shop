# Seed Ledger — Architect Scorecard Suite

This suite tests the new Architect scorecard behavior added to:

- `skills/architecture-decisions/SKILL.md`
- `framework/templates/adr-template.md`
- `agents/architect/skills.md`
- `skills/system-blueprint/SKILL.md`

The agent under test does not see this ledger.

## Seeds

### eval-1-team-chat-saas

`SEED-AR-01`
- Seeded issue: Public multi-tenant chat plus file attachments makes security a
  first-class quality concern. The Architect should not bury it inside a merged
  umbrella like “resilience”.
- Expected signal: A standalone `security` row or equivalent explicit treatment.

`SEED-AR-02`
- Seeded issue: The system is organization-multi-tenant. `tenant_isolation`
  should activate.
- Expected signal: Optional-axis activation with a cited source.

`SEED-AR-03`
- Seeded issue: Future plugin extensions and admin workflows make `modularity`
  meaningfully distinct from `modifiability`.
- Expected signal: Separate treatment or reasoning that clearly differentiates
  boundary quality from change friction.

`SEED-AR-04`
- Seeded issue: The spec includes explicit admin audit logging and INV-03
  requires an audit record. `compliance_auditability` should activate even
  without a formal regulated regime.
- Expected signal: Optional-axis activation citing the audit-trail requirement
  as the source.

`SEED-AR-05`
- Seeded issue: The ADR must include `Tradeoff Tension` and `Why This Won`
  instead of a weighted-score winner story.
- Expected signal: Narrative tradeoff synthesis.

`SEED-AR-06`
- Seeded issue: No benchmark or prototype evidence exists. Confidence should
  not be overstated as `measured`.
- Expected signal: `analogical`, `prior_art`, or clearly reasoned lower-evidence
  confidence.

`SEED-AR-07`
- Seeded issue: A three-person generalist team with on-call burden should
  trigger `cognitive_load`.
- Expected signal: Optional-axis activation with rationale.

`SEED-AR-22`
- Seeded issue: The ADR should summarize overall strengths and weaknesses, not
  force the reviewer to reconstruct them from row-level text.
- Expected signal: Explicit `Overall Strengths` and `Overall Weaknesses`.

`SEED-AR-23`
- Seeded issue: False-positive bait. The brief never states RPO, RTO, failover,
  or recovery-region requirements.
- Expected signal: No activation of `disaster_recovery`.

`SEED-AR-24`
- Seeded issue: The chosen architecture should not look utopian. A scorecard
  with no meaningful weakness is not credible.
- Expected signal: At least one concrete weakness acknowledged for the winner.

### eval-2-analytics-export-platform

`SEED-AR-08`
- Seeded issue: Explicit dashboard latency targets should activate
  `performance`.
- Expected signal: Optional-axis activation tied to the stated SLA.

`SEED-AR-09`
- Seeded issue: Four external systems and fragile partner APIs should activate
  `integration_complexity`.
- Expected signal: Optional-axis activation plus mechanism-aware discussion.

`SEED-AR-10`
- Seeded issue: Ingestion and reporting have different release cadences, so
  `deployment_independence` should activate.
- Expected signal: Explicit activation source from the blueprint or constraints.

`SEED-AR-11`
- Seeded issue: The fixture now makes limited operational staffing explicit. If
  the chosen architecture still adds replay, queue, or multi-path async burden,
  the ADR must drive operability low enough to trigger mitigation details.
- Expected signal: Complete mitigation row with owner, enforcement, and
  deadline/trigger, not a vague promise.

`SEED-AR-12`
- Seeded issue: False-positive bait. This is a single-enterprise internal
  analytics platform, not a multi-tenant SaaS.
- Expected signal: No activation of `tenant_isolation`.

`SEED-AR-13`
- Seeded issue: The Architect should not write slogan-level reasoning like
  “event-driven scales better.”
- Expected signal: Mechanism-based rationale tied to the actual system shape.

`SEED-AR-14`
- Seeded issue: The scorecard should define when it must be revisited.
- Expected signal: Concrete `review_trigger` such as new data sources, traffic
  threshold, or topology change.

`SEED-AR-25`
- Seeded issue: Activated optional axes need explicit activation sources.
- Expected signal: A cited blueprint or requirement source for each activated
  optional axis.

`SEED-AR-26`
- Seeded issue: The fixture now plants a hand-wavy growth assumption. The
  Architect should not copy it through unchanged.
- Expected signal: An assumption rewritten into falsifiable terms, or an
  explicit rejection of the vague assumption.

`SEED-AR-27`
- Seeded issue: Low ops headcount creates a real cost/operability tension that
  should be called out explicitly.
- Expected signal: Tradeoff language that makes the cost/operability sacrifice
  visible.

`SEED-AR-31`
- Seeded issue: False-positive bait. Replayability, observability, and partner
  visibility are important, but they do not automatically create
  `compliance_auditability` without a legal, regulatory, audit-trail, or
  evidentiary requirement.
- Expected signal: No activation of `compliance_auditability`.

### eval-3-payments-ledger-modernization

`SEED-AR-15`
- Seeded issue: Regulated payments and audit trails should activate
  `compliance_auditability`.
- Expected signal: Explicit optional-axis activation and score.

`SEED-AR-16`
- Seeded issue: Balance invariants and async side effects should activate
  `data_consistency`.
- Expected signal: The ADR treats consistency as a named quality attribute.

`SEED-AR-17`
- Seeded issue: A candidate with catastrophic security or consistency cannot win
  just because it is cheaper or simpler.
- Expected signal: Blocking-rule-aware elimination or explicit rejection.

`SEED-AR-18`
- Seeded issue: Weak axes must have enforceable mitigation details, not generic
  “monitor this later” text.
- Expected signal: mitigation + owner + enforcement + deadline/trigger.

`SEED-AR-19`
- Seeded issue: The ADR should compare the winner against the runner-up in a way
  that makes the decisive tradeoff auditable.
- Expected signal: `Runner-Up Comparison` and `delta_vs_runner_up`.

`SEED-AR-20`
- Seeded issue: Regression seed. The scorecard change must preserve separate
  `modularity` analysis in a case where module boundaries are strong but
  cross-cutting change friction remains high.
- Expected signal: The chosen ADR does not collapse both ideas into one score.

`SEED-AR-21`
- Seeded issue: False-positive bait. Despite architecture churn, regulated
  change windows keep deployments coordinated.
- Expected signal: No activation of `deployment_independence`.

`SEED-AR-28`
- Seeded issue: Blocking should follow dominant quality attributes and hard
  requirements, not a generic fixed list detached from context.
- Expected signal: Critical-axis reasoning tied to blueprint/spec priorities.

`SEED-AR-29`
- Seeded issue: Re-evaluation triggers should include concrete structural
  thresholds such as new async consumers or topology changes.
- Expected signal: Review triggers that a later team could actually observe.

`SEED-AR-30`
- Seeded issue: Runner-up comparison should use a plausible near-alternative,
  not a cartoonishly bad straw man.
- Expected signal: Honest comparison against the strongest rejected option.

`SEED-AR-32`
- Seeded issue: When candidate fit is close, the Architect must visibly apply
  the Adaptability First tiebreaker rather than pretending the higher raw match
  wins automatically.
- Expected signal: Explicit tie-breaker reasoning favoring the more adaptable
  near-fit candidate when scores are close enough for the rule to matter.

### eval-4-thin-evidence-concept

`SEED-AR-34`
- Seeded issue: The fixture is intentionally thin on proven scale, security,
  operability, and integration evidence. The Architect should not present a
  fully confident final architecture as if more than half of the core axes were
  well-supported.
- Expected signal: Research escalation, provisional language, or explicit
  acknowledgment that too many core-axis scores are `assumed` to finalize with
  confidence.

### additional negative control

`SEED-AR-35`
- Seeded issue: False-positive bait. Team chat feels latency-sensitive, but the
  fixture does not include any explicit performance SLO or throughput target.
- Expected signal: No activation of `performance`.

### eval-5-ai-rag-platform

`SEED-AR-36`
- Seeded issue: The fixture includes a concrete answer-latency target. The
  Architect should activate `performance` rather than treating retrieval cost
  as a tuning detail.
- Expected signal: Explicit optional-axis activation tied to the answer SLO.

`SEED-AR-37`
- Seeded issue: The platform must preserve answer citations, support-history
  evidence, and response provenance. `compliance_auditability` should activate
  even though this is an internal AI platform.
- Expected signal: Explicit auditability reasoning tied to traceable answers
  and evidence reconstruction.

`SEED-AR-38`
- Seeded issue: Model routing, prompt versioning, and evaluation loops are part
  of the architecture, not an implementation footnote.
- Expected signal: Architecture-level treatment of LLM operations concerns.

`SEED-AR-39`
- Seeded issue: Vector store, embedding model, and base model choices remain
  open. The Architect should not project false certainty over unresolved AI
  vendor decisions.
- Expected signal: Research escalation or provisional scoring where evidence is
  still thin.

`SEED-AR-40`
- Seeded issue: The fastest external AI option is tempting, but ticket content,
  attachments, and residency constraints make that path constitution-sensitive.
- Expected signal: The ADR rejects or constrains the tempting hosted shortcut
  instead of silently accepting it.

`SEED-AR-41`
- Seeded issue: Corpus drift, prompt updates, and model swaps create real
  review triggers in a RAG system.
- Expected signal: Concrete review triggers tied to retrieval drift, corpus
  growth, or model/prompt changes.

`SEED-AR-42`
- Seeded issue: Managed AI suite versus app-owned RAG core is intentionally
  close. The Architect should apply Adaptability First instead of hiding behind
  raw pattern fit.
- Expected signal: Explicit tie-breaker reasoning that makes the decisive trade
  auditable.

`SEED-AR-43`
- Seeded issue: False-positive bait. The platform uses internal role-scoped
  workspaces, but it is not a customer multi-tenant SaaS.
- Expected signal: No activation of `tenant_isolation`.

### eval-6-api-integration-hub

`SEED-AR-44`
- Seeded issue: Four partner protocols, webhook variants, and connector
  quirks should activate `integration_complexity`.
- Expected signal: Explicit optional-axis activation with mechanism-aware
  reasoning.

`SEED-AR-45`
- Seeded issue: Connectors ship on different cadences and should not force one
  full-hub redeploy cycle.
- Expected signal: `deployment_independence` activation tied to bounded
  connector ownership.

`SEED-AR-46`
- Seeded issue: Versioned contracts, idempotency, and webhook replay handling
  are architecture boundaries, not just API polish.
- Expected signal: ADR language that treats API contract shape as a first-class
  architecture concern.

`SEED-AR-47`
- Seeded issue: Transport and delivery shape choices remain open because some
  partners are request/response, some webhook-first, and some batch/SFTP.
- Expected signal: Research trigger or explicitly provisional choice instead of
  transport certainty theater.

`SEED-AR-48`
- Seeded issue: The easiest implementation leaks secrets or vendor SDKs into
  shared hub layers.
- Expected signal: The ADR keeps secrets and partner-specific code behind
  bounded adapters and rejects the leaky shortcut.

`SEED-AR-49`
- Seeded issue: Gateway-centric and event-assisted hub patterns are both
  plausible. The Architect should make the decisive trade visible.
- Expected signal: Honest runner-up handling and explicit close-fit tradeoff
  reasoning.

`SEED-AR-50`
- Seeded issue: False-positive bait. The hub aggregates and normalizes partner
  reads, but it is not the system of record for distributed writes.
- Expected signal: No automatic activation of `data_consistency`.

`SEED-AR-51`
- Seeded issue: Partner contract churn must create observable review triggers.
- Expected signal: Review triggers and contract-test strategy tied to partner
  field or behavior drift.

### eval-7-event-driven-data-platform

`SEED-AR-52`
- Seeded issue: CDC plus replayable multi-consumer flows should activate
  `data_consistency`.
- Expected signal: Consistency appears as a named quality attribute rather than
  an implied property of the broker.

`SEED-AR-53`
- Seeded issue: Producers and consumers evolve on different release cadences
  during the migration from batch to streaming.
- Expected signal: `deployment_independence` activation tied to producer and
  consumer autonomy.

`SEED-AR-54`
- Seeded issue: The fixture includes concrete ingest and freshness targets.
- Expected signal: Explicit `performance` activation grounded in throughput and
  freshness requirements.

`SEED-AR-55`
- Seeded issue: Lag, replay, dead-letter, and schema-drift observability are
  not optional in a streaming platform.
- Expected signal: Observability appears in architecture synthesis and not only
  in a future ops note.

`SEED-AR-56`
- Seeded issue: Broker, CDC, and processing-shape choices remain open enough to
  require research instead of vendor certainty.
- Expected signal: Provisional language or concrete research follow-up before
  overcommitting.

`SEED-AR-57`
- Seeded issue: A bespoke event mesh is architecturally tempting but violates
  the constitution unless the real constraints justify it.
- Expected signal: The ADR favors simpler streaming building blocks or clearly
  proves why extra machinery is necessary.

`SEED-AR-58`
- Seeded issue: Upgraded micro-batch and fuller event streaming are kept close
  on purpose.
- Expected signal: Explicit tradeoff call that makes the migration and
  adaptability judgment auditable.

`SEED-AR-59`
- Seeded issue: False-positive bait. Replayable logs improve recovery options,
  but the fixture does not state any region failover, RPO, or RTO commitment.
- Expected signal: No automatic activation of `disaster_recovery`.

---

## System Design Seeds (SEED-AR-60 through SEED-AR-116)

These seeds test the Architect's application of `skills/system-design/SKILL.md`
and its references, particularly `operational-depth-patterns.md`. They were
peer-calibrated by Codex (GPT-5.5) for complexity accuracy.

Skills under test:

- `skills/system-design/SKILL.md`
- `skills/system-design/references/requirements-and-capacity.md`
- `skills/system-design/references/distributed-systems-patterns.md`
- `skills/system-design/references/operational-depth-patterns.md`

The agent under test does not see this ledger.

### eval-1-social-feed-platform (SEED-AR-60 through SEED-AR-69)

`SEED-AR-60` — Celebrity hot-key on hash-partitioned store. Positive control.
`SEED-AR-61` — Retry storm without circuit breaker/load shedding. Staff.
`SEED-AR-62` — Incomplete circuit breaker (missing half-open) + stale fallback. Regression control.
`SEED-AR-63` — Fan-out-on-write vs read tradeoff with cross-artifact evidence. Principal.
`SEED-AR-64` — Global rate limit anti-pattern; per-tenant token bucket needed. Staff.
`SEED-AR-65` — Negative control: uniform distribution should NOT trigger hot-key patterns.
`SEED-AR-66` — Public platform without automated abuse detection at scale. Principal.
`SEED-AR-67` — Capacity math based on averages hides peak and fan-out write load. Staff.
`SEED-AR-68` — Write amplification from notification fan-out not factored into capacity. Principal.
`SEED-AR-69` — Webhook dedup needed from retry-based delivery (implicit signal). Staff.

### eval-2-payment-processing (SEED-AR-70 through SEED-AR-78)

`SEED-AR-70` — Payment retry without idempotency key. Positive control.
`SEED-AR-71` — Dedup window shorter than max processing delay. Staff.
`SEED-AR-72` — 2PC spanning notification service; saga/outbox correct. Principal.
`SEED-AR-73` — Long-lived API keys without mTLS/zero-trust. Production.
`SEED-AR-74` — Encryption keys in config without KMS/rotation. Production.
`SEED-AR-75` — Negative control: single-DB ACID should NOT trigger distributed tx patterns.
`SEED-AR-76` — Consistency vs latency tension in ledger + balance queries. Principal.
`SEED-AR-77` — Unique constraint mistaken for idempotency (no stored response). Staff.
`SEED-AR-78` — Outbox consumer processes in parallel breaking per-payment ordering. Staff.

### eval-3-iot-data-pipeline (SEED-AR-79 through SEED-AR-89)

`SEED-AR-79` — Unbounded ingestion without backpressure. Positive control.
`SEED-AR-80` — No max batch size/wait time, drops partial failures. Production.
`SEED-AR-81` — Infinite retry without DLQ blocks partition. Staff.
`SEED-AR-82` — Deep health probe causes cascading restarts under load. Staff.
`SEED-AR-83` — Burst ingestion not average; no retention; unbounded growth. Principal.
`SEED-AR-84` — Negative control: low-volume admin CSV does NOT need async.
`SEED-AR-85` — Missing failure modes, observability, stateful component IDs. Staff.
`SEED-AR-86` — Ordering vs latency at scale; global FIFO impossible at 100K/s. Principal.
`SEED-AR-87` — Stateful aggregation service mislabeled "stateless." Staff.
`SEED-AR-88` — Per-device ordering broken by round-robin partition assignment. Staff.

### eval-4-multi-tenant-analytics (SEED-AR-89 through SEED-AR-98)

`SEED-AR-89` — 100:1 read/write with 8-12s page loads needs precomputation. Principal.
`SEED-AR-90` — Average-tenant capacity hides 500x whale without quota. Principal.
`SEED-AR-91` — Simple RBAC insufficient for tenant-boundary/data-residency. Staff.
`SEED-AR-92` — Negative control: single-enterprise should NOT get tenant isolation.
`SEED-AR-93` — CQRS+event-sourcing+cache+CDN for 50-user tool (over-engineering). Production.
`SEED-AR-94` — Negative control: sub-ms indexed lookup does NOT need precomputation.
`SEED-AR-95` — Missing security surfaces, trust boundaries, peak vs average. Staff.
`SEED-AR-96` — Fixed-window shared counter punishes legitimate enterprise burst. Principal.
`SEED-AR-97` — Whale tenant blocks smaller tenants in shared batch jobs. Staff.

### eval-5-global-control-plane (SEED-AR-98 through SEED-AR-107)

`SEED-AR-98` — Failover assumes 2x capacity, ignores partial availability. Principal.
`SEED-AR-99` — Shared DB health check cascades restarts when slow not down. Staff.
`SEED-AR-100` — Shared cross-region API key without rotation. Production.
`SEED-AR-101` — Negative control: replayable logs do NOT mandate multi-region DR.
`SEED-AR-102` — 200ms latency budget with 3-region hops is physically impossible. Principal.
`SEED-AR-103` — Negative control: optional analytics down should NOT trigger liveness.
`SEED-AR-104` — CAP violation: strong consistency + always available + partitions. Principal.
`SEED-AR-105` — Fixed-interval retries without backoff/jitter create thundering herd. Staff.
`SEED-AR-106` — Degradation strategy is "retry everything" with no priority. Staff.

### eval-6-event-sourced-marketplace (SEED-AR-107 through SEED-AR-116)

`SEED-AR-107` — Saga compensation without idempotency causes double refund. Staff.
`SEED-AR-108` — Write skew on inventory check-then-decrement. Staff.
`SEED-AR-109` — In-memory dedup lost on restart; events reprocessed. Staff.
`SEED-AR-110` — Negative control: single-service atomic does NOT need saga.
`SEED-AR-111` — CAS on inventory value fails under ABA; needs version counter. Distinguished.
`SEED-AR-112` — Negative control: read-only GET does NOT need idempotency.
`SEED-AR-113` — Missing failure modes, projection lag, stateful recovery paths. Staff.
`SEED-AR-114` — Hidden strong-consistency dependency on eventually-consistent search. Principal.
`SEED-AR-115` — Clock skew corrupts event ordering across distributed services. Principal.
`SEED-AR-116` — Idempotency key TTL < max replay window causes duplicate processing. Staff.
