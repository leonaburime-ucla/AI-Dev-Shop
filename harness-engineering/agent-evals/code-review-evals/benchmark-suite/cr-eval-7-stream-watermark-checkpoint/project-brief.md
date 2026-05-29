# Stream Watermark Checkpoint - Project Brief

## Overview

A streaming aggregation worker consumes event-time records from multiple
partitions, maintains per-partition watermarks, aggregates into tumbling
windows, handles late events, emits window results, stores checkpoints, and
exposes operational metrics for lag and state growth.

This eval is intentionally focused on Code Review depth. The worker looks like
a normal streaming component and the tests exercise plausible happy paths, but
production failures emerge only when partitions drift, late events arrive after
the grace window, checkpoint durability and sink durability diverge, and
rebalances leave stale in-memory state behind.

## Requirements

### Functional Requirements

1. The global watermark advances from the minimum active partition watermark,
   with explicit idle-partition handling.
2. Late events inside the allowed lateness window are aggregated, while events
   beyond that window route to a late-event sink with full metadata.
3. Checkpoints are committed only after window output side effects are durably
   confirmed.
4. Partition rebalance must not let revoked partition state flush after
   ownership changes.
5. Window state cleanup must be bounded even when no new events arrive.
6. Metrics must expose partition lag, late-event rate, checkpoint age, state
   size, tenant, and partition dimensions.
7. Tests must cover divergent partitions, late-event routing, crash ordering,
   rebalance flush, idle cleanup, and metrics dimensions.

### Acceptance Criteria

- AC-1: A lagging partition prevents the global watermark from passing its
  event-time frontier unless it is explicitly marked idle.
- AC-2: Beyond-window late events are routed to a late-event sink, not silently
  discarded.
- AC-3: A crash after checkpoint but before sink emission cannot lose output.
- AC-4: Rebalance removes in-memory windows for revoked partitions.
- AC-5: Closed windows are cleaned up through a periodic or lifecycle hook, not
  only when another event arrives.
- AC-6: Metrics can identify which tenant and partition is lagging or growing
  state.
- AC-7: The test suite covers the interaction cases above.
- AC-8: Correct partition-local watermark and late-event routing helpers are
  valid and should not be flagged as defects.

## Spec Hash

`spec-stream-watermark-checkpoint-v1-stu901`
