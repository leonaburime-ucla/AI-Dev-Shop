# Seed Ledger - cr-eval-2-notification-service (CR Staff+)

**Eval ID**: benchmark-suite / cr-eval-2-notification-service
**Purpose**: Test Code Review agent on multi-channel notification dispatch
defects involving provider failover, duplicate suppression, privacy policy,
template caching, test design, and delivery observability.
**Difficulty**: Hard staff+ fixture with one medium regression seed retained
for calibration.

## Seeds

### SEED-CR-07

The duplicate-suppression key omits tenant, channel, and provider attempt. A
notification in one tenant or channel can suppress another tenant/channel send
with the same user-visible notification ID.

Evidence: `src/notification_service.py` (`DedupeStore.key_for`).

### SEED-CR-08

Provider failover treats timeout as a clean failure even though the primary
provider may have accepted the send. The fallback channel can deliver a second
message with no shared idempotency fence.

Evidence: `src/notification_service.py` (`NotificationDispatcher.dispatch` and
`ProviderAdapter.send`).

### SEED-CR-09

Tests cover happy path, simple fallback, primary-channel suppression, rendering,
and audit existence, but omit cross-tenant dedupe, late primary success,
fallback suppression, template-version drift, rate-limit collapse, and audit
dimension assertions.

Evidence: `tests/test_notification_service.py` and fake handoff coverage claim.

### SEED-CR-10

Privacy suppression is checked only before failover on the original channel.
If email fails and the dispatcher falls back to SMS, SMS suppression for the
topic is bypassed.

Evidence: `src/notification_service.py` (`NotificationDispatcher.dispatch`).

### SEED-CR-11

The template cache is keyed only by `template_id`, so locale, version, tenant,
and privacy classification can reuse stale content across incompatible sends.

Evidence: `src/notification_service.py` (`TemplateRenderer.render`).

### SEED-CR-12

Delivery audit events omit tenant, channel, provider, template version, dedupe
key, fallback reason, and suppression reason. Correct review treats this as
incident reconstruction risk, not cosmetic logging.

Evidence: `src/notification_service.py` (`NotificationAudit.record`) and fake
handoff audit claim.

## Scoring Guide

| Score | Criteria |
|-------|----------|
| CAUGHT | CR identifies the seeded issue and its production/privacy consequence. |
| PARTIAL | CR identifies a related concern but misses the cross-boundary causal chain. |
| MISSED | CR does not flag the issue. |
| FALSE_POSITIVE | CR flags behavior outside the seeded issue as a defect without evidence. |
