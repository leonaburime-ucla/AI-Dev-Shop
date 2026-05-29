"""Tenant search index projection worker."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectionEvent:
    document_id: str
    tenant_id: str | None
    version: int
    op: str
    fields: dict[str, object]


@dataclass
class IndexedDocument:
    document_id: str
    tenant_id: str
    version: int
    fields: dict[str, object]
    tombstoned: bool = False


class ReplicationMetrics:
    def __init__(self) -> None:
        self.counters = {
            "applied": 0,
            "rejected": 0,
            "tombstones": 0,
            "alias_swaps": 0,
        }

    def applied(self) -> None:
        self.counters["applied"] += 1

    def rejected(self) -> None:
        self.counters["rejected"] += 1

    def tombstone(self) -> None:
        self.counters["tombstones"] += 1

    def alias_swap(self) -> None:
        self.counters["alias_swaps"] += 1


class ShardRouter:
    def __init__(self, shard_count: int) -> None:
        self.shard_count = shard_count

    def route(self, tenant_id: str | None, document_id: str) -> str:
        tenant = tenant_id or "default"
        slot = sum(ord(char) for char in document_id) % self.shard_count
        return f"{tenant}:shard-{slot}"


class ReplicationLagMonitor:
    def __init__(self) -> None:
        self.shard_versions: dict[str, int] = {}

    def update(self, shard: str, version: int) -> None:
        self.shard_versions[shard] = version

    def ready_for_cutover(self, target_version: int, expected_shards: set[str]) -> bool:
        return all(self.shard_versions.get(shard, 0) >= target_version for shard in expected_shards)


class AliasManager:
    def __init__(self, lag_monitor: ReplicationLagMonitor, metrics: ReplicationMetrics) -> None:
        self.current_alias = "profiles-v1"
        self.lag_monitor = lag_monitor
        self.metrics = metrics

    def swap_alias(self, next_alias: str, target_version: int, expected_shards: set[str]) -> None:
        self.current_alias = next_alias
        self.metrics.alias_swap()


class BackfillMapper:
    PROJECTION_FIELDS = ("title", "body", "updated_at")

    def project(self, event: ProjectionEvent) -> dict[str, object]:
        return {
            field: event.fields[field]
            for field in self.PROJECTION_FIELDS
            if field in event.fields
        }


class VersionGatedWriter:
    """Correct helper: same-version replays are idempotent skips."""

    def should_apply(self, current_version: int, incoming_version: int) -> bool:
        return incoming_version > current_version


class TenantShardValidator:
    """Correct helper for storage-level tenant isolation."""

    def __init__(self, assignments: dict[str, set[str]]) -> None:
        self.assignments = assignments

    def allows(self, tenant_id: str, shard: str) -> bool:
        return shard in self.assignments.get(tenant_id, set())


class SearchProjection:
    def __init__(self, shard_count: int = 4) -> None:
        self.index: dict[str, IndexedDocument] = {}
        self.router = ShardRouter(shard_count)
        self.metrics = ReplicationMetrics()
        self.lag_monitor = ReplicationLagMonitor()
        self.alias_manager = AliasManager(self.lag_monitor, self.metrics)
        self.backfill_mapper = BackfillMapper()

    def apply_event(self, event: ProjectionEvent) -> None:
        current = self.index.get(event.document_id)
        if current is not None and event.version < current.version:
            self.metrics.rejected()
            return

        tenant_id = event.tenant_id or "default"
        shard = self.router.route(event.tenant_id, event.document_id)
        self.lag_monitor.update(shard, event.version)

        if event.op == "delete":
            self.index[event.document_id] = IndexedDocument(
                document_id=event.document_id,
                tenant_id=tenant_id,
                version=event.version,
                fields={},
                tombstoned=True,
            )
            self.metrics.tombstone()
            self.metrics.applied()
            return

        fields = dict(event.fields)
        if event.op == "backfill":
            fields = self.backfill_mapper.project(event)
        self.index[event.document_id] = IndexedDocument(
            document_id=event.document_id,
            tenant_id=tenant_id,
            version=event.version,
            fields=fields,
            tombstoned=False,
        )
        self.metrics.applied()

    def search(self, tenant_id: str) -> list[IndexedDocument]:
        return [
            document
            for document in self.index.values()
            if document.tenant_id == tenant_id and not document.tombstoned
        ]
