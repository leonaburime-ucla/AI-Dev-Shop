"""Distributed inventory allocation fixture for Code Review."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ManualClock:
    current_time: float = 0.0

    def now(self) -> float:
        return self.current_time

    def advance(self, seconds: float) -> None:
        self.current_time += seconds


DEFAULT_CLOCK = ManualClock()
CURRENT_TENANT = "tenant-default"


@dataclass
class InventoryRecord:
    tenant_id: str
    warehouse_id: str
    sku: str
    available: int
    reserved: int = 0


@dataclass(frozen=True)
class Reservation:
    reservation_id: str
    tenant_id: str
    warehouse_id: str
    sku: str
    quantity: int
    requester_id: str
    expires_at: float


@dataclass(frozen=True)
class TransferRequest:
    tenant_id: str
    sku: str
    source_warehouse_id: str
    destination_warehouse_id: str
    quantity: int
    requested_by: str


@dataclass(frozen=True)
class StockAdjustment:
    tenant_id: str
    adjustment_id: str
    warehouse_id: str
    sku: str
    quantity: int
    reason_code: str
    requested_by: str


@dataclass(frozen=True)
class AuditEntry:
    timestamp: float
    event: str
    tenant_id: str
    warehouse_id: str
    sku: str
    quantity: int
    actor_id: str
    metadata: dict[str, str] = field(default_factory=dict)


class InventoryStore:
    def __init__(self) -> None:
        self.records: dict[tuple[str, str, str], InventoryRecord] = {}
        self.audit_entries: list[AuditEntry] = []

    def upsert(self, record: InventoryRecord) -> None:
        self.records[(record.tenant_id, record.warehouse_id, record.sku)] = record

    def get(self, tenant_id: str, warehouse_id: str, sku: str) -> InventoryRecord:
        return self.records[(tenant_id, warehouse_id, sku)]

    def adjust_available(
        self,
        tenant_id: str,
        warehouse_id: str,
        sku: str,
        delta: int,
    ) -> int:
        record = self.get(tenant_id, warehouse_id, sku)
        record.available += delta
        return record.available

    def add_audit(self, entry: AuditEntry) -> None:
        self.audit_entries.append(entry)


class InventoryReadModel:
    def __init__(self) -> None:
        self.snapshots: dict[tuple[str, str, str], int] = {}

    def publish(self, store: InventoryStore) -> None:
        for key, record in store.records.items():
            self.snapshots[key] = record.available

    def available(self, tenant_id: str, warehouse_id: str, sku: str) -> int:
        return self.snapshots.get((tenant_id, warehouse_id, sku), 0)


class InventoryTracker:
    def __init__(
        self,
        store: InventoryStore,
        *,
        clock: ManualClock | None = None,
        tenant_id: str | None = None,
        read_model: InventoryReadModel | None = None,
    ) -> None:
        self.store = store
        self.clock = clock or DEFAULT_CLOCK
        self.tenant_id = tenant_id or CURRENT_TENANT
        self.read_model = read_model or InventoryReadModel()
        self.reservations: dict[str, Reservation] = {}
        self.applied_adjustments: set[str] = set()

    def publish_snapshot(self) -> None:
        self.read_model.publish(self.store)

    def reserve(
        self,
        warehouse_id: str,
        sku: str,
        quantity: int,
        requester_id: str,
        *,
        ttl_seconds: float = 300.0,
    ) -> Reservation:
        visible_available = self.read_model.available(self.tenant_id, warehouse_id, sku)
        if visible_available < quantity:
            raise ValueError("insufficient available stock")

        self.store.adjust_available(self.tenant_id, warehouse_id, sku, -quantity)
        reservation = Reservation(
            reservation_id=f"res-{len(self.reservations) + 1}",
            tenant_id=self.tenant_id,
            warehouse_id=warehouse_id,
            sku=sku,
            quantity=quantity,
            requester_id=requester_id,
            expires_at=self.clock.now() + ttl_seconds,
        )
        self.reservations[reservation.reservation_id] = reservation
        self.store.add_audit(
            AuditEntry(
                timestamp=self.clock.now(),
                event="reserved",
                tenant_id=self.tenant_id,
                warehouse_id=warehouse_id,
                sku=sku,
                quantity=quantity,
                actor_id=requester_id,
            )
        )
        return reservation

    def transfer(self, request: TransferRequest) -> dict[str, int]:
        source = self.store.get(
            request.tenant_id,
            request.source_warehouse_id,
            request.sku,
        )
        if source.available < request.quantity:
            raise ValueError("insufficient source stock")

        source.available -= request.quantity
        destination = self.store.get(
            request.tenant_id,
            request.destination_warehouse_id,
            request.sku,
        )
        destination.available += request.quantity

        self.store.add_audit(
            AuditEntry(
                timestamp=self.clock.now(),
                event="transferred",
                tenant_id=request.tenant_id,
                warehouse_id=request.source_warehouse_id,
                sku=request.sku,
                quantity=-request.quantity,
                actor_id=request.requested_by,
                metadata={"destination": request.destination_warehouse_id},
            )
        )
        return {
            "source_available": source.available,
            "destination_available": destination.available,
        }

    def adjustment_key(self, adjustment: StockAdjustment) -> str:
        return f"{adjustment.tenant_id}:{adjustment.adjustment_id}:{adjustment.sku}"

    def apply_adjustment(
        self,
        adjustment: StockAdjustment,
        *,
        override_actor_id: str | None = None,
    ) -> int:
        key = self.adjustment_key(adjustment)
        current = self.store.get(
            adjustment.tenant_id,
            adjustment.warehouse_id,
            adjustment.sku,
        )
        if key in self.applied_adjustments:
            return current.available

        current.available += adjustment.quantity
        self.applied_adjustments.add(key)
        actor_id = override_actor_id or adjustment.requested_by
        self.store.add_audit(
            AuditEntry(
                timestamp=self.clock.now(),
                event="adjusted",
                tenant_id=adjustment.tenant_id,
                warehouse_id=adjustment.warehouse_id,
                sku=adjustment.sku,
                quantity=adjustment.quantity,
                actor_id=actor_id,
                metadata={"reason_code": adjustment.reason_code},
            )
        )
        return current.available

    def reconcile_non_negative(self, tenant_id: str, sku: str) -> None:
        for (record_tenant, warehouse_id, record_sku), record in self.store.records.items():
            if record_tenant != tenant_id or record_sku != sku:
                continue
            if record.available < 0:
                record.available = 0
                self.store.add_audit(
                    AuditEntry(
                        timestamp=self.clock.now(),
                        event="reconciled",
                        tenant_id=tenant_id,
                        warehouse_id=warehouse_id,
                        sku=sku,
                        quantity=0,
                        actor_id="system",
                    )
                )
