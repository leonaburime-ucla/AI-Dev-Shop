"""Tests for the notification dispatcher fixture."""
from __future__ import annotations

from src.notification_service import (
    Notification,
    NotificationDispatcher,
    ProviderAdapter,
)


def make_notification(**overrides: object) -> Notification:
    defaults = {
        "tenant_id": "tenant-a",
        "notification_id": "welcome-1",
        "user_id": "user-1",
        "channel": "email",
        "template_id": "welcome",
        "template_version": 1,
        "locale": "en-US",
        "priority": "normal",
        "topic": "marketing",
        "payload": {"body": "Your order is ready."},
    }
    defaults.update(overrides)
    return Notification(**defaults)


def make_dispatcher(**providers: ProviderAdapter) -> NotificationDispatcher:
    defaults: dict[str, ProviderAdapter] = {
        "email": ProviderAdapter("email-primary"),
        "sms": ProviderAdapter("sms-primary"),
        "push": ProviderAdapter("push-primary"),
    }
    defaults.update(providers)
    return NotificationDispatcher(providers=defaults)


def test_dispatches_email_notification() -> None:
    dispatcher = make_dispatcher()

    result = dispatcher.dispatch(make_notification())

    assert result.status == "sent"
    assert result.channel == "email"
    assert dispatcher.providers["email"].sent


def test_falls_back_to_sms_after_email_hard_failure() -> None:
    dispatcher = make_dispatcher(email=ProviderAdapter("email-primary", hard_fail=True))

    result = dispatcher.dispatch(make_notification())

    assert result.status == "sent"
    assert result.channel == "sms"
    assert dispatcher.providers["sms"].sent


def test_suppresses_primary_channel_by_policy() -> None:
    dispatcher = make_dispatcher()
    dispatcher.policy.suppress("tenant-a", "user-1", "email", "marketing")

    result = dispatcher.dispatch(make_notification())

    assert result.status == "suppressed"
    assert dispatcher.providers["email"].sent == []


def test_template_renderer_formats_payload() -> None:
    dispatcher = make_dispatcher()
    body = dispatcher.renderer.render(
        make_notification(payload={"body": "Localized body"})
    )

    assert "Localized body" in body
    assert "en-US v1" in body


def test_duplicate_send_returns_prior_result() -> None:
    dispatcher = make_dispatcher()
    notification = make_notification()

    first = dispatcher.dispatch(notification)
    second = dispatcher.dispatch(notification)

    assert first.status == "sent"
    assert second.status == "duplicate"
    assert len(dispatcher.providers["email"].sent) == 1


def test_audit_records_delivery_event() -> None:
    dispatcher = make_dispatcher()

    dispatcher.dispatch(make_notification())

    assert dispatcher.audit.events == [
        {
            "event": "sent",
            "notification_id": "welcome-1",
            "status": "sent",
        }
    ]
