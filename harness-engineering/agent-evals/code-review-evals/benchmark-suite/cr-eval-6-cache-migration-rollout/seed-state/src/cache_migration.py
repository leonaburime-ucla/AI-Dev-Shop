"""Profile cache migration coordinator fixture."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256


@dataclass(frozen=True)
class CacheEntry:
    key: str
    value: dict[str, object]
    schema_version: str
    ttl_seconds: int
    written_at: float
    generation: int


@dataclass(frozen=True)
class MigrationFlags:
    read_v2: bool = False
    write_v2: bool = False
    dual_write: bool = False
    shadow_read: bool = False
    backfill_complete: bool = False


class InMemoryCache:
    def __init__(self) -> None:
        self.entries: dict[str, CacheEntry] = {}

    def put(self, entry: CacheEntry) -> None:
        self.entries[entry.key] = entry

    def get(self, key: str) -> CacheEntry | None:
        return self.entries.get(key)

    def delete(self, key: str) -> None:
        self.entries.pop(key, None)

    def clear_prefix(self, prefix: str) -> None:
        for key in list(self.entries):
            if key.startswith(prefix):
                del self.entries[key]


class SchemaTransformer:
    @staticmethod
    def v1_to_v2(profile: dict[str, object]) -> dict[str, object]:
        return {
            "user_id": profile["user_id"],
            "email": profile["email"],
            "display_name": profile.get("name", ""),
            "risk_flags": list(profile.get("risk_flags", [])),
            "marketing_opt_in": bool(profile.get("marketing_opt_in", True)),
            "metadata": dict(profile.get("metadata", {})),
        }

    @staticmethod
    def v2_to_v1(profile: dict[str, object]) -> dict[str, object]:
        return {
            "user_id": profile["user_id"],
            "email": profile["email"],
            "name": profile.get("display_name", ""),
            "marketing_opt_in": profile.get("marketing_opt_in", True),
        }


class MigrationMetrics:
    def __init__(self) -> None:
        self.counters: dict[str, int] = {
            "legacy_hits": 0,
            "v2_hits": 0,
            "shadow_mismatch": 0,
        }
        self.events: list[dict[str, object]] = []

    def record_hit(self, cache_name: str) -> None:
        self.counters[f"{cache_name}_hits"] += 1

    def record_shadow_mismatch(self, user_id: str) -> None:
        self.counters["shadow_mismatch"] += 1
        self.events.append({"event": "shadow_mismatch"})


def versioned_cache_key(tenant_id: str, user_id: str, schema_version: str) -> str:
    return f"{tenant_id}:{schema_version}:profile:{user_id}"


class DualWriteCompatibilityShim:
    """Correct helper: writes both shapes while rollback is allowed."""

    def write_pair(
        self,
        legacy: InMemoryCache,
        v2: InMemoryCache,
        tenant_id: str,
        profile_v2: dict[str, object],
        now: float,
        generation: int,
    ) -> None:
        user_id = str(profile_v2["user_id"])
        legacy.put(
            CacheEntry(
                key=versioned_cache_key(tenant_id, user_id, "v1"),
                value=SchemaTransformer.v2_to_v1(profile_v2),
                schema_version="v1",
                ttl_seconds=300,
                written_at=now,
                generation=generation,
            )
        )
        v2.put(
            CacheEntry(
                key=versioned_cache_key(tenant_id, user_id, "v2"),
                value=dict(profile_v2),
                schema_version="v2",
                ttl_seconds=300,
                written_at=now,
                generation=generation,
            )
        )


class ProfileCacheMigration:
    def __init__(self, tenant_id: str) -> None:
        self.tenant_id = tenant_id
        self.legacy_cache = InMemoryCache()
        self.v2_cache = InMemoryCache()
        self.database: dict[str, dict[str, object]] = {}
        self.metrics = MigrationMetrics()
        self.cache_generation = 0
        self.backfill_watermark: dict[str, int] = {}
        self.promoted_tenants: set[str] = set()

    def write_profile(
        self,
        user_id: str,
        profile: dict[str, object],
        flags: MigrationFlags,
        now: float,
    ) -> None:
        self.cache_generation += 1
        profile_v2 = SchemaTransformer.v1_to_v2(profile)
        self.database[user_id] = dict(profile_v2)

        legacy_key = versioned_cache_key(self.tenant_id, user_id, "v1")
        v2_key = versioned_cache_key(self.tenant_id, user_id, "v2")
        self.legacy_cache.delete(legacy_key)
        self.v2_cache.delete(v2_key)

        if flags.write_v2:
            self.v2_cache.put(
                CacheEntry(v2_key, profile_v2, "v2", 300, now, self.cache_generation)
            )
            if flags.dual_write:
                self.legacy_cache.put(
                    CacheEntry(
                        legacy_key,
                        SchemaTransformer.v2_to_v1(profile_v2),
                        "v1",
                        300,
                        now,
                        self.cache_generation,
                    )
                )
        else:
            self.legacy_cache.put(
                CacheEntry(legacy_key, dict(profile), "v1", 300, now, self.cache_generation)
            )

    def read_profile(
        self,
        user_id: str,
        flags: MigrationFlags,
        now: float,
    ) -> dict[str, object] | None:
        if flags.read_v2:
            entry = self.v2_cache.get(versioned_cache_key(self.tenant_id, user_id, "v2"))
            if entry is not None:
                self.metrics.record_hit("v2")
                return dict(entry.value)

        legacy_entry = self.legacy_cache.get(
            versioned_cache_key(self.tenant_id, user_id, "v1")
        )
        if legacy_entry is not None:
            self.metrics.record_hit("legacy")
            profile_v2 = SchemaTransformer.v1_to_v2(legacy_entry.value)
            if flags.shadow_read:
                v2_entry = self.v2_cache.get(
                    versioned_cache_key(self.tenant_id, user_id, "v2")
                )
                if v2_entry is not None and v2_entry.value != profile_v2:
                    self.metrics.record_shadow_mismatch(user_id)
            return profile_v2 if flags.read_v2 else dict(legacy_entry.value)

        stored = self.database.get(user_id)
        if stored is None:
            return None
        self.repopulate_legacy_cache(
            user_id,
            SchemaTransformer.v2_to_v1(stored),
            snapshot_generation=0,
            now=now,
        )
        return dict(stored) if flags.read_v2 else SchemaTransformer.v2_to_v1(stored)

    def repopulate_legacy_cache(
        self,
        user_id: str,
        snapshot: dict[str, object],
        snapshot_generation: int,
        now: float,
    ) -> None:
        self.legacy_cache.put(
            CacheEntry(
                versioned_cache_key(self.tenant_id, user_id, "v1"),
                dict(snapshot),
                "v1",
                300,
                now,
                snapshot_generation,
            )
        )

    def mark_backfill_complete(self, tenant_id: str, watermark_generation: int) -> None:
        self.backfill_watermark[tenant_id] = watermark_generation

    def promote_tenant(self, tenant_id: str, flags: MigrationFlags) -> bool:
        if flags.backfill_complete:
            self.promoted_tenants.add(tenant_id)
            return True
        return False

    def rollout_bucket(self, user_id: str) -> int:
        digest = sha256(f"{self.tenant_id}:{user_id}".encode("utf-8")).hexdigest()
        return int(digest[:8], 16) % 100
