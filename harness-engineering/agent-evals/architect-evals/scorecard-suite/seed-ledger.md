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
