from __future__ import annotations

from src.cache_migration import (
    DualWriteCompatibilityShim,
    InMemoryCache,
    MigrationFlags,
    ProfileCacheMigration,
    SchemaTransformer,
    versioned_cache_key,
)


def legacy_profile(user_id: str = "u-1") -> dict[str, object]:
    return {
        "user_id": user_id,
        "email": f"{user_id}@example.test",
        "name": "User One",
        "marketing_opt_in": False,
        "risk_flags": ["manual-review"],
    }


def test_dual_write_populates_legacy_and_v2_caches() -> None:
    service = ProfileCacheMigration("tenant-a")
    flags = MigrationFlags(write_v2=True, dual_write=True)

    service.write_profile("u-1", legacy_profile(), flags, now=10)

    assert service.legacy_cache.get("tenant-a:v1:profile:u-1") is not None
    assert service.v2_cache.get("tenant-a:v2:profile:u-1") is not None


def test_read_v2_falls_back_to_legacy_cache() -> None:
    service = ProfileCacheMigration("tenant-a")
    service.write_profile("u-1", legacy_profile(), MigrationFlags(), now=10)

    result = service.read_profile("u-1", MigrationFlags(read_v2=True), now=20)

    assert result is not None
    assert result["display_name"] == "User One"
    assert service.metrics.counters["legacy_hits"] == 1


def test_schema_transform_forward_shape() -> None:
    transformed = SchemaTransformer.v1_to_v2(legacy_profile())

    assert transformed["user_id"] == "u-1"
    assert transformed["display_name"] == "User One"
    assert transformed["risk_flags"] == ["manual-review"]


def test_shadow_read_records_mismatch_count() -> None:
    service = ProfileCacheMigration("tenant-a")
    service.write_profile("u-1", legacy_profile(), MigrationFlags(write_v2=True), now=10)
    service.repopulate_legacy_cache(
        "u-1",
        {**legacy_profile(), "name": "Old Name"},
        snapshot_generation=1,
        now=20,
    )

    service.read_profile("u-1", MigrationFlags(read_v2=False, shadow_read=True), now=30)

    assert service.metrics.counters["shadow_mismatch"] == 1


def test_versioned_cache_key_is_schema_scoped() -> None:
    assert versioned_cache_key("tenant-a", "u-1", "v1") == "tenant-a:v1:profile:u-1"
    assert versioned_cache_key("tenant-a", "u-1", "v2") == "tenant-a:v2:profile:u-1"


def test_dual_write_compatibility_shim_is_lossless() -> None:
    legacy = InMemoryCache()
    v2 = InMemoryCache()
    shim = DualWriteCompatibilityShim()
    profile_v2 = {
        "user_id": "u-1",
        "email": "u-1@example.test",
        "display_name": "User One",
        "risk_flags": ["manual-review"],
        "marketing_opt_in": False,
        "metadata": {"tier": "gold"},
    }

    shim.write_pair(legacy, v2, "tenant-a", profile_v2, now=40, generation=2)

    assert legacy.get("tenant-a:v1:profile:u-1") is not None
    assert v2.get("tenant-a:v2:profile:u-1").value == profile_v2


def test_promotion_uses_backfill_flag() -> None:
    service = ProfileCacheMigration("tenant-a")

    assert service.promote_tenant("tenant-a", MigrationFlags(backfill_complete=True))
    assert "tenant-a" in service.promoted_tenants
