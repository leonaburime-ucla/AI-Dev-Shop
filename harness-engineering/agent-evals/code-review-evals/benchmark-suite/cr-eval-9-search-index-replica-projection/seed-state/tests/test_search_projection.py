from __future__ import annotations

from src.search_projection import (
    ProjectionEvent,
    SearchProjection,
    TenantShardValidator,
    VersionGatedWriter,
)


def event(
    document_id: str = "doc-1",
    *,
    tenant_id: str | None = "tenant-a",
    version: int = 1,
    op: str = "upsert",
    fields: dict[str, object] | None = None,
) -> ProjectionEvent:
    return ProjectionEvent(
        document_id=document_id,
        tenant_id=tenant_id,
        version=version,
        op=op,
        fields=fields or {"title": "First", "body": "Body", "updated_at": 1},
    )


def test_increasing_version_updates_document() -> None:
    projection = SearchProjection()
    projection.apply_event(event(version=1, fields={"title": "First"}))
    projection.apply_event(event(version=2, fields={"title": "Second"}))

    assert projection.index["doc-1"].version == 2
    assert projection.index["doc-1"].fields["title"] == "Second"


def test_older_version_is_rejected() -> None:
    projection = SearchProjection()
    projection.apply_event(event(version=2, fields={"title": "Second"}))
    projection.apply_event(event(version=1, fields={"title": "First"}))

    assert projection.index["doc-1"].fields["title"] == "Second"
    assert projection.metrics.counters["rejected"] == 1


def test_delete_creates_tombstone() -> None:
    projection = SearchProjection()
    projection.apply_event(event(version=1))
    projection.apply_event(event(version=2, op="delete", fields={}))

    assert projection.index["doc-1"].tombstoned
    assert projection.search("tenant-a") == []


def test_alias_swap_changes_read_alias() -> None:
    projection = SearchProjection()
    projection.lag_monitor.update("tenant-a:shard-1", 10)

    projection.alias_manager.swap_alias(
        "profiles-v2",
        target_version=10,
        expected_shards={"tenant-a:shard-1"},
    )

    assert projection.alias_manager.current_alias == "profiles-v2"


def test_backfill_projects_known_fields() -> None:
    projection = SearchProjection()
    projection.apply_event(
        event(
            version=3,
            op="backfill",
            fields={"title": "Backfilled", "body": "B", "updated_at": 3},
        )
    )

    assert projection.index["doc-1"].fields == {
        "title": "Backfilled",
        "body": "B",
        "updated_at": 3,
    }


def test_query_filters_by_tenant() -> None:
    projection = SearchProjection()
    projection.apply_event(event("doc-a", tenant_id="tenant-a"))
    projection.apply_event(event("doc-b", tenant_id="tenant-b"))

    assert [doc.document_id for doc in projection.search("tenant-a")] == ["doc-a"]


def test_version_gated_writer_skips_same_version() -> None:
    writer = VersionGatedWriter()

    assert writer.should_apply(1, 2)
    assert not writer.should_apply(2, 2)
    assert not writer.should_apply(3, 2)


def test_tenant_shard_validator_rejects_wrong_shard() -> None:
    validator = TenantShardValidator({"tenant-a": {"tenant-a:shard-0"}})

    assert validator.allows("tenant-a", "tenant-a:shard-0")
    assert not validator.allows("tenant-a", "default:shard-0")
