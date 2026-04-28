# System Blueprint — Team Chat Platform

- Status: APPROVED
- Scope: Greenfield

## Macro Components

- web app
- API/backend
- background jobs
- file storage
- plugin integration adapters

## Runtime Topology

- web client
- single backend deployable for core product logic
- worker process for async notifications and attachment processing

## Dominant Quality Attributes

- tenant isolation
- modifiability
- operability

## Risks

- plugin surface could grow faster than the team
- attachment processing expands attack surface

## Spec Decomposition

- `core-foundation`
- `chat-domain`
- `attachments-domain`
- `plugins-domain`
