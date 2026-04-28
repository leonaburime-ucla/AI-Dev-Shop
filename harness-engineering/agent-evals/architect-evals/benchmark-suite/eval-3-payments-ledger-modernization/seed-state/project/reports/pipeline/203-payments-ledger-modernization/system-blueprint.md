# System Blueprint — Payments Ledger Modernization

- Status: APPROVED
- Scope: Existing system modernization

## Macro Components

- payment command path
- ledger write model
- balance query path
- async notification adapters
- audit and investigation tooling

## Runtime Topology

- synchronous payment acceptance path
- async side-effect path for notifications and partner sync
- investigation and reconciliation path

## Dominant Quality Attributes

- compliance_auditability
- data_consistency
- security

## Risks

- async side effects can drift away from the authoritative ledger
- simplistic decomposition can hide balance invariant risk
- release windows are coordinated by compliance, not by service autonomy
- two macro directions remain plausible after the first pass: a modular
  monolith with a more adaptable ledger slice, or an earlier split into
  service boundaries for runtime autonomy. The fit is close enough that
  adaptability should break ties when raw match alone is not decisive.

## Spec Decomposition

- `core-foundation`
- `ledger-domain`
- `balance-query-domain`
- `notifications-domain`
