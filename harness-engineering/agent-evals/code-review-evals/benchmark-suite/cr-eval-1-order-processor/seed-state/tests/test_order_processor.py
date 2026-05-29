from __future__ import annotations

from src.order_processor import (
    IdempotentReceiptStore,
    InventoryGateway,
    OrderSaga,
    OrderState,
    OrderStore,
    PaymentGateway,
    PaymentReceipt,
    PromotionLedger,
)


def make_saga() -> OrderSaga:
    return OrderSaga(
        OrderStore(),
        PaymentGateway(),
        InventoryGateway(),
        PromotionLedger(),
    )


def test_place_order_confirms_payment_and_reservation() -> None:
    saga = make_saga()

    order = saga.place_order(
        "tenant-a",
        "cust-1",
        "sku-1",
        2,
        5000,
        "idem-1",
        now=100,
    )

    assert order.state == OrderState.CONFIRMED
    assert order.payment_intent_id == "pi_1"
    assert saga.store.get("tenant-a", order.order_id) == order


def test_cancel_order_refunds_and_releases_inventory() -> None:
    saga = make_saga()
    order = saga.place_order("tenant-a", "cust-1", "sku-1", 1, 1000, "idem-1", now=100)

    canceled = saga.cancel_order("tenant-a", order.order_id)

    assert canceled.state == OrderState.REFUNDED
    assert saga.payments.refunds == [order.payment_intent_id]
    assert saga.inventory.released == [order.reservation_id]


def test_gateway_refund_event_sets_refunded_state() -> None:
    saga = make_saga()
    order = saga.place_order("tenant-a", "cust-1", "sku-1", 1, 1000, "idem-1", now=100)

    updated = saga.apply_gateway_event("tenant-a", order.order_id, "payment_refunded")

    assert updated.state == OrderState.REFUNDED


def test_admin_lookup_finds_existing_order() -> None:
    saga = make_saga()
    order = saga.place_order("tenant-a", "cust-1", "sku-1", 1, 1000, "idem-1", now=100)

    assert saga.store.lookup_order_admin(order.order_id) == order


def test_idempotent_receipt_store_returns_prior() -> None:
    store = IdempotentReceiptStore()
    calls = 0

    def capture() -> PaymentReceipt:
        nonlocal calls
        calls += 1
        return PaymentReceipt(payment_intent_id=f"pi_{calls}", amount_cents=1000)

    first = store.complete_once("idem-1", capture)
    second = store.complete_once("idem-1", capture)

    assert first == second
    assert calls == 1
