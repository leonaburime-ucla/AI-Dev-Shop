from __future__ import annotations

import json

from src.webhook_rotation import (
    DualKeyGraceVerifier,
    SigningKey,
    TenantKeyRegistry,
    WebhookRequest,
    WebhookVerifier,
    constant_time_compare,
    sign,
)


def body(tenant_id: str = "tenant-a", event_id: str = "evt-1") -> bytes:
    return json.dumps({"tenant_id": tenant_id, "event_id": event_id}, sort_keys=True).encode(
        "utf-8"
    )


def request_for(
    *,
    secret: bytes,
    tenant_id: str = "tenant-a",
    route_tenant_id: str | None = "tenant-a",
    event_id: str = "evt-1",
    nonce: str = "nonce-1",
    timestamp: float = 1000.0,
) -> WebhookRequest:
    raw = body(tenant_id, event_id)
    return WebhookRequest(
        provider="stripe",
        route_tenant_id=route_tenant_id,
        raw_body=raw,
        headers={
            "x-webhook-timestamp": str(timestamp),
            "x-webhook-nonce": nonce,
            "x-webhook-signature": sign(secret, raw),
        },
    )


def registry_with_key(secret: bytes = b"current") -> TenantKeyRegistry:
    registry = TenantKeyRegistry()
    registry.set_current(
        SigningKey(
            tenant_id="tenant-a",
            provider="stripe",
            version="v2",
            secret=secret,
        )
    )
    return registry


def test_valid_same_tenant_signature_is_allowed() -> None:
    registry = registry_with_key()
    verifier = WebhookVerifier(registry)

    assert verifier.verify(request_for(secret=b"current"), now=1000)


def test_replay_nonce_rejected_for_same_tenant() -> None:
    registry = registry_with_key()
    verifier = WebhookVerifier(registry)
    req = request_for(secret=b"current")

    assert verifier.verify(req, now=1000)
    assert not verifier.verify(req, now=1001)


def test_old_timestamp_is_rejected() -> None:
    registry = registry_with_key()
    verifier = WebhookVerifier(registry, tolerance_seconds=300)

    assert not verifier.verify(request_for(secret=b"current", timestamp=600), now=1000)


def test_legacy_key_accepted_during_rotation_setup() -> None:
    registry = TenantKeyRegistry()
    registry.set_current(
        SigningKey("tenant-a", "stripe", "v1", b"old", retired_at=900)
    )
    registry.set_current(SigningKey("tenant-a", "stripe", "v2", b"new"))
    verifier = WebhookVerifier(registry, rotation_grace_seconds=100)

    assert verifier.verify(request_for(secret=b"old", nonce="old-key"), now=950)


def test_audit_records_failed_verification() -> None:
    registry = registry_with_key()
    verifier = WebhookVerifier(registry)

    assert not verifier.verify(request_for(secret=b"wrong", nonce="bad"), now=1000)
    assert verifier.audit.entries[-1]["reason"] == "signature"


def test_constant_time_compare_accepts_equal_digest() -> None:
    digest = "a" * 64

    assert constant_time_compare(digest, digest)
    assert not constant_time_compare(digest, "b" * 64)


def test_dual_key_grace_verifier_rejects_after_expiry() -> None:
    verifier = DualKeyGraceVerifier(grace_seconds=10)

    assert verifier.accepts_legacy(retired_at=100, now=105)
    assert not verifier.accepts_legacy(retired_at=100, now=111)
