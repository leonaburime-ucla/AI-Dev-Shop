# Multi-Channel Notification Dispatcher - Project Brief

## Overview

The notification service dispatches operational and marketing messages across
email, SMS, and push providers. The implementation now supports provider
failover, unsubscribe policy checks, template rendering with locale/version
metadata, duplicate suppression, and audit events for delivery operations.

This eval is intentionally focused on Code Review depth. The code and tests
cover common success paths, but production failures emerge when duplicate
suppression, provider failover, fallback channels, template cache keys, privacy
rules, and audit evidence interact.

## Requirements

### Functional Requirements

1. Duplicate suppression must be scoped by tenant, notification, channel, and
   provider attempt so cross-tenant or cross-channel sends cannot collide.
2. Provider failover must remain idempotent when a primary provider times out
   after accepting a request and the dispatcher retries on a fallback channel.
3. Privacy suppression must be evaluated for the actual channel that will be
   used, including fallback channels.
4. Templates must be rendered by tenant, template ID, locale, version, and
   privacy classification. Cached templates must not cross those boundaries.
5. Delivery audit events must include tenant, channel, provider, template
   version, dedupe key, fallback reason, and suppression reason.
6. Tests must cover cross-tenant duplicate keys, late primary success after
   failover, fallback privacy suppression, template-version drift, provider
   backoff, and audit evidence completeness.

### Acceptance Criteria

- AC-1: A duplicate notification retry for the same tenant/channel/provider
  returns the prior result without sending again.
- AC-2: A timeout followed by provider failover cannot deliver the same
  notification twice.
- AC-3: An SMS fallback is blocked when the user has suppressed SMS for the
  topic, even if the original email channel was allowed.
- AC-4: Template rendering uses locale, version, and privacy classification in
  the cache boundary.
- AC-5: Delivery audit events include enough dimensions to reconstruct
  provider failover and suppression decisions.
- AC-6: The test suite covers the cross-boundary cases above.

## Spec Hash

`spec-notification-failover-v5-a91c2`
