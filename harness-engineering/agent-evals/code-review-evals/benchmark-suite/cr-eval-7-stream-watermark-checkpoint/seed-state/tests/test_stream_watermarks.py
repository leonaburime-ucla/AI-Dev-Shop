from __future__ import annotations

from src.stream_watermarks import (
    LateEventRouter,
    LateEventSink,
    PartitionWatermarkTracker,
    StreamEvent,
    StreamProcessor,
)


def event(
    event_id: str,
    *,
    partition: int = 0,
    event_time: float = 10.0,
    value: int = 1,
) -> StreamEvent:
    return StreamEvent(
        event_id=event_id,
        tenant_id="tenant-a",
        partition=partition,
        event_time=event_time,
        value=value,
    )


def test_lockstep_partitions_advance_watermark() -> None:
    processor = StreamProcessor(assigned_partitions={0, 1})

    processor.process_event(event("a", partition=0, event_time=60), now=100)
    processor.process_event(event("b", partition=1, event_time=60), now=101)

    assert processor.global_watermark == 60


def test_late_event_within_window_is_aggregated() -> None:
    processor = StreamProcessor(assigned_partitions={0}, allowed_lateness=30)
    processor.process_event(event("lead", event_time=100, value=2), now=100)

    processor.process_event(event("late", event_time=80, value=3), now=101)

    assert sum(processor.active_windows.values()) == 5
    assert processor.late_sink.events == []


def test_closed_window_emits_result() -> None:
    processor = StreamProcessor(assigned_partitions={0}, window_size=60)
    processor.process_event(event("a", event_time=10, value=4), now=100)
    processor.process_event(event("b", event_time=65, value=1), now=101)

    processor.flush_closed_windows()

    assert processor.output_sink.results[0].total == 4
    assert processor.checkpoint_store.positions[0] == 60


def test_rebalance_restores_partition_checkpoint() -> None:
    processor = StreamProcessor(assigned_partitions={0})
    processor.checkpoint_store.commit(1, 120)

    processor.on_rebalance({1})

    assert processor.assigned_partitions == {1}
    assert processor.partition_watermarks[1] == 120


def test_cleanup_runs_during_active_processing() -> None:
    processor = StreamProcessor(assigned_partitions={0}, cleanup_delay=10)
    processor.active_windows[(0, 0)] = 3
    processor.global_watermark = 100

    processor.process_event(event("new", event_time=100, value=1), now=200)

    assert (0, 0) not in processor.active_windows


def test_partition_tracker_uses_minimum_active_watermark() -> None:
    tracker = PartitionWatermarkTracker(idle_after_seconds=300)
    tracker.observe(0, event_time=100, now=10)
    tracker.observe(1, event_time=70, now=10)

    assert tracker.minimum_active({0, 1}, now=20) == 70


def test_late_event_router_keeps_metadata() -> None:
    sink = LateEventSink()
    router = LateEventRouter(sink)

    router.route(event("late", partition=2, event_time=5), "beyond_lateness")

    assert sink.events == [
        {
            "event_id": "late",
            "tenant_id": "tenant-a",
            "partition": 2,
            "event_time": 5,
            "reason": "beyond_lateness",
        }
    ]
