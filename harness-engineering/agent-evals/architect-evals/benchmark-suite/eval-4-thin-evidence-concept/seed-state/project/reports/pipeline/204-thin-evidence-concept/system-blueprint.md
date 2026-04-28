# System Blueprint — Thin Evidence Concept

- Status: APPROVED
- Scope: Concept exploration

## Macro Components

- web app
- API/backend
- record storage
- optional attachment handling

## Runtime Topology

- likely one web/API deployable in the first release
- optional background work if attachments or indexing become heavier later
- final auth and integration boundaries are not settled yet

## Dominant Quality Attributes

- adaptability
- modifiability
- operability

## Risks

- internal-only versus customer-facing rollout is unresolved
- single-tenant versus multi-tenant shape is unresolved
- traffic and attachment volume are unknown
- security posture and auth split are not yet final
- the architecture should not overfit today's guesses

## Spec Decomposition

- `core-foundation`
- `records-domain`
- `workflow-domain`
- `attachments-domain`
