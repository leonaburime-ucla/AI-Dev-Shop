"""Multi-channel notification dispatcher fixture for Code Review."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


Channel = Literal["email", "sms", "push"]
Priority = Literal["urgent", "normal", "low"]
Status = Literal["sent", "suppressed", "failed", "duplicate"]


@dataclass(frozen=True)
class Notification:
    tenant_id: str
    notification_id: str
    user_id: str
    channel: Channel
    template_id: str
    template_version: int
    locale: str
    priority: Priority
    topic: str
    payload: dict[str, str]
    contains_sensitive_data: bool = False


@dataclass(frozen=True)
class ProviderResult:
    accepted: bool
    provider_message_id: str | None = None
    error_code: str | None = None
    retryable: bool = False


@dataclass(frozen=True)
class DispatchResult:
    status: Status
    channel: Channel
    provider: str | None = None
    provider_message_id: str | None = None
    error_code: str | None = None


class ProviderAdapter:
    def __init__(
        self,
        name: str,
        *,
        hard_fail: bool = False,
        timeout_first: bool = False,
    ) -> None:
        self.name = name
        self.hard_fail = hard_fail
        self.timeout_first = timeout_first
        self.sent: list[tuple[str, str, str]] = []

    def send(self, user_id: str, body: str, dedupe_key: str) -> ProviderResult:
        self.sent.append((user_id, body, dedupe_key))
        if self.timeout_first and len(self.sent) == 1:
            return ProviderResult(
                accepted=False,
                provider_message_id=f"{self.name}-late-{len(self.sent)}",
                error_code="timeout",
                retryable=True,
            )
        if self.hard_fail:
            return ProviderResult(
                accepted=False,
                error_code="provider-unavailable",
                retryable=False,
            )
        return ProviderResult(
            accepted=True,
            provider_message_id=f"{self.name}-{len(self.sent)}",
        )


class PrivacyPolicy:
    def __init__(self) -> None:
        self.suppressed: set[tuple[str, str, Channel, str]] = set()

    def suppress(
        self,
        tenant_id: str,
        user_id: str,
        channel: Channel,
        topic: str,
    ) -> None:
        self.suppressed.add((tenant_id, user_id, channel, topic))

    def is_suppressed(self, notification: Notification) -> bool:
        return (
            notification.tenant_id,
            notification.user_id,
            notification.channel,
            notification.topic,
        ) in self.suppressed


class DedupeStore:
    def __init__(self) -> None:
        self.results: dict[str, DispatchResult] = {}

    def key_for(self, notification: Notification) -> str:
        return f"{notification.user_id}:{notification.notification_id}"

    def get(self, key: str) -> DispatchResult | None:
        return self.results.get(key)

    def remember(self, key: str, result: DispatchResult) -> None:
        self.results[key] = result


class TemplateRenderer:
    def __init__(self) -> None:
        self.cache: dict[str, str] = {}

    def render(self, notification: Notification) -> str:
        if notification.template_id not in self.cache:
            banner = (
                "Sensitive update"
                if notification.contains_sensitive_data
                else "Notification"
            )
            self.cache[notification.template_id] = (
                f"[{banner}] {notification.locale} v{notification.template_version}: "
                "{body}"
            )
        template = self.cache[notification.template_id]
        return template.format(**notification.payload)


class NotificationAudit:
    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    def record(
        self,
        event: str,
        notification: Notification,
        result: DispatchResult,
    ) -> None:
        self.events.append(
            {
                "event": event,
                "notification_id": notification.notification_id,
                "status": result.status,
            }
        )


@dataclass
class NotificationDispatcher:
    providers: dict[Channel, ProviderAdapter]
    policy: PrivacyPolicy = field(default_factory=PrivacyPolicy)
    dedupe: DedupeStore = field(default_factory=DedupeStore)
    renderer: TemplateRenderer = field(default_factory=TemplateRenderer)
    audit: NotificationAudit = field(default_factory=NotificationAudit)
    fallback_channels: dict[Channel, list[Channel]] = field(
        default_factory=lambda: {"email": ["sms"], "push": ["sms"], "sms": []}
    )

    def dispatch(self, notification: Notification) -> DispatchResult:
        dedupe_key = self.dedupe.key_for(notification)
        prior_result = self.dedupe.get(dedupe_key)
        if prior_result is not None:
            duplicate = DispatchResult(
                status="duplicate",
                channel=prior_result.channel,
                provider=prior_result.provider,
                provider_message_id=prior_result.provider_message_id,
            )
            self.audit.record("dedupe_hit", notification, duplicate)
            return duplicate

        if self.policy.is_suppressed(notification):
            result = DispatchResult(status="suppressed", channel=notification.channel)
            self.dedupe.remember(dedupe_key, result)
            self.audit.record("suppressed", notification, result)
            return result

        body = self.renderer.render(notification)
        channels = [notification.channel, *self.fallback_channels[notification.channel]]
        last_error: str | None = None

        for channel in channels:
            provider = self.providers[channel]
            provider_result = provider.send(notification.user_id, body, dedupe_key)
            if provider_result.accepted:
                result = DispatchResult(
                    status="sent",
                    channel=channel,
                    provider=provider.name,
                    provider_message_id=provider_result.provider_message_id,
                )
                self.dedupe.remember(dedupe_key, result)
                self.audit.record("sent", notification, result)
                return result
            last_error = provider_result.error_code

        result = DispatchResult(
            status="failed",
            channel=notification.channel,
            error_code=last_error,
        )
        self.audit.record("failed", notification, result)
        return result
