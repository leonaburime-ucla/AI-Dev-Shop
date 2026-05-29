# Search Index Replica Projection - Project Brief

## Overview

A projection worker consumes primary database change events and maintains
tenant-scoped search indexes. It applies versioned create/update/delete events,
handles tombstones, runs schema backfills, routes documents to shards, swaps
read aliases during index rebuilds, and reports replication lag.

This eval is intentionally focused on Code Review depth. The projection code
looks complete and the tests cover direct create/update/delete behavior, but
production failures emerge only when event versions, tombstone semantics,
backfill schema drift, per-shard readiness, tenant routing, and observability
interact.

## Requirements

### Functional Requirements

1. Projection writes apply only strictly newer aggregate versions; same-version
   replays are idempotent skips.
2. Tombstones cannot be resurrected by late updates or backfill events unless a
   new aggregate generation explicitly recreates the document.
3. Alias cutover waits for every shard and replica to reach the target version
   and backfill generation.
4. Backfill schema mapping preserves all fields required by the current search
   contract.
5. Shard routing and storage-level operations maintain tenant isolation, not
   only query-time filters.
6. Lag and projection metrics include tenant, shard, max version, alias
   generation, tombstones, and backfill progress.
7. Tests must cover out-of-order versions, tombstone resurrection, partial
   shard cutover, schema drift, tenant routing fallback, and metric dimensions.

### Acceptance Criteria

- AC-1: Older and same-version replayed events do not overwrite newer index
  state.
- AC-2: Deletes remain durable against late update and backfill events.
- AC-3: Alias cutover fails closed until all shards reach the target version.
- AC-4: Backfill preserves new schema fields required by current reads.
- AC-5: Documents missing tenant context are rejected instead of falling back to
  shared routing.
- AC-6: Metrics can identify lag by tenant, shard, version, and generation.
- AC-7: The test suite covers the interaction cases above.
- AC-8: Correct strict-version idempotency and tenant shard validation helpers
  are valid and should not be flagged as defects.

## Spec Hash

`spec-search-index-replica-projection-v1-yza567`
