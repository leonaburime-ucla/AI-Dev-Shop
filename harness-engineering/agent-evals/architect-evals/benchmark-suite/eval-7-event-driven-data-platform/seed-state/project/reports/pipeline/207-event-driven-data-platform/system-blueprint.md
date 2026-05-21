# System Blueprint — Event-Driven Data Platform

- Status: APPROVED
- Scope: Brownfield modernization

## Macro Components

- source capture and change extraction
- durable event log
- schema contract and compatibility layer
- consumer delivery and warehouse-serving paths
- replay, investigation, and migration-control tooling

## Runtime Topology

- CDC or source-capture path from operational systems
- streaming consumer path for priority downstream domains
- legacy batch coexistence path during migration
- replay and backfill path for recovery and onboarding

## Dominant Quality Attributes

- data_consistency
- deployment_independence
- performance

## Risks

- coexistence between legacy batch and new streaming paths creates material
  change-management pressure during rollout
- lag, replay, dead-letter, and schema-drift observability must be first-class
  or the migration becomes operationally opaque
- broker, CDC, and processing-shape choices remain open enough that vendor
  certainty would be unjustified without more research
- replayable logs improve recovery options, but no explicit RPO, RTO, or
  multi-region failover objective is currently stated
- two macro directions remain plausible after first pass: an upgraded
  micro-batch plus CDC pipeline, or a fuller event-streaming backbone with more
  durable replay semantics
- a bespoke event mesh is architecturally tempting but would violate the
  constitution unless real constraints prove it necessary

## Spec Decomposition

- `capture-domain`
- `event-contract-domain`
- `consumer-delivery-domain`
- `warehouse-serving-domain`
- `migration-ops-domain`
