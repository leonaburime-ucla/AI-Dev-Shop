"""
Tests for Notification Service.

Coverage: formatting, sending, retries, channel availability, legacy compat.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.notification_service import (
    NotificationRecord,
    NotificationRequest,
    format_message,
    legacy_notify,
    process_pending_notifications,
    send_notification,
)


# --- Test helpers ---


def make_mock_provider(**overrides: object) -> AsyncMock:
    provider = AsyncMock()
    provider.send = AsyncMock(return_value={"success": True})
    provider.is_available = AsyncMock(return_value=True)
    for key, value in overrides.items():
        setattr(provider, key, value)
    return provider


def make_mock_store(**overrides: object) -> AsyncMock:
    store = AsyncMock()
    store.save = AsyncMock(return_value=None)
    store.find_by_id = AsyncMock(return_value=None)
    store.find_pending = AsyncMock(return_value=[])
    for key, value in overrides.items():
        setattr(store, key, value)
    return store


def make_providers(**overrides: object) -> dict[str, AsyncMock]:
    providers: dict[str, AsyncMock] = {
        "email": make_mock_provider(),
        "sms": make_mock_provider(),
        "push": make_mock_provider(),
    }
    providers.update(overrides)
    return providers


def make_request(**overrides: object) -> NotificationRequest:
    defaults = {
        "recipient_id": "USER-001",
        "channel": "email",
        "subject": "Test Notification",
        "body": "Hello, this is a test notification.",
        "priority": "high",
    }
    defaults.update(overrides)
    return NotificationRequest(**defaults)


# --- format_message tests ---


class TestFormatMessage:
    def test_should_format_email_with_subject(self) -> None:
        result = format_message("email", "Hello", "Body text")
        assert result == "Subject: Hello\n\nBody text"

    def test_should_format_email_without_subject(self) -> None:
        result = format_message("email", None, "Body text")
        assert result == "Body text"

    def test_should_truncate_sms_to_160_chars(self) -> None:
        long_message = "A" * 200
        result = format_message("sms", None, long_message)
        assert len(result) <= 160
        assert "..." in result

    def test_should_not_truncate_short_sms(self) -> None:
        result = format_message("sms", None, "Short message")
        assert result == "Short message"

    def test_should_truncate_push_to_100_chars_and_strip_newlines(self) -> None:
        long_message = "Line 1\nLine 2\n" + "A" * 200
        result = format_message("push", None, long_message)
        assert len(result) <= 100
        assert "\n" not in result

    def test_should_return_body_for_unknown_channel(self) -> None:
        result = format_message("carrier-pigeon", None, "Body")  # type: ignore[arg-type]
        assert result == "Body"


# --- send_notification tests ---


class TestSendNotification:
    @pytest.mark.asyncio
    async def test_should_send_notification_successfully(self) -> None:
        providers = make_providers()
        store = make_mock_store()

        result = await send_notification(
            make_request(), {"providers": providers, "store": store}
        )

        assert result.status == "sent"
        assert result.notification_id  # truthy check
        assert store.save.call_count == 1

    @pytest.mark.asyncio
    async def test_should_throw_for_unknown_channel(self) -> None:
        providers: dict[str, AsyncMock] = {}
        store = make_mock_store()

        with pytest.raises(ValueError, match="Unknown channel"):
            await send_notification(
                make_request(channel="fax"),  # type: ignore[arg-type]
                {"providers": providers, "store": store},
            )

    @pytest.mark.asyncio
    async def test_should_queue_when_channel_is_unavailable(self) -> None:
        email_provider = make_mock_provider(
            is_available=AsyncMock(return_value=False),
        )
        providers = make_providers(email=email_provider)
        store = make_mock_store()

        result = await send_notification(
            make_request(), {"providers": providers, "store": store}
        )

        assert result.status == "queued"
        assert store.save.call_count == 1

    @pytest.mark.asyncio
    async def test_should_retry_on_failure_and_eventually_succeed(self) -> None:
        email_provider = make_mock_provider(
            send=AsyncMock(
                side_effect=[
                    {"success": False, "error": "Temporary failure"},
                    {"success": True},
                ]
            ),
        )
        providers = make_providers(email=email_provider)
        store = make_mock_store()

        result = await send_notification(
            make_request(), {"providers": providers, "store": store}
        )

        assert result.status == "sent"
        assert email_provider.send.call_count == 2

    @pytest.mark.asyncio
    async def test_should_fail_after_all_retries_exhausted(self) -> None:
        email_provider = make_mock_provider(
            send=AsyncMock(return_value={"success": False, "error": "Persistent failure"}),
        )
        providers = make_providers(email=email_provider)
        store = make_mock_store()

        result = await send_notification(
            make_request(), {"providers": providers, "store": store}
        )

        assert result.status == "failed"
        assert result.error == "Persistent failure"
        assert email_provider.send.call_count == 3

    @pytest.mark.asyncio
    async def test_should_handle_provider_throwing_exceptions(self) -> None:
        email_provider = make_mock_provider(
            send=AsyncMock(side_effect=RuntimeError("Network error")),
        )
        providers = make_providers(email=email_provider)
        store = make_mock_store()

        result = await send_notification(
            make_request(), {"providers": providers, "store": store}
        )

        assert result.status == "failed"
        assert result.error == "Network error"


# --- legacy_notify tests ---


class TestLegacyNotify:
    @pytest.mark.asyncio
    async def test_should_return_true_on_success(self) -> None:
        provider = make_mock_provider()
        result = await legacy_notify("user@example.com", "Hello", provider)
        assert result is True

    @pytest.mark.asyncio
    async def test_should_return_false_on_failure(self) -> None:
        provider = make_mock_provider(
            send=AsyncMock(return_value={"success": False}),
        )
        result = await legacy_notify("user@example.com", "Hello", provider)
        assert result is False

    @pytest.mark.asyncio
    async def test_should_return_false_on_exception(self) -> None:
        provider = make_mock_provider(
            send=AsyncMock(side_effect=RuntimeError("Boom")),
        )
        result = await legacy_notify("user@example.com", "Hello", provider)
        assert result is False


# --- process_pending_notifications tests ---


class TestProcessPendingNotifications:
    @pytest.mark.asyncio
    async def test_should_process_pending_notifications(self) -> None:
        pending: list[NotificationRecord] = [
            NotificationRecord(
                id="NOTIF-1",
                recipient_id="USER-001",
                channel="email",
                body="Pending message",
                formatted_body="Pending message",
                priority="high",
                status="queued",
                attempts=0,
            ),
        ]
        providers = make_providers()
        store = make_mock_store(
            find_pending=AsyncMock(return_value=pending),
        )

        results = await process_pending_notifications(
            "email", {"providers": providers, "store": store}
        )

        assert len(results) == 1
        assert results[0].status == "sent"

    @pytest.mark.asyncio
    async def test_should_return_empty_list_when_no_pending(self) -> None:
        providers = make_providers()
        store = make_mock_store()

        results = await process_pending_notifications(
            "email", {"providers": providers, "store": store}
        )

        assert len(results) == 0
