from __future__ import annotations

import pytest

from src.retry_queue import (
    BackpressureMonitor,
    DeliveryReceipt,
    IdempotencyStore,
    IdempotentReceiptCache,
    Message,
    QueueConsumer,
    RetryPolicy,
    TransientPartnerError,
)


def receipt(message: Message) -> DeliveryReceipt:
    return DeliveryReceipt(receipt_id=f"rcpt-{message.message_id}", status="sent")


def test_successful_delivery_is_deduped_within_window() -> None:
    consumer = QueueConsumer(receipt, idempotency=IdempotencyStore(window_seconds=120))
    consumer.claim_partitions({0})
    message = Message(
        message_id="m-1",
        tenant_id="tenant-a",
        partition=0,
        payload={"kind": "charge"},
        idempotency_key="tenant-a:charge-1",
    )

    first = consumer.process_batch([message], now=10)
    second = consumer.process_batch([message], now=20)

    assert first == second
    assert consumer.checkpoints[0] == "m-1"


def test_transient_failure_schedules_retry() -> None:
    def failing_handler(message: Message) -> DeliveryReceipt:
        raise TransientPartnerError("partner unavailable")

    consumer = QueueConsumer(
        failing_handler,
        retry_policy=RetryPolicy(max_attempts=3, base_delay_seconds=2),
    )
    consumer.claim_partitions({0})

    consumer.process_batch(
        [
            Message(
                message_id="m-2",
                tenant_id="tenant-a",
                partition=0,
                payload={"kind": "email"},
                idempotency_key="tenant-a:email-1",
            )
        ],
        now=100,
    )

    assert len(consumer.retry_queue) == 1
    assert consumer.retry_queue[0].attempt_count == 1
    assert consumer.retry_queue[0].not_before == 102


def test_max_attempts_goes_to_dead_letter_sink() -> None:
    def failing_handler(message: Message) -> DeliveryReceipt:
        raise TransientPartnerError("still unavailable")

    consumer = QueueConsumer(failing_handler, retry_policy=RetryPolicy(max_attempts=2))
    consumer.claim_partitions({0})
    message = Message(
        message_id="m-3",
        tenant_id="tenant-a",
        partition=0,
        payload={"kind": "invoice"},
        idempotency_key="tenant-a:invoice-1",
        attempt_count=1,
    )

    consumer.process_batch([message], now=200)

    assert consumer.dlq.messages[0][0] == message


def test_backpressure_monitor_signals_pause() -> None:
    monitor = BackpressureMonitor(max_inflight=2, max_retry_queue=5)

    assert not monitor.should_pause_fetch(inflight=1, retry_depth=0)
    assert monitor.should_pause_fetch(inflight=2, retry_depth=0)
    assert monitor.should_pause_fetch(inflight=1, retry_depth=5)


def test_idempotent_receipt_cache_returns_prior() -> None:
    cache = IdempotentReceiptCache()
    calls = 0

    def factory() -> DeliveryReceipt:
        nonlocal calls
        calls += 1
        return DeliveryReceipt(receipt_id=f"rcpt-{calls}", status="sent")

    first = cache.complete_once("tenant-a:message-1", factory)
    second = cache.complete_once("tenant-a:message-1", factory)

    assert first == second
    assert calls == 1


def test_unassigned_partition_is_ignored() -> None:
    consumer = QueueConsumer(receipt)
    consumer.claim_partitions({1})
    message = Message(
        message_id="m-4",
        tenant_id="tenant-a",
        partition=0,
        payload={"kind": "shipment"},
        idempotency_key="tenant-a:shipment-1",
    )

    assert consumer.process_batch([message], now=300) == []
    assert consumer.checkpoints == {}
