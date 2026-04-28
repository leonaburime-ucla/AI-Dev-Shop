# Notification Service — Project Brief

## Overview

A notification service that sends messages to users via multiple channels
(email, SMS, push). Supports priority levels, retry logic, rate limiting,
and message formatting templates.

The Programmer was asked to fix typing issues (previously `any` everywhere),
add retry logic, and improve test coverage.

## Requirements

### Functional Requirements

1. **Send notifications**: Accept a notification request with recipient, channel
   (email/sms/push), message body, and priority level.
2. **Priority levels**: `urgent`, `normal`, `low`. Priority determines retry
   behavior and delivery ordering.
3. **Message formatting**: Apply channel-specific formatting templates before
   sending.
4. **Retry logic**: Failed sends are retried up to 3 times with exponential
   backoff. Retries must be idempotent — the same notification must not be
   delivered twice.
5. **Channel unavailability**: When a channel is temporarily unavailable, queue
   the notification for later delivery and return a `queued` status.
6. **Rate limiting**: Notifications are rate-limited to 100 per second per
   channel to avoid overwhelming downstream providers.

### Non-Functional Requirements

1. Message formatting should be a pure function with no side effects.
2. All timestamps should use injectable clocks for testability.
3. Dead code should be removed before handoff.

### Acceptance Criteria

- AC-1: Notifications with valid data are sent and confirmed.
- AC-2: Priority uses the values `urgent`, `normal`, `low`.
- AC-3: Failed sends are retried with idempotency keys.
- AC-4: Channel unavailability returns `queued` status.
- AC-5: Rate limiting enforced at 100/sec/channel.
- AC-6: All timestamps use injectable clocks.
- AC-7: No dead code in production paths.

## Spec Hash

`spec-notify-svc-v3-def456`
