# Cache Migration Rollout - Project Brief

## Overview

A customer profile service is migrating from a legacy v1 cache shape to a v2
profile schema behind feature flags. The migration runs in rolling phases:
legacy reads, dual writes, shadow reads, backfill, partial read rollout,
promotion, and rollback support.

This eval is intentionally focused on Code Review depth. The code looks like a
normal migration coordinator and the tests exercise direct read/write paths,
but production failures emerge when stale cache repopulation, schema
compatibility, feature flag combinations, backfill watermarks, and rollout
observability interact.

## Requirements

### Functional Requirements

1. Cache keys and invalidation must prevent stale legacy reads from
   repopulating current data after writes.
2. During the rollback window, profile writes must remain lossless for both v1
   and v2 readers.
3. Schema translators must preserve safety-sensitive fields across forward and
   rollback transforms and deny-by-default when required fields are absent.
4. Feature flag combinations must not create unsupported read/write states.
5. Backfill and cutover require tenant-specific watermarks and cache-generation
   readiness before promotion.
6. Shadow-read and migration metrics must include schema version, cache
   generation, source cache, tenant, and active flag set.
7. Tests must cover stale repopulation, dual-read/write rollback, unsupported
   flag combinations, schema compatibility, and cutover readiness.

### Acceptance Criteria

- AC-1: Legacy and v2 cache reads return equivalent profile data during the
  migration window.
- AC-2: Writes during the rollback window are available to both old and new
  readers without losing fields.
- AC-3: Missing or renamed safety fields do not silently default to an unsafe
  value.
- AC-4: Unsupported feature flag combinations are rejected or fail closed.
- AC-5: Promotion waits for backfill and cache-generation convergence.
- AC-6: Stale snapshot repopulation cannot overwrite fresh cache state.
- AC-7: Observability exposes the dimensions needed to debug rollout drift.
- AC-8: Versioned cache keys and explicit dual-write shims are valid and should
  not be flagged as defects.

## Spec Hash

`spec-cache-migration-rollout-v1-pqr678`
