# Seed Ledger - cr-eval-9-search-index-replica-projection (CR Staff+)

**Eval ID**: benchmark-suite / cr-eval-9-search-index-replica-projection
**Purpose**: Test Code Review agent on projection ordering, tombstone,
backfill, alias cutover, tenant routing, and observability defects that look
safe in local index tests but fail under distributed replica timelines.
**Difficulty**: Hard - evidence is distributed across source, tests, project
brief, and fake Programmer handoff.

## Seeds

### SEED-CR-55

Projection writes accept same-version events with `>=`, so redelivery or
backfill can overwrite current state with stale field values. Correct review
flags strict version-gate semantics.

Evidence: `src/search_projection.py` (`SearchProjection.apply_event`) and
`tests/test_search_projection.py` (strictly increasing versions only).

### SEED-CR-56

Tombstones use only a version number and can be overwritten by a late update or
backfill event with a higher version. Correct review flags resurrection of
deleted documents without a new aggregate generation.

Evidence: `src/search_projection.py` (`apply_event`) and `project-brief.md`
(AC-2).

### SEED-CR-57

Alias cutover swaps the read alias without calling the readiness check for
per-shard target versions. Correct review flags partial replica cutover.

Evidence: `src/search_projection.py` (`AliasManager.swap_alias`,
`ReplicationLagMonitor.ready_for_cutover`).

### SEED-CR-58

Backfill uses a static field allowlist that drops newer schema fields required
by current search reads. Correct review flags schema drift across migration and
projection paths.

Evidence: `src/search_projection.py` (`BackfillMapper`) and fake handoff
backfill claim.

### SEED-CR-59

Shard routing falls back to a shared default tenant route when tenant context is
missing. Correct review flags storage-level tenant leakage even when query
filters are present.

Evidence: `src/search_projection.py` (`ShardRouter.route`) and
`project-brief.md` (AC-5).

### SEED-CR-60

Projection metrics aggregate applied/rejected events but omit tenant, shard,
version gap, alias generation, and backfill progress dimensions. Correct review
treats this as an operational incident gap.

Evidence: `src/search_projection.py` (`ReplicationMetrics`) and fake handoff
observability claim.

### SEED-CR-61

Tests cover create/update/delete, older-version rejection, alias swap after
convergence, backfill original fields, routing determinism, and aggregate
metrics, but omit same-version replay, tombstone resurrection, lagging shard
cutover, schema drift, tenant fallback, and metric dimensions.

Evidence: `tests/test_search_projection.py` and fake handoff coverage claim.

### SEED-CR-NC-13

`VersionGatedWriter` correctly accepts only strictly newer versions. Correct
review should not misflag same-version skips as dropped updates.

Evidence: `src/search_projection.py` (`VersionGatedWriter`) and
`tests/test_search_projection.py` (`test_version_gated_writer_skips_same_version`).

### SEED-CR-NC-14

`TenantShardValidator` rejects writes whose tenant is not assigned to the shard.
Correct review should not misflag this as redundant with query-time filtering.

Evidence: `src/search_projection.py` (`TenantShardValidator`) and
`tests/test_search_projection.py` (`test_tenant_shard_validator_rejects_wrong_shard`).

## Scoring Guide

| Score | Criteria |
|-------|----------|
| CAUGHT | CR identifies the seeded issue and its production/security consequence. |
| PARTIAL | CR identifies a related concern but misses the causal chain or severity. |
| MISSED | CR does not flag the issue. |
| FALSE_POSITIVE | CR flags a negative-control behavior as a defect. |
