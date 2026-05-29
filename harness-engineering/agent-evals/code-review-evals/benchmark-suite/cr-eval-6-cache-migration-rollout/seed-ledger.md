# Seed Ledger - cr-eval-6-cache-migration-rollout (CR Staff+)

**Eval ID**: benchmark-suite / cr-eval-6-cache-migration-rollout
**Purpose**: Test Code Review agent on cache migration and rollout defects that
look safe in local read/write tests but fail under stale snapshots, schema
compatibility, feature flags, backfill, and rollback.
**Difficulty**: Hard - evidence is distributed across source, tests, project
brief, and fake Programmer handoff.

## Seeds

### SEED-CR-34

Stale legacy snapshots can repopulate the shared cache after a fresher write
because repopulation ignores cache generation. Correct review flags distributed
state divergence during cache invalidation and repopulation.

Evidence: `src/cache_migration.py` (`repopulate_legacy_cache`,
`write_profile`) and `project-brief.md` (AC-6).

### SEED-CR-35

The v2 write path can skip the legacy cache while old readers are still active,
creating a rollback/read window where updates disappear for v1 clients. Correct
review flags the dual-write migration data-loss window.

Evidence: `src/cache_migration.py` (`write_profile`) and fake handoff rollout
claim.

### SEED-CR-36

Schema translation silently defaults missing risk fields and drops v2-only
fields on rollback. Correct review flags the serialization/type-contract escape
instead of trusting the local dataclass shape.

Evidence: `src/cache_migration.py` (`SchemaTransformer`) and missing contract
tests.

### SEED-CR-37

Independent read, write, dual-write, and backfill flags can combine into
unsupported states. Correct review flags the lack of configuration validation
for rollout flag interactions.

Evidence: `src/cache_migration.py` (`MigrationFlags`, `write_profile`,
`read_profile`).

### SEED-CR-38

Tenant promotion only checks a backfill flag and ignores cache generation
convergence, allowing cutover before warm-up catches the latest writes. Correct
review flags the migration temporal hazard.

Evidence: `src/cache_migration.py` (`mark_backfill_complete`,
`promote_tenant`).

### SEED-CR-39

Shadow-read mismatch metrics increment counters but omit user, schema version,
source cache, generation, tenant, and flag set. Correct review treats this as a
rollout observability defect.

Evidence: `src/cache_migration.py` (`MigrationMetrics`) and fake handoff
observability claim.

### SEED-CR-40

Tests cover static read and write modes but omit stale repopulation, rollback
dual-read/write, unsupported flag combinations, schema-compatibility failures,
and partial backfill promotion.

Evidence: `tests/test_cache_migration.py` and fake handoff coverage claim.

### SEED-CR-NC-07

`versioned_cache_key` explicitly includes schema version and tenant. Correct
review should not misflag versioned keys as redundant storage.

Evidence: `src/cache_migration.py` (`versioned_cache_key`) and
`tests/test_cache_migration.py` (`test_versioned_cache_key_is_schema_scoped`).

### SEED-CR-NC-08

`DualWriteCompatibilityShim` writes a lossless v1/v2 pair during the rollback
window. Correct review should not misflag it as duplicate work.

Evidence: `src/cache_migration.py` (`DualWriteCompatibilityShim`) and
`tests/test_cache_migration.py` (`test_dual_write_compatibility_shim_is_lossless`).

## Scoring Guide

| Score | Criteria |
|-------|----------|
| CAUGHT | CR identifies the seeded issue and its production consequence. |
| PARTIAL | CR identifies a related concern but misses the causal chain or severity. |
| MISSED | CR does not flag the issue. |
| FALSE_POSITIVE | CR flags a negative-control behavior as a defect. |
