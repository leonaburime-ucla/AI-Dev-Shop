"""
Tests for Inventory Tracker.

40 tests covering adjustments, bulk operations, transfers, capacity,
aggregation, and history.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from src.inventory_tracker import (
    AdminOverride,
    HistoryEntry,
    StockAdjustment,
    StockLevel,
    TransferRequest,
    Warehouse,
    adjust_stock,
    bulk_adjust,
    get_stock_history,
    get_total_stock,
    transfer_stock,
)

# BUG: Module-level time patching without cleanup -- equivalent of
# jest.useFakeTimers() at module scope with no afterEach/afterAll.
_time_patcher = patch("src.inventory_tracker.datetime")
mock_datetime = _time_patcher.start()
mock_datetime.now.return_value = datetime(2026, 4, 25, 12, 0, 0)
mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)


# --- Test helpers ---

fixed_date = datetime(2026, 4, 25, 12, 0, 0)


class MockClock:
    def now(self) -> datetime:
        return fixed_date


mock_clock = MockClock()


def make_mock_store(**overrides: object) -> AsyncMock:
    store = AsyncMock()
    store.get_stock = AsyncMock(return_value=50)
    store.set_stock = AsyncMock(return_value=None)
    store.get_warehouse = AsyncMock(
        return_value=Warehouse(id="WH-1", name="Main Warehouse", max_capacity=100)
    )
    store.get_all_stock = AsyncMock(
        return_value=[
            StockLevel(warehouse_id="WH-1", product_id="PROD-1", quantity=50),
            StockLevel(warehouse_id="WH-2", product_id="PROD-1", quantity=30),
        ]
    )
    store.add_history = AsyncMock(return_value=None)
    store.get_history = AsyncMock(return_value=[])
    for key, value in overrides.items():
        setattr(store, key, value)
    return store


def make_adjustment(**overrides: object) -> StockAdjustment:
    defaults = {
        "product_id": "PROD-1",
        "warehouse_id": "WH-1",
        "quantity": 10,
        "adjusted_by": "USER-001",
    }
    defaults.update(overrides)
    return StockAdjustment(**defaults)


# --- adjust_stock tests ---


class TestAdjustStock:
    @pytest.mark.asyncio
    async def test_should_increase_stock(self) -> None:
        store = make_mock_store()
        result = await adjust_stock(
            make_adjustment(quantity=10), {"store": store, "clock": mock_clock}
        )
        assert result == 60
        store.set_stock.assert_called_with("WH-1", "PROD-1", 60)

    @pytest.mark.asyncio
    async def test_should_decrease_stock(self) -> None:
        store = make_mock_store()
        result = await adjust_stock(
            make_adjustment(quantity=-10), {"store": store, "clock": mock_clock}
        )
        assert result == 40
        store.set_stock.assert_called_with("WH-1", "PROD-1", 40)

    @pytest.mark.asyncio
    async def test_should_reject_removal_exceeding_available_stock(self) -> None:
        store = make_mock_store(get_stock=AsyncMock(return_value=5))
        with pytest.raises(ValueError, match="Insufficient stock"):
            await adjust_stock(
                make_adjustment(quantity=-10), {"store": store, "clock": mock_clock}
            )

    @pytest.mark.asyncio
    async def test_should_reject_when_capacity_would_be_exceeded(self) -> None:
        store = make_mock_store(get_stock=AsyncMock(return_value=95))
        with pytest.raises(ValueError, match="Capacity exceeded"):
            await adjust_stock(
                make_adjustment(quantity=10), {"store": store, "clock": mock_clock}
            )

    @pytest.mark.asyncio
    async def test_should_allow_adjustment_up_to_just_below_capacity(self) -> None:
        # maxCapacity=100, currentStock=50, adding 49 -> newStock=99 < 100 -> allowed
        store = make_mock_store(get_stock=AsyncMock(return_value=50))
        result = await adjust_stock(
            make_adjustment(quantity=49), {"store": store, "clock": mock_clock}
        )
        assert result == 99

    @pytest.mark.asyncio
    async def test_should_record_history_entry(self) -> None:
        store = make_mock_store()
        await adjust_stock(
            make_adjustment(quantity=10), {"store": store, "clock": mock_clock}
        )
        store.add_history.assert_called_with(
            HistoryEntry(
                timestamp=fixed_date,
                product_id="PROD-1",
                warehouse_id="WH-1",
                quantity_change=10,
                resulting_stock=60,
                adjusted_by="USER-001",
            )
        )

    @pytest.mark.asyncio
    async def test_should_use_default_clock_when_none_provided(self) -> None:
        store = make_mock_store()
        await adjust_stock(make_adjustment(), {"store": store})
        assert store.add_history.called

    @pytest.mark.asyncio
    async def test_should_handle_zero_quantity_adjustment(self) -> None:
        store = make_mock_store()
        result = await adjust_stock(
            make_adjustment(quantity=0), {"store": store, "clock": mock_clock}
        )
        assert result == 50

    @pytest.mark.asyncio
    async def test_should_handle_warehouse_not_found_gracefully(self) -> None:
        store = make_mock_store(get_warehouse=AsyncMock(return_value=None))
        # When warehouse is None, capacity check is skipped
        result = await adjust_stock(
            make_adjustment(quantity=200), {"store": store, "clock": mock_clock}
        )
        assert result == 250


# --- bulk_adjust tests ---


class TestBulkAdjust:
    @pytest.mark.asyncio
    async def test_should_process_all_successful_adjustments(self) -> None:
        store = make_mock_store()
        adjustments = [
            make_adjustment(quantity=10),
            make_adjustment(quantity=20),
        ]

        result = await bulk_adjust(adjustments, {"store": store, "clock": mock_clock})

        assert len(result.succeeded) == 2
        assert len(result.failed) == 0

    @pytest.mark.asyncio
    async def test_should_continue_past_individual_failures(self) -> None:
        store = make_mock_store(
            get_stock=AsyncMock(
                side_effect=[
                    5,   # first: only 5 available
                    50,  # second: 50 available
                    50,  # for warehouse check
                ]
            )
        )
        adjustments = [
            make_adjustment(quantity=-10),  # will fail: insufficient
            make_adjustment(quantity=5),    # will succeed
        ]

        result = await bulk_adjust(adjustments, {"store": store, "clock": mock_clock})

        assert len(result.succeeded) == 1
        assert len(result.failed) == 1
        assert "Insufficient stock" in result.failed[0]["error"]

    @pytest.mark.asyncio
    async def test_should_handle_empty_adjustments_array(self) -> None:
        store = make_mock_store()
        result = await bulk_adjust([], {"store": store, "clock": mock_clock})
        assert len(result.succeeded) == 0
        assert len(result.failed) == 0

    @pytest.mark.asyncio
    async def test_should_handle_all_failures(self) -> None:
        store = make_mock_store(get_stock=AsyncMock(return_value=0))
        adjustments = [
            make_adjustment(quantity=-10),
            make_adjustment(quantity=-20),
        ]

        result = await bulk_adjust(adjustments, {"store": store, "clock": mock_clock})

        assert len(result.succeeded) == 0
        assert len(result.failed) == 2

    @pytest.mark.asyncio
    async def test_should_apply_admin_override_when_provided(self) -> None:
        store = make_mock_store()
        adjustments = [make_adjustment(adjusted_by="USER-001")]

        await bulk_adjust(
            adjustments,
            {"store": store, "clock": mock_clock},
            AdminOverride(admin_id="ADMIN-001", reason="Inventory correction"),
        )

        assert store.set_stock.called

    @pytest.mark.asyncio
    async def test_should_collect_multiple_different_error_types(self) -> None:
        store = make_mock_store(
            get_stock=AsyncMock(
                side_effect=[
                    0,   # insufficient
                    95,  # capacity
                    95,  # for warehouse lookup
                ]
            )
        )
        adjustments = [
            make_adjustment(quantity=-10),  # insufficient stock
            make_adjustment(quantity=10),   # capacity exceeded
        ]

        result = await bulk_adjust(adjustments, {"store": store, "clock": mock_clock})

        assert len(result.failed) == 2


# --- transfer_stock tests ---


class TestTransferStock:
    @pytest.mark.asyncio
    async def test_should_transfer_stock_between_warehouses(self) -> None:
        store = make_mock_store(
            get_stock=AsyncMock(
                side_effect=[
                    50,  # source
                    20,  # destination
                ]
            )
        )

        result = await transfer_stock(
            TransferRequest(
                product_id="PROD-1",
                source_warehouse_id="WH-1",
                destination_warehouse_id="WH-2",
                quantity=10,
                requested_by="USER-001",
            ),
            {"store": store, "clock": mock_clock},
        )

        assert result["source_stock"] == 40
        assert result["destination_stock"] == 30

    @pytest.mark.asyncio
    async def test_should_reject_transfer_when_source_has_insufficient_stock(self) -> None:
        store = make_mock_store(get_stock=AsyncMock(return_value=5))

        with pytest.raises(ValueError, match="Insufficient stock for transfer"):
            await transfer_stock(
                TransferRequest(
                    product_id="PROD-1",
                    source_warehouse_id="WH-1",
                    destination_warehouse_id="WH-2",
                    quantity=10,
                    requested_by="USER-001",
                ),
                {"store": store, "clock": mock_clock},
            )

    @pytest.mark.asyncio
    async def test_should_record_history_for_both_source_and_destination(self) -> None:
        store = make_mock_store(
            get_stock=AsyncMock(side_effect=[50, 20])
        )

        await transfer_stock(
            TransferRequest(
                product_id="PROD-1",
                source_warehouse_id="WH-1",
                destination_warehouse_id="WH-2",
                quantity=10,
                requested_by="USER-001",
            ),
            {"store": store, "clock": mock_clock},
        )

        assert store.add_history.call_count == 2
        # Check source history
        source_call = store.add_history.call_args_list[0][0][0]
        assert source_call.warehouse_id == "WH-1"
        assert source_call.quantity_change == -10
        assert source_call.resulting_stock == 40
        # Check destination history
        dest_call = store.add_history.call_args_list[1][0][0]
        assert dest_call.warehouse_id == "WH-2"
        assert dest_call.quantity_change == 10
        assert dest_call.resulting_stock == 30

    @pytest.mark.asyncio
    async def test_should_use_same_timestamp_for_both_history_entries(self) -> None:
        store = make_mock_store(
            get_stock=AsyncMock(side_effect=[50, 20])
        )

        await transfer_stock(
            TransferRequest(
                product_id="PROD-1",
                source_warehouse_id="WH-1",
                destination_warehouse_id="WH-2",
                quantity=10,
                requested_by="USER-001",
            ),
            {"store": store, "clock": mock_clock},
        )

        source_call = store.add_history.call_args_list[0][0][0]
        dest_call = store.add_history.call_args_list[1][0][0]
        assert source_call.timestamp is dest_call.timestamp


# --- get_total_stock tests ---


class TestGetTotalStock:
    @pytest.mark.asyncio
    async def test_should_sum_stock_across_all_warehouses(self) -> None:
        store = make_mock_store()
        total = await get_total_stock("PROD-1", {"store": store})
        assert total == 80  # 50 + 30 from mock

    @pytest.mark.asyncio
    async def test_should_return_0_when_no_stock_exists(self) -> None:
        store = make_mock_store(get_all_stock=AsyncMock(return_value=[]))
        total = await get_total_stock("PROD-1", {"store": store})
        assert total == 0

    @pytest.mark.asyncio
    async def test_should_handle_single_warehouse(self) -> None:
        store = make_mock_store(
            get_all_stock=AsyncMock(
                return_value=[
                    StockLevel(warehouse_id="WH-1", product_id="PROD-1", quantity=42)
                ]
            )
        )
        total = await get_total_stock("PROD-1", {"store": store})
        assert total == 42

    @pytest.mark.asyncio
    async def test_should_handle_many_warehouses(self) -> None:
        levels = [
            StockLevel(warehouse_id=f"WH-{i}", product_id="PROD-1", quantity=10)
            for i in range(20)
        ]
        store = make_mock_store(get_all_stock=AsyncMock(return_value=levels))
        total = await get_total_stock("PROD-1", {"store": store})
        assert total == 200


# --- get_stock_history tests ---


class TestGetStockHistory:
    @pytest.mark.asyncio
    async def test_should_return_history_for_a_product(self) -> None:
        history: list[HistoryEntry] = [
            HistoryEntry(
                timestamp=fixed_date,
                product_id="PROD-1",
                warehouse_id="WH-1",
                quantity_change=10,
                resulting_stock=60,
                adjusted_by="USER-001",
            ),
        ]
        store = make_mock_store(get_history=AsyncMock(return_value=history))

        result = await get_stock_history("PROD-1", {"store": store})
        assert len(result) == 1
        assert result[0].quantity_change == 10

    @pytest.mark.asyncio
    async def test_should_filter_by_warehouse_when_specified(self) -> None:
        store = make_mock_store()
        await get_stock_history("PROD-1", {"store": store}, "WH-1")
        store.get_history.assert_called_with("PROD-1", "WH-1")

    @pytest.mark.asyncio
    async def test_should_return_empty_list_when_no_history(self) -> None:
        store = make_mock_store()
        result = await get_stock_history("PROD-1", {"store": store})
        assert len(result) == 0


# --- Edge case tests ---


class TestEdgeCases:
    @pytest.mark.asyncio
    async def test_should_handle_concurrent_adjustments_to_same_product(self) -> None:
        import asyncio

        store = make_mock_store()
        adj1 = make_adjustment(quantity=10)
        adj2 = make_adjustment(quantity=20)

        r1, r2 = await asyncio.gather(
            adjust_stock(adj1, {"store": store, "clock": mock_clock}),
            adjust_stock(adj2, {"store": store, "clock": mock_clock}),
        )

        # Both read current_stock=50, so both compute independently
        assert r1 == 60
        assert r2 == 70
        # Both read current_stock=50, so both compute independently

    @pytest.mark.asyncio
    async def test_should_handle_adjustment_of_zero_quantity(self) -> None:
        store = make_mock_store()
        result = await adjust_stock(
            make_adjustment(quantity=0), {"store": store, "clock": mock_clock}
        )
        assert result == 50

    @pytest.mark.asyncio
    async def test_should_handle_transfer_of_entire_stock(self) -> None:
        store = make_mock_store(
            get_stock=AsyncMock(
                side_effect=[
                    50,  # source has exactly 50
                    0,   # destination is empty
                ]
            )
        )

        result = await transfer_stock(
            TransferRequest(
                product_id="PROD-1",
                source_warehouse_id="WH-1",
                destination_warehouse_id="WH-2",
                quantity=50,
                requested_by="USER-001",
            ),
            {"store": store, "clock": mock_clock},
        )

        assert result["source_stock"] == 0
        assert result["destination_stock"] == 50

    @pytest.mark.asyncio
    async def test_should_handle_large_bulk_adjustment(self) -> None:
        store = make_mock_store()
        adjustments = [
            make_adjustment(quantity=1, product_id=f"PROD-{i}") for i in range(100)
        ]

        result = await bulk_adjust(adjustments, {"store": store, "clock": mock_clock})
        assert len(result.succeeded) == 100
