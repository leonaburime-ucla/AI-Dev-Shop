# Seed Ledger - cr-eval-7-stream-watermark-checkpoint (CR Staff+)

**Eval ID**: benchmark-suite / cr-eval-7-stream-watermark-checkpoint
**Purpose**: Test Code Review agent on stream watermark, late-event,
checkpoint, rebalance, cleanup, and observability defects that look locally
reasonable but fail under partition drift and recovery timelines.
**Difficulty**: Hard - evidence is distributed across source, tests, project
brief, and fake Programmer handoff.

## Seeds

### SEED-CR-41

The global watermark advances from the maximum partition watermark instead of
the minimum active partition watermark. Correct review flags premature window
closure when one partition is ahead of another.

Evidence: `src/stream_watermarks.py` (`StreamProcessor.advance_watermark`) and
`tests/test_stream_watermarks.py` (lockstep partition coverage only).

### SEED-CR-42

Events beyond the allowed lateness window are silently dropped instead of being
routed to the late-event sink with metadata. Correct review distinguishes this
from the valid within-window late-event aggregation path.

Evidence: `src/stream_watermarks.py` (`StreamProcessor.process_event`) and
`project-brief.md` (AC-2).

### SEED-CR-43

Checkpoint state is committed before output sink emission is durably recorded.
Correct review flags the crash window that can skip output after restart.

Evidence: `src/stream_watermarks.py` (`flush_closed_windows`) and fake handoff
checkpoint claim.

### SEED-CR-44

Rebalance loads checkpoints for newly assigned partitions but does not clear
active windows for revoked partitions. Correct review flags stale window flush
and duplicate output after ownership changes.

Evidence: `src/stream_watermarks.py` (`on_rebalance`, `flush_closed_windows`).

### SEED-CR-45

Expired window cleanup only runs when another event is processed. Correct
review flags unbounded state growth for idle partitions and low-traffic tenants.

Evidence: `src/stream_watermarks.py` (`process_event`,
`_cleanup_expired_windows`) and `project-brief.md` (AC-5).

### SEED-CR-46

Metrics record aggregate counters but omit partition, tenant, checkpoint-age,
and state-size dimensions. Correct review treats this as an operational
diagnosis gap, not a logging preference.

Evidence: `src/stream_watermarks.py` (`StreamMetrics`) and fake handoff
observability claim.

### SEED-CR-47

Tests cover single-partition and lockstep happy paths but omit divergent
watermarks, beyond-window late routing, crash ordering, rebalance stale flush,
idle cleanup, and metric dimensions.

Evidence: `tests/test_stream_watermarks.py` and fake handoff coverage claim.

### SEED-CR-NC-09

`PartitionWatermarkTracker` correctly uses max event time per partition and a
minimum across active partitions. Correct review should not misflag the
partition-local max update as the global max-watermark defect.

Evidence: `src/stream_watermarks.py` (`PartitionWatermarkTracker`) and
`tests/test_stream_watermarks.py` (`test_partition_tracker_uses_minimum_active_watermark`).

### SEED-CR-NC-10

`LateEventRouter` intentionally removes beyond-window events from aggregation
and publishes metadata to the late-event sink. Correct review should not
misflag this as data loss.

Evidence: `src/stream_watermarks.py` (`LateEventRouter`) and
`tests/test_stream_watermarks.py` (`test_late_event_router_keeps_metadata`).

## Scoring Guide

| Score | Criteria |
|-------|----------|
| CAUGHT | CR identifies the seeded issue and its production consequence. |
| PARTIAL | CR identifies a related concern but misses the causal chain or severity. |
| MISSED | CR does not flag the issue. |
| FALSE_POSITIVE | CR flags a negative-control behavior as a defect. |
