# Decomposition Draft

Candidate packages:

- Core/Foundation: app shell, config, env validation, shared DB/auth clients, CI/test harness.
- Billing Domain: owns invoices and subscriptions.
- Entitlements Domain: depends on Billing subscription status.
- Reporting Domain: needs foreign keys to Billing-owned invoices.
- Fulfillment Domain: consumes Entitlements events.

Invalid variants include putting billing tables into P0, sequencing Reporting parallel with Billing, and omitting Depends on entries.

Control variant: P0 contains only shell, runtime primitives, shared clients, and test harness bootstrap.
