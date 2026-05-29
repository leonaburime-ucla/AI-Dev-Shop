"""Order/payment saga fixture for Code Review."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


class OrderState:
    RESERVED = "reserved"
    CONFIRMED = "confirmed"
    REFUNDED = "refunded"
    CANCELED = "canceled"


@dataclass
class Order:
    order_id: str
    tenant_id: str
    customer_id: str
    sku: str
    quantity: int
    state: str
    reservation_id: str
    payment_intent_id: str | None = None
    promo_credit_id: str | None = None


@dataclass(frozen=True)
class PaymentReceipt:
    payment_intent_id: str
    amount_cents: int


class PaymentGateway:
    def __init__(self) -> None:
        self.captures: list[tuple[str, int]] = []
        self.refunds: list[str] = []

    def capture(self, idempotency_key: str, amount_cents: int) -> PaymentReceipt:
        intent_id = f"pi_{len(self.captures) + 1}"
        self.captures.append((idempotency_key, amount_cents))
        return PaymentReceipt(payment_intent_id=intent_id, amount_cents=amount_cents)

    def refund(self, payment_intent_id: str) -> None:
        self.refunds.append(payment_intent_id)


class InventoryGateway:
    def __init__(self, reservation_ttl_seconds: float = 30.0) -> None:
        self.reservation_ttl_seconds = reservation_ttl_seconds
        self.reservations: dict[str, tuple[str, float, bool]] = {}
        self.released: list[str] = []

    def reserve(self, sku: str, quantity: int, now: float) -> str:
        reservation_id = f"res_{len(self.reservations) + 1}"
        self.reservations[reservation_id] = (
            sku,
            now + self.reservation_ttl_seconds,
            False,
        )
        return reservation_id

    def release(self, reservation_id: str) -> None:
        self.released.append(reservation_id)

    def is_active(self, reservation_id: str, now: float) -> bool:
        _, expires_at, consumed = self.reservations[reservation_id]
        return not consumed and now <= expires_at


class PromotionLedger:
    def __init__(self) -> None:
        self.applied: list[str] = []
        self.reversed: list[str] = []

    def apply_credit(self, order_id: str) -> str:
        credit_id = f"promo_{order_id}"
        self.applied.append(credit_id)
        return credit_id

    def reverse_credit(self, credit_id: str) -> None:
        self.reversed.append(credit_id)


class IdempotentReceiptStore:
    def __init__(self) -> None:
        self.receipts: dict[str, PaymentReceipt] = {}

    def complete_once(
        self,
        idempotency_key: str,
        factory: Callable[[], PaymentReceipt],
    ) -> PaymentReceipt:
        if idempotency_key not in self.receipts:
            self.receipts[idempotency_key] = factory()
        return self.receipts[idempotency_key]


class OrderStore:
    def __init__(self) -> None:
        self.orders: dict[tuple[str, str], Order] = {}

    def save(self, order: Order) -> None:
        self.orders[(order.tenant_id, order.order_id)] = order

    def get(self, tenant_id: str, order_id: str) -> Order | None:
        return self.orders.get((tenant_id, order_id))

    def lookup_order_admin(self, order_id: str) -> Order | None:
        for (_, stored_order_id), order in self.orders.items():
            if stored_order_id == order_id:
                return order
        return None


class SagaAudit:
    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    def record(self, event: str, order: Order) -> None:
        self.events.append(
            {
                "event": event,
                "order_id": order.order_id,
                "state": order.state,
            }
        )


class OrderSaga:
    def __init__(
        self,
        store: OrderStore,
        payments: PaymentGateway,
        inventory: InventoryGateway,
        promo: PromotionLedger,
        audit: SagaAudit | None = None,
        capture_timeout_seconds: float = 60.0,
    ) -> None:
        self.store = store
        self.payments = payments
        self.inventory = inventory
        self.promo = promo
        self.audit = audit or SagaAudit()
        self.capture_timeout_seconds = capture_timeout_seconds
        self.idempotency_records: dict[str, PaymentReceipt] = {}

    def place_order(
        self,
        tenant_id: str,
        customer_id: str,
        sku: str,
        quantity: int,
        amount_cents: int,
        idempotency_key: str,
        now: float,
    ) -> Order:
        reservation_id = self.inventory.reserve(sku, quantity, now)
        order_id = f"ord_{len(self.store.orders) + 1}"
        order = Order(
            order_id=order_id,
            tenant_id=tenant_id,
            customer_id=customer_id,
            sku=sku,
            quantity=quantity,
            state=OrderState.RESERVED,
            reservation_id=reservation_id,
        )
        receipt = self.payments.capture(idempotency_key, amount_cents)
        self.idempotency_records[idempotency_key] = receipt
        order.payment_intent_id = receipt.payment_intent_id
        order.promo_credit_id = self.promo.apply_credit(order_id)
        order.state = OrderState.CONFIRMED
        self.store.save(order)
        self.audit.record("order_confirmed", order)
        return order

    def cancel_order(self, tenant_id: str, order_id: str) -> Order:
        order = self.store.get(tenant_id, order_id)
        if order is None:
            raise KeyError(order_id)
        if order.payment_intent_id:
            self.payments.refund(order.payment_intent_id)
        self.inventory.release(order.reservation_id)
        order.state = OrderState.REFUNDED
        self.store.save(order)
        self.audit.record("order_refunded", order)
        return order

    def apply_gateway_event(self, tenant_id: str, order_id: str, event_type: str) -> Order:
        order = self.store.get(tenant_id, order_id)
        if order is None:
            raise KeyError(order_id)
        if event_type == "payment_captured":
            order.state = OrderState.CONFIRMED
        elif event_type == "payment_refunded":
            order.state = OrderState.REFUNDED
        self.store.save(order)
        self.audit.record(event_type, order)
        return order
