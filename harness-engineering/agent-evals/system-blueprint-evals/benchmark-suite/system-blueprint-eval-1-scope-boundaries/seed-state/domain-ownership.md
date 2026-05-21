# Domain Ownership Notes

- Billing owns invoices and subscription status.
- Entitlements owns feature access decisions but wants to share the subscription table directly.
- Fulfillment consumes entitlement events.
- CRM integration is required for onboarding handoff.

Expected behavior: mark subscription ownership ambiguity or choose one owner with explicit boundary rules; include CRM in integration map.
