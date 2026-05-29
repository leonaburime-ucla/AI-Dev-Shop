"""Streaming aggregation worker with watermark and checkpoint handling."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StreamEvent:
    event_id: str
    tenant_id: str
    partition: int
    event_time: float
    value: int


@dataclass(frozen=True)
class WindowResult:
    tenant_id: str
    partition: int
    window_start: float
    window_end: float
    total: int


class OutputSink:
    def __init__(self) -> None:
        self.results: list[WindowResult] = []

    def emit(self, result: WindowResult) -> None:
        self.results.append(result)


class CheckpointStore:
    def __init__(self) -> None:
        self.positions: dict[int, float] = {}

    def commit(self, partition: int, watermark: float) -> None:
        self.positions[partition] = watermark

    def load(self, partition: int) -> float:
        return self.positions.get(partition, 0.0)


class LateEventSink:
    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    def publish(self, event: StreamEvent, reason: str) -> None:
        self.events.append(
            {
                "event_id": event.event_id,
                "tenant_id": event.tenant_id,
                "partition": event.partition,
                "event_time": event.event_time,
                "reason": reason,
            }
        )


class StreamMetrics:
    def __init__(self) -> None:
        self.counters = {
            "events": 0,
            "late_events": 0,
            "checkpoints": 0,
            "windows_flushed": 0,
        }

    def record_event(self) -> None:
        self.counters["events"] += 1

    def record_late_event(self) -> None:
        self.counters["late_events"] += 1

    def record_checkpoint(self) -> None:
        self.counters["checkpoints"] += 1

    def record_window_flush(self) -> None:
        self.counters["windows_flushed"] += 1


class PartitionWatermarkTracker:
    """Correct helper: max per partition, minimum across active partitions."""

    def __init__(self, idle_after_seconds: float) -> None:
        self.idle_after_seconds = idle_after_seconds
        self.watermarks: dict[int, float] = {}
        self.last_seen: dict[int, float] = {}

    def observe(self, partition: int, event_time: float, now: float) -> None:
        self.watermarks[partition] = max(self.watermarks.get(partition, 0.0), event_time)
        self.last_seen[partition] = now

    def minimum_active(self, assigned_partitions: set[int], now: float) -> float:
        active = [
            self.watermarks.get(partition, 0.0)
            for partition in assigned_partitions
            if now - self.last_seen.get(partition, now) <= self.idle_after_seconds
        ]
        return min(active) if active else 0.0


class LateEventRouter:
    """Correct helper: remove late data from aggregation while preserving evidence."""

    def __init__(self, sink: LateEventSink) -> None:
        self.sink = sink

    def route(self, event: StreamEvent, reason: str) -> None:
        self.sink.publish(event, reason)


class StreamProcessor:
    def __init__(
        self,
        *,
        assigned_partitions: set[int],
        window_size: float = 60.0,
        allowed_lateness: float = 30.0,
        cleanup_delay: float = 300.0,
    ) -> None:
        self.assigned_partitions = set(assigned_partitions)
        self.window_size = window_size
        self.allowed_lateness = allowed_lateness
        self.cleanup_delay = cleanup_delay
        self.partition_watermarks: dict[int, float] = {
            partition: 0.0 for partition in assigned_partitions
        }
        self.global_watermark = 0.0
        self.active_windows: dict[tuple[int, float], int] = {}
        self.output_sink = OutputSink()
        self.checkpoint_store = CheckpointStore()
        self.late_sink = LateEventSink()
        self.metrics = StreamMetrics()

    def advance_watermark(self, partition: int, event_time: float) -> float:
        self.partition_watermarks[partition] = max(
            self.partition_watermarks.get(partition, 0.0),
            event_time,
        )
        if self.partition_watermarks:
            self.global_watermark = max(self.partition_watermarks.values())
        return self.global_watermark

    def process_event(self, event: StreamEvent, now: float) -> None:
        if event.partition not in self.assigned_partitions:
            return
        self.metrics.record_event()
        self.advance_watermark(event.partition, event.event_time)
        if event.event_time < self.global_watermark - self.allowed_lateness:
            self.metrics.record_late_event()
            return
        window_start = event.event_time - (event.event_time % self.window_size)
        key = (event.partition, window_start)
        self.active_windows[key] = self.active_windows.get(key, 0) + event.value
        self._cleanup_expired_windows(now)

    def flush_closed_windows(self) -> None:
        closed: list[tuple[tuple[int, float], int]] = []
        for key, total in self.active_windows.items():
            partition, window_start = key
            if window_start + self.window_size <= self.global_watermark:
                closed.append((key, total))
        for (partition, window_start), total in closed:
            result = WindowResult(
                tenant_id="unknown",
                partition=partition,
                window_start=window_start,
                window_end=window_start + self.window_size,
                total=total,
            )
            self.checkpoint_store.commit(partition, window_start + self.window_size)
            self.metrics.record_checkpoint()
            self.output_sink.emit(result)
            self.metrics.record_window_flush()
            del self.active_windows[(partition, window_start)]

    def on_rebalance(self, new_partitions: set[int]) -> None:
        self.assigned_partitions = set(new_partitions)
        for partition in new_partitions:
            self.partition_watermarks[partition] = self.checkpoint_store.load(partition)

    def _cleanup_expired_windows(self, now: float) -> None:
        expired = [
            key
            for key in self.active_windows
            if self.global_watermark - (key[1] + self.window_size) > self.cleanup_delay
        ]
        for key in expired:
            del self.active_windows[key]
