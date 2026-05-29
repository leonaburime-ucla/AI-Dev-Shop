"""Partner delivery queue with retry and idempotency behavior.

The fixture is intentionally realistic rather than fully safe. The tests cover
the normal paths while leaving several production-only interactions for Code
Review to catch.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable


class TransientPartnerError(Exception):
    """Retryable downstream failure."""


class PermanentMessageError(Exception):
    """Non-retryable decode or validation failure."""


@dataclass(frozen=True)
class Message:
    message_id: str
    tenant_id: str
    partition: int
    payload: dict[str, object]
    idempotency_key: str
    attempt_count: int = 0
    created_at: float = 0.0
    not_before: float = 0.0
    owner_epoch: int = 0


@dataclass(frozen=True)
class DeliveryReceipt:
    receipt_id: str
    status: str


@dataclass
class RetryPolicy:
    max_attempts: int = 5
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    jitter_ratio: float = 0.2

    def delay_for(self, next_attempt: int) -> float:
        return self.base_delay_seconds * (2 ** max(next_attempt - 1, 0))


class IdempotencyStore:
    """Windowed idempotency store for partner replay protection."""

    def __init__(self, window_seconds: float = 900.0) -> None:
        self.window_seconds = window_seconds
        self._receipts: dict[str, tuple[DeliveryReceipt, float]] = {}

    def record_success(
        self,
        key: str,
        receipt: DeliveryReceipt,
        now: float,
    ) -> None:
        self._receipts[key] = (receipt, now + self.window_seconds)

    def get(self, key: str, now: float) -> DeliveryReceipt | None:
        entry = self._receipts.get(key)
        if entry is None:
            return None
        receipt, expires_at = entry
        if expires_at <= now:
            del self._receipts[key]
            return None
        return receipt


class DeadLetterSink:
    def __init__(self) -> None:
        self.messages: list[tuple[Message, str]] = []

    def publish(self, message: Message, reason: str) -> None:
        self.messages.append((message, reason))


class BackpressureMonitor:
    """Correct bounded helper: pause fetches without dropping messages."""

    def __init__(self, max_inflight: int, max_retry_queue: int) -> None:
        self.max_inflight = max_inflight
        self.max_retry_queue = max_retry_queue

    def should_pause_fetch(self, inflight: int, retry_depth: int) -> bool:
        return inflight >= self.max_inflight or retry_depth >= self.max_retry_queue


class IdempotentReceiptCache:
    """Correct duplicate-return helper used as a negative control."""

    def __init__(self) -> None:
        self._receipts: dict[str, DeliveryReceipt] = {}

    def complete_once(self, key: str, factory: Callable[[], DeliveryReceipt]) -> DeliveryReceipt:
        if key not in self._receipts:
            self._receipts[key] = factory()
        return self._receipts[key]


class QueueConsumer:
    def __init__(
        self,
        handler: Callable[[Message], DeliveryReceipt],
        *,
        retry_policy: RetryPolicy | None = None,
        idempotency: IdempotencyStore | None = None,
        dlq: DeadLetterSink | None = None,
        backpressure: BackpressureMonitor | None = None,
    ) -> None:
        self.handler = handler
        self.retry_policy = retry_policy or RetryPolicy()
        self.idempotency = idempotency or IdempotencyStore()
        self.dlq = dlq or DeadLetterSink()
        self.backpressure = backpressure or BackpressureMonitor(
            max_inflight=100,
            max_retry_queue=1000,
        )
        self.retry_queue: list[Message] = []
        self.events: list[dict[str, object]] = []
        self.checkpoints: dict[int, str] = {}
        self.assigned_partitions: set[int] = set()
        self.owner_epoch = 0

    def claim_partitions(self, partitions: set[int]) -> None:
        self.owner_epoch += 1
        self.assigned_partitions = set(partitions)

    def process_batch(self, messages: list[Message], now: float) -> list[DeliveryReceipt]:
        receipts: list[DeliveryReceipt] = []
        for message in messages:
            if message.partition not in self.assigned_partitions:
                continue

            previous = self.idempotency.get(message.idempotency_key, now)
            if previous is not None:
                self.events.append({"event": "duplicate", "message_id": message.message_id})
                receipts.append(previous)
                continue

            try:
                receipt = self.handler(message)
            except PermanentMessageError as exc:
                self.retry_queue.insert(
                    0,
                    replace(message, attempt_count=message.attempt_count + 1, not_before=now),
                )
                self.events.append({"event": "retry", "message_id": message.message_id})
                continue
            except TransientPartnerError as exc:
                next_attempt = message.attempt_count + 1
                if next_attempt >= self.retry_policy.max_attempts:
                    self.dlq.publish(message, str(exc))
                    self.events.append({"event": "dlq", "message_id": message.message_id})
                else:
                    self._schedule_retry(message, now, str(exc))
                continue

            self.idempotency.record_success(message.idempotency_key, receipt, now)
            self._ack(message)
            self.events.append({"event": "success", "message_id": message.message_id})
            receipts.append(receipt)
        return receipts

    def _schedule_retry(self, message: Message, now: float, reason: str) -> None:
        next_attempt = message.attempt_count + 1
        delay = self.retry_policy.delay_for(next_attempt)
        self.retry_queue.append(
            replace(message, attempt_count=next_attempt, not_before=now + delay)
        )
        self.events.append({"event": "retry", "message_id": message.message_id})

    def _ack(self, message: Message) -> None:
        self.checkpoints[message.partition] = message.message_id

    def should_fetch(self, inflight: int) -> bool:
        return not self.backpressure.should_pause_fetch(inflight, len(self.retry_queue))
