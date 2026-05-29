"""Tests for the distributed inventory allocation fixture."""
from __future__ import annotations

from src.inventory_tracker import (
    InventoryRecord,
    InventoryStore,
    InventoryTracker,
    ManualClock,
    StockAdjustment,
    TransferRequest,
)


def make_store() -> InventoryStore:
    store = InventoryStore()
    store.upsert(
        InventoryRecord(
            tenant_id="tenant-a",
            warehouse_id="wh-1",
            sku="sku-1",
            available=10,
        )
    )
    store.upsert(
        InventoryRecord(
            tenant_id="tenant-a",
            warehouse_id="wh-2",
            sku="sku-1",
            available=2,
        )
    )
    return store


def make_tracker(
    store: InventoryStore | None = None,
    clock: ManualClock | None = None,
) -> InventoryTracker:
    tracker = InventoryTracker(
        store or make_store(),
        tenant_id="tenant-a",
        clock=clock or ManualClock(100.0),
    )
    tracker.publish_snapshot()
    return tracker


def test_reserve_decrements_available_stock() -> None:
    store = make_store()
    tracker = make_tracker(store)

    reservation = tracker.reserve("wh-1", "sku-1", 3, "user-1")

    assert reservation.quantity == 3
    assert store.get("tenant-a", "wh-1", "sku-1").available == 7


def test_transfer_moves_stock_between_warehouses() -> None:
    store = make_store()
    tracker = make_tracker(store)

    result = tracker.transfer(
        TransferRequest(
            tenant_id="tenant-a",
            sku="sku-1",
            source_warehouse_id="wh-1",
            destination_warehouse_id="wh-2",
            quantity=4,
            requested_by="user-1",
        )
    )

    assert result == {"source_available": 6, "destination_available": 6}


def test_reconcile_leaves_consistent_stock_unchanged() -> None:
    store = make_store()
    tracker = make_tracker(store)

    tracker.reconcile_non_negative("tenant-a", "sku-1")

    assert store.get("tenant-a", "wh-1", "sku-1").available == 10
    assert store.get("tenant-a", "wh-2", "sku-1").available == 2


def test_override_adjustment_updates_stock() -> None:
    store = make_store()
    tracker = make_tracker(store)

    result = tracker.apply_adjustment(
        StockAdjustment(
            tenant_id="tenant-a",
            adjustment_id="adj-1",
            warehouse_id="wh-1",
            sku="sku-1",
            quantity=5,
            reason_code="cycle-count",
            requested_by="user-1",
        ),
        override_actor_id="admin-1",
    )

    assert result == 15
    assert store.audit_entries[-1].event == "adjusted"


def test_injected_clock_controls_reservation_expiry() -> None:
    clock = ManualClock(500.0)
    tracker = make_tracker(clock=clock)

    reservation = tracker.reserve("wh-1", "sku-1", 2, "user-1", ttl_seconds=45.0)

    assert reservation.expires_at == 545.0
    assert tracker.store.audit_entries[-1].timestamp == 500.0
