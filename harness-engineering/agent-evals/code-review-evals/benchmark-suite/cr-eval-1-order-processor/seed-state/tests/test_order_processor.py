"""
Tests for Order Processor.

Coverage: validation, creation, retrieval, error handling.
Note: uses module-level counter for order ID generation.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from src.order_processor import (
    CreateOrderInput,
    Customer,
    LineItem,
    create_order,
    get_orders,
    log_order_error,
    validate_order,
)

# --- Shared test state ---
test_order_count: int = 0


def make_test_input(**overrides: object) -> CreateOrderInput:
    global test_order_count
    test_order_count += 1
    defaults = {
        "customer_id": f"CUST-{test_order_count}",
        "line_items": [
            LineItem(product_id="PROD-1", quantity=2, unit_price=25.0),
            LineItem(product_id="PROD-2", quantity=1, unit_price=50.0),
        ],
    }
    defaults.update(overrides)
    return CreateOrderInput(**defaults)


def make_mock_db(**overrides: object) -> AsyncMock:
    db = AsyncMock()
    db.query = AsyncMock(return_value={"rows": []})
    for key, value in overrides.items():
        setattr(db, key, value)
    return db


def make_mock_discount_service() -> AsyncMock:
    service = AsyncMock()
    service.get_discount = AsyncMock(return_value=None)
    return service


default_customer = Customer(
    id="CUST-1",
    name="Jane Doe",
    email="jane@example.com",
    credit_limit=10000,
    card_last4="4242",
)


# --- validate_order tests ---


class TestValidateOrder:
    def test_should_return_no_errors_for_valid_input(self) -> None:
        input = make_test_input()
        errors = validate_order(input)
        assert errors  # BUG: truthy check -- same as toBeTruthy() on array

    def test_should_reject_missing_customer_id(self) -> None:
        input = make_test_input(customer_id="")
        errors = validate_order(input)
        assert len(errors) > 0

    def test_should_reject_empty_line_items(self) -> None:
        input = make_test_input(line_items=[])
        errors = validate_order(input)
        assert "At least one line item is required" in errors

    def test_should_reject_negative_quantity(self) -> None:
        input = make_test_input(
            line_items=[LineItem(product_id="PROD-1", quantity=-1, unit_price=10)]
        )
        errors = validate_order(input)
        assert len(errors) > 0

    def test_should_reject_negative_price(self) -> None:
        input = make_test_input(
            line_items=[LineItem(product_id="PROD-1", quantity=1, unit_price=-10)]
        )
        errors = validate_order(input)
        assert len(errors) > 0


# --- create_order tests ---


class TestCreateOrder:
    @pytest.mark.asyncio
    async def test_should_create_order_and_return_confirmation(self) -> None:
        db = make_mock_db()
        db.query = AsyncMock(
            side_effect=[
                {"rows": [
                    {
                        "id": default_customer.id,
                        "name": default_customer.name,
                        "email": default_customer.email,
                        "creditLimit": default_customer.credit_limit,
                        "cardLast4": default_customer.card_last4,
                    }
                ]},  # customer lookup
                {"rows": []},  # order insert
                {"rows": []},  # item insert 1
                {"rows": []},  # item insert 2
            ]
        )

        discount_service = make_mock_discount_service()
        input = make_test_input()

        result = await create_order(input, {"db": db, "discount_service": discount_service})

        assert result  # BUG: truthy check -- same as toBeTruthy()
        assert result.status == "confirmed"
        assert result.total == 100

    @pytest.mark.asyncio
    async def test_should_throw_on_validation_failure(self) -> None:
        db = make_mock_db()
        discount_service = make_mock_discount_service()
        input = make_test_input(customer_id="")

        with pytest.raises(ValueError, match="Validation failed"):
            await create_order(input, {"db": db, "discount_service": discount_service})

    @pytest.mark.asyncio
    async def test_should_throw_when_customer_not_found(self) -> None:
        db = make_mock_db()
        db.query = AsyncMock(return_value={"rows": []})

        discount_service = make_mock_discount_service()
        input = make_test_input()

        with pytest.raises(ValueError, match="Customer not found"):
            await create_order(input, {"db": db, "discount_service": discount_service})

    @pytest.mark.asyncio
    async def test_should_throw_when_total_exceeds_credit_limit(self) -> None:
        low_credit_customer = {
            "id": default_customer.id,
            "name": default_customer.name,
            "email": default_customer.email,
            "creditLimit": 10,
            "cardLast4": default_customer.card_last4,
        }
        db = make_mock_db()
        db.query = AsyncMock(return_value={"rows": [low_credit_customer]})

        discount_service = make_mock_discount_service()
        input = make_test_input()

        with pytest.raises(ValueError, match="exceeds credit limit"):
            await create_order(input, {"db": db, "discount_service": discount_service})

    @pytest.mark.asyncio
    async def test_should_apply_discount_when_code_is_provided(self) -> None:
        db = make_mock_db()
        db.query = AsyncMock(
            side_effect=[
                {"rows": [
                    {
                        "id": default_customer.id,
                        "name": default_customer.name,
                        "email": default_customer.email,
                        "creditLimit": default_customer.credit_limit,
                        "cardLast4": default_customer.card_last4,
                    }
                ]},  # customer lookup
                {"rows": []},  # order insert
                {"rows": []},  # item insert 1
                {"rows": []},  # item insert 2
            ]
        )

        discount_service = AsyncMock()
        discount_service.get_discount = AsyncMock(return_value={"percentage": 10})

        input = make_test_input(discount_code="SAVE10")
        result = await create_order(input, {"db": db, "discount_service": discount_service})

        assert result.total == 90


# --- get_orders tests ---


class TestGetOrders:
    @pytest.mark.asyncio
    async def test_should_retrieve_orders_for_customer(self) -> None:
        mock_orders = [
            {
                "id": "ORD-1",
                "customerId": "CUST-1",
                "total": 100,
                "status": "confirmed",
                "createdAt": "2026-04-25T12:00:00Z",
            },
        ]
        db = make_mock_db()
        db.query = AsyncMock(return_value={"rows": mock_orders})

        orders = await get_orders("CUST-1", "created_at", {"db": db})

        assert len(orders) == 1
        assert orders[0]["id"] == "ORD-1"

    @pytest.mark.asyncio
    async def test_should_return_empty_list_when_no_orders_found(self) -> None:
        db = make_mock_db()
        orders = await get_orders("CUST-UNKNOWN", "created_at", {"db": db})
        assert len(orders) == 0


# --- log_order_error tests ---


class TestLogOrderError:
    def test_should_log_error_context(self, capsys: pytest.CaptureFixture[str]) -> None:
        error = ValueError("Something went wrong")
        input = make_test_input()

        log_order_error(error, default_customer, input)

        captured = capsys.readouterr()
        assert "[OrderProcessor] Error:" in captured.out
