# Controls - System Blueprint Benchmark Suite

The suite uses explicit controls so scoring can separate real misses from false-positive tendency and regression drift.

## Positive Controls

- `SBP-SEED-01`: contradictory product constraints block stable decomposition. Expected: agent escalates or asks clarification.
- `SBP-SEED-11`: stack direction is finalized before the mandatory human tradeoff checkpoint. Expected: agent presents 2-3 directions and pauses.
- `SBP-SEED-21`: spec decomposition lacks P0 Core/Foundation. Expected: agent creates a required P0 package.

## Negative Controls

- `SBP-SEED-09`: user mandates a single-app monolith for MVP. Expected: agent does not force microservices.
- `SBP-SEED-10`: admin/reporting domains are explicitly deferred. Expected: agent keeps them out of MVP.
- `SBP-SEED-19`: only two dominant quality attributes are named. Expected: agent does not force exactly three.
- `SBP-SEED-20`: ownership is clear in the control variant. Expected: agent does not invent uncertainty.
- `SBP-SEED-29`: horizontal Core/Foundation platform slice is explicitly justified. Expected: agent accepts it.
- `SBP-SEED-30`: P0 is validly thin. Expected: agent does not invent feature-owned schema in P0.

## Regression Controls

- `SBP-SEED-08`: guarded failure mode where blueprint imported prior-project domains.
- `SBP-SEED-18`: guarded failure mode where quality attributes were scored at blueprint stage.
- `SBP-SEED-28`: guarded failure mode where agent wrote detailed feature specs instead of decomposition packages.

## Scoring Notes

- Negative controls are scored only as `CORRECT_SKIP` or `FALSE_POSITIVE`.
- Non-negative controls are scored only as `CAUGHT`, `PARTIAL`, or `MISSED`.
- This suite evaluates System Blueprint output behavior against persona and skill requirements.
- The agent under test must not see this file, `seed-catalog.tsv`, or `seed-ledger.md`.
