# System Blueprint — Analytics Export Platform

- Status: APPROVED
- Scope: Existing codebase extension

## Macro Components

- ingestion adapters
- event storage
- aggregation pipeline
- dashboard query service
- export orchestrator

## Runtime Topology

- app-facing query path
- async ingestion path
- scheduled export path

## Dominant Quality Attributes

- performance
- integration complexity
- deployment independence

## Risks

- partner API failures can cascade into missed export windows
- more data sources increase replay and observability pressure
- there is no dedicated SRE or platform engineer; replay tooling, queue
  operations, and async failure handling fall to two product engineers sharing
  business-hours on-call
- stakeholders keep saying the current volume is small enough that the platform
  should scale without significant redesign, but no measured evidence or
  durable threshold backs that assumption

## Spec Decomposition

- `core-foundation`
- `ingestion-domain`
- `aggregation-domain`
- `exports-domain`
