# Controls — Architect Scorecard Suite

Suite kind: `benchmark`

Positive controls:

- `SEED-AR-01` — obvious standalone security pressure
- `SEED-AR-15` — obvious regulated compliance/auditability pressure

Negative controls:

- `SEED-AR-12` — do not invent tenant isolation for a single-enterprise system
- `SEED-AR-23` — do not invent disaster recovery requirements without RPO/RTO or failover needs
- `SEED-AR-21` — do not invent deployment independence under coordinated
  regulated release windows
- `SEED-AR-31` — do not invent compliance/auditability from generic replay and observability needs
- `SEED-AR-35` — do not invent performance requirements without explicit latency or throughput targets
- `SEED-AR-43` — do not invent tenant isolation from role-scoped internal RAG workspaces
- `SEED-AR-50` — do not invent data consistency from read-only API aggregation
- `SEED-AR-59` — do not invent disaster recovery from replayable event logs alone

Regression controls:

- `SEED-AR-20` — preserve separate modularity scoring after the scorecard
  redesign

Why these packs exist:

- Positive controls verify the Architect is awake and applying the obvious
  parts of the scorecard.
- Negative controls measure false-positive behavior on optional-axis
  activation.
- The breadth expansion also uses negative controls to measure conditional-skill
  restraint, not just optional-axis restraint.
- Regression control preserves the new modularity/modifiability distinction.
- `SEED-AR-04` was reclassified from a negative control to a standard seed
  after external audit showed the fixture legitimately contains audit-trail
  activation signals under the current skill.
