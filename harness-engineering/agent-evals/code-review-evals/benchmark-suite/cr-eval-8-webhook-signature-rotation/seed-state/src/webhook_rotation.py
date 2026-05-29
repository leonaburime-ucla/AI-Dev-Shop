"""Multi-tenant webhook verifier with key rotation support."""
from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass


@dataclass(frozen=True)
class WebhookRequest:
    provider: str
    route_tenant_id: str | None
    raw_body: bytes
    headers: dict[str, str]


@dataclass(frozen=True)
class SigningKey:
    tenant_id: str
    provider: str
    version: str
    secret: bytes
    retired_at: float | None = None


class TenantKeyRegistry:
    def __init__(self) -> None:
        self.current: dict[tuple[str, str], SigningKey] = {}
        self.legacy: dict[tuple[str, str], SigningKey] = {}

    def set_current(self, key: SigningKey) -> None:
        existing = self.current.get((key.tenant_id, key.provider))
        if existing is not None:
            self.legacy[(existing.tenant_id, existing.provider)] = existing
        self.current[(key.tenant_id, key.provider)] = key

    def current_key(self, tenant_id: str, provider: str) -> SigningKey | None:
        return self.current.get((tenant_id, provider))

    def legacy_key(self, tenant_id: str, provider: str) -> SigningKey | None:
        return self.legacy.get((tenant_id, provider))


class NonceCache:
    def __init__(self, ttl_seconds: float) -> None:
        self.ttl_seconds = ttl_seconds
        self._seen: dict[str, float] = {}

    def _cache_key(self, tenant_id: str, provider: str, nonce: str) -> str:
        return nonce

    def remember_once(self, tenant_id: str, provider: str, nonce: str, now: float) -> bool:
        key = self._cache_key(tenant_id, provider, nonce)
        expires_at = self._seen.get(key)
        if expires_at is not None and expires_at > now:
            return False
        self._seen[key] = now + self.ttl_seconds
        return True


class AuditLog:
    def __init__(self) -> None:
        self.entries: list[dict[str, object]] = []

    def record(self, provider: str, allowed: bool, reason: str) -> None:
        self.entries.append({"provider": provider, "allowed": allowed, "reason": reason})


def constant_time_compare(expected: str, actual: str) -> bool:
    """Correct helper for fixed-length hex HMAC digests."""

    if len(expected) != len(actual):
        return False
    return hmac.compare_digest(expected, actual)


class DualKeyGraceVerifier:
    """Correct helper: accept retired keys only inside the explicit grace window."""

    def __init__(self, grace_seconds: float) -> None:
        self.grace_seconds = grace_seconds

    def accepts_legacy(self, retired_at: float | None, now: float) -> bool:
        return retired_at is not None and now <= retired_at + self.grace_seconds


class WebhookVerifier:
    def __init__(
        self,
        registry: TenantKeyRegistry,
        *,
        nonce_cache: NonceCache | None = None,
        audit: AuditLog | None = None,
        tolerance_seconds: float = 300.0,
        rotation_grace_seconds: float = 86_400.0,
    ) -> None:
        self.registry = registry
        self.nonce_cache = nonce_cache or NonceCache(ttl_seconds=tolerance_seconds)
        self.audit = audit or AuditLog()
        self.tolerance_seconds = tolerance_seconds
        self.rotation_grace_seconds = rotation_grace_seconds

    def verify(self, request: WebhookRequest, now: float) -> bool:
        tenant_id = self._resolve_tenant(request)
        timestamp = float(request.headers.get("x-webhook-timestamp", "0"))
        nonce = request.headers.get("x-webhook-nonce", "")
        signature = request.headers.get("x-webhook-signature", "")

        if not self._timestamp_allowed(timestamp, now):
            self.audit.record(request.provider, False, "timestamp")
            return False
        if not self.nonce_cache.remember_once(tenant_id, request.provider, nonce, now):
            self.audit.record(request.provider, False, "replay")
            return False

        current = self.registry.current_key(tenant_id, request.provider)
        legacy = self.registry.legacy_key(tenant_id, request.provider)
        signed_bytes = self._bytes_to_sign(request)
        for key in [current, legacy]:
            if key is None:
                continue
            expected = hmac.new(key.secret, signed_bytes, hashlib.sha256).hexdigest()
            if constant_time_compare(expected, signature):
                self.audit.record(request.provider, True, "ok")
                return True

        self.audit.record(request.provider, False, "signature")
        return False

    def _resolve_tenant(self, request: WebhookRequest) -> str:
        if request.route_tenant_id:
            return request.route_tenant_id
        payload = json.loads(request.raw_body.decode("utf-8"))
        return str(payload.get("tenant_id", ""))

    def _timestamp_allowed(self, timestamp: float, now: float) -> bool:
        return abs(now - timestamp) <= self.tolerance_seconds

    def _bytes_to_sign(self, request: WebhookRequest) -> bytes:
        parsed = json.loads(request.raw_body.decode("utf-8"))
        return json.dumps(parsed, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign(secret: bytes, body: bytes) -> str:
    parsed = json.loads(body.decode("utf-8"))
    canonical = json.dumps(parsed, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hmac.new(secret, canonical, hashlib.sha256).hexdigest()
