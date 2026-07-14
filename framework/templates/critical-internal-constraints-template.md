# Critical Internal Constraints: <feature-name>

- Spec: SPEC-<id> v<version> (hash: <sha256>)
- ADR: ADR-<id>
- Implementation Outline: <path to implementation-outline.md OR "SKIP - <reason>">
- Prior designations consulted: <prior CIC artifact paths for touched units, with re-affirmed / superseded / promoted per unit, OR "none found">
- Status: PRODUCED
- Trigger result: <trigger names with unit counts>
- Source sync: <verified <date> | STALE - <changed IDs>>
- Date: <ISO-8601 UTC>
- Author: Software Architect

> This artifact is a constraint ledger for designated complex units only — it records load-bearing internal constraints where a plausible implementation can satisfy the public contract yet still violate correctness, security, recovery, parity, or an explicit NFR budget. It must not contain call flows, class layouts, code or pseudo-code at any granularity, constraints for non-designated units, restated Implementation Outline content, or task sequencing. Do not create this file when no trigger applies — record `Critical Internal Constraints: NOT TRIGGERED - <candidate units checked; checked surfaces; why no trigger applies>` in the ADR and handoff instead.

## Trigger Decision Matrix

A designation is valid only with all four parts: candidate unit, plausible wrong implementation, broken property, required constraint.

| Trigger | Applies? | Designated Unit(s) | Plausible Wrong Implementation | Broken Property | Required Constraint | Source Trace |
|---|---:|---|---|---|---|---|
| Algorithmic Correctness Constraint | yes/no | <U-xxx> | <what a competent implementer might do> | <AC/invariant/parity/budget it violates> | <internal constraint that prevents it> | <AC/ADR/outline/ref> |
| Stateful Protocol Constraint | yes/no | <U-xxx> | <...> | <...> | <internal constraint that prevents it> | <AC/ADR/outline/ref> |
| Concurrency / Ordering / Idempotency Constraint | yes/no | <U-xxx> | <...> | <...> | <internal constraint that prevents it> | <AC/ADR/outline/ref> |
| Security-Critical Sequencing Constraint | yes/no | <U-xxx> | <...> | <...> | <internal constraint that prevents it> | <AC/red-team/ref> |
| Explicit Performance Budget Constraint | yes/no | <U-xxx> | <...> | <named NFR budget> | <internal constraint that prevents it> | <NFR/ADR/ref> |
| Failure / Recovery Constraint | yes/no | <U-xxx> | <...> | <...> | <internal constraint that prevents it> | <AC/ADR/ref> |
| Characterization Parity Constraint | yes/no | <U-xxx> | <...> | <...> | <internal constraint that prevents it> | <characterization/ref> |

## Designated Units

| Unit ID | Name | Location (module / contract ref) | Designating Trigger(s) | Outline Refs | Trace |
|---|---|---|---|---|---|
| U-001 | <name> | <module or `C-xxx`> | <trigger names> | <C-xxx / INV-xxx or N/A> | <AC/ADR/ref> |

## Unit Constraints

Repeat per designated unit. Include only the subsections that apply; omit the rest.

### U-001 <name>

- Responsibility: <the unit's single job>
- Designation: <trigger + plausible wrong implementation + broken property + required constraint, one line each>
- Outline refs: <C-xxx / INV-xxx or N/A>

#### Binding Constraints

Escalation markers default by trigger: Security-Critical Sequencing → `ESCALATE_SECURITY`; money movement, permanent deletion, privilege mutation, or non-idempotent external effects → `ESCALATE_IRREVERSIBLE`. Omitting a default marker requires a recorded reason in the row.

| ID | Constraint | Escalation Marker | Property Protected | Verification Surface | Trace |
|---|---|---|---|---|---|
| U-001-B1 | <internal decision downstream must preserve> | — / ESCALATE_SECURITY / ESCALATE_IRREVERSIBLE | <what breaks without it> | <observable surface: API result / persisted state / event / external-call boundary / error / recovery result / approved seam> OR `audit-only: <reason>` | <AC/ADR/NFR/ref> |

#### State Machine (Stateful Protocol Constraint only)

| ID | State | Event / Input | Next State | Guard / Precondition | Escalation Marker |
|---|---|---|---|---|---|
| U-001-SM1 | <state> | <event> | <state> | <guard> | — / ESCALATE_SECURITY / ESCALATE_IRREVERSIBLE |

- Illegal states / transitions: <list and the property each violation breaks>
- State persistence: <where state lives; recovery source of truth>

#### Required Ordering Constraints

Only orderings where reversing or omitting the order breaks a named property. No full call flows; no private helper names unless approved test seams or public boundaries.

| ID | Required Ordering | Property Protected | Observable Verification Surface | Escalation Marker | Trace |
|---|---|---|---|---|---|
| U-001-ORD1 | <X completes before Y> | <what breaks if reversed/omitted> | <observable outcome, not private call order> | — / ESCALATE_SECURITY / ESCALATE_IRREVERSIBLE | <REQ/C/INV/ADR> |

#### Failure / Recovery Constraints

| ID | Failure Point | Required Behavior | Partial-State Rule | Verification Surface | Escalation Marker |
|---|---|---|---|---|---|
| U-001-F1 | <where it can fail> | <retry/abort/compensate rule> | <what may/may not persist> | <observable recovery outcome> | — / ESCALATE_SECURITY / ESCALATE_IRREVERSIBLE |

#### Invariant References

Do not create a second invariant ledger here. Cite the outline `INV-xxx` IDs or ADR/spec evidence that support the Binding constraints above; a newly discovered invariant is expressed as a Binding constraint row instead.

| Reference | Source | Binding Constraint IDs Supported |
|---|---|---|
| INV-001 | <outline/ADR/spec> | <U-001-B1, U-001-ORD1> |

#### Design Context (optional, non-binding)

<Short note recording the architect's reasoning. Creates no audit obligations and must not smuggle in de facto constraints.>

## Deviation And Promotion Protocol

- Escalation-marked constraints (`ESCALATE_SECURITY`, `ESCALATE_IRREVERSIBLE`): pause and route to Coordinator **before** deviating. Approval is a recorded `[CIC_DEVIATION_APPROVED] Unit=<U-xxx> Constraint=<constraint ID> ApprovedBy=<Software Architect via Coordinator> Date=<ISO-8601> Rationale=<one line>` entry; deviation without a matching approval record = Architecture Audit BLOCKER.
- Other Binding constraints: deviate only with a recorded `[CIC_DEVIATION]` entry (Unit ID, constraint ID, what was done instead, why, effect on invariants and tests). Unrecorded deviation = WARNING minimum.
- Before final handoff, Programmer confirms each in-scope Binding constraint still applies, records a deviation, or requests reclassification.
- Downstream proposals: `[CIC_PROPOSED] Unit=<U-xxx or candidate> Trigger=<trigger> Constraint=<proposed Binding text> Property=<what breaks> VerificationSurface=<observable surface or audit-only> Evidence=<test/code/legacy/ADR/spec trace>` — Architect/Coordinator ratifies, revises, or rejects before final Architecture Audit.
- Downstream requests: `[CIC_REQUESTED] Unit=<candidate> Trigger=<trigger> PlausibleWrong=<what a competent implementer might do> Property=<what breaks> MissingConstraint=<required constraint> Evidence=<ADR/spec/outline/test/code trace>` — Coordinator routes to the Software Architect before proceeding.
- Rejected proposals after work continued: Coordinator routes the rejection to TDD/Programmer to reconcile tests or code written assuming the proposed constraint; rejection and reconciliation outcome recorded in the handoff chain.

## Downstream Handoff Notes

- Coordinator: <tasks touching designated units must reference Unit IDs; source-sync IDs to watch>
- TDD focus: <which Binding constraints and verification surfaces to encode as tests first; audit-only constraints excluded from TDD>
- Programmer audit focus: <which Binding constraints the Architecture Audit must check; escalation-marked constraints in scope>
- Open risks or ambiguities: <none or list>
