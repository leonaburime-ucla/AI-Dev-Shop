# Webhook Signature Rotation - Project Brief

## Overview

A multi-tenant webhook gateway verifies provider signatures for billing,
identity, and fulfillment callbacks. It supports tenant-specific signing keys,
timestamp tolerance, replay nonce caching, key rotation with a bounded grace
period, provider-specific body canonicalization, and audit logs for incident
response.

This eval is intentionally focused on Code Review depth. The verifier looks
security-conscious and the tests cover valid signatures, replay rejection, and
rotation happy paths, but production failures emerge only when tenant routing,
legacy key fallback, timestamp windows, raw body contracts, and audit evidence
interact.

## Requirements

### Functional Requirements

1. Tenant and provider key lookup must never trust unsigned payload fields.
2. Replay nonce caches must be scoped by tenant, provider, key version, and
   signature timestamp.
3. Timestamp tolerance rejects stale events and does not reopen replay windows
   through clock-skew logic.
4. Legacy signing keys are accepted only during an explicit bounded grace
   period after rotation.
5. HMAC verification uses the provider's exact signed bytes, not a locally
   reserialized body unless that provider explicitly signs canonical JSON.
6. Audit logs include tenant, provider, key version, canonicalization method,
   nonce, timestamp, and failure reason.
7. Tests must cover cross-tenant payload/header mismatch, stale and future
   timestamps, replay across tenants, post-grace legacy keys, raw-body
   canonicalization, and audit completeness.

### Acceptance Criteria

- AC-1: A valid same-tenant signature is accepted.
- AC-2: Replays are rejected inside the full timestamp tolerance window.
- AC-3: Legacy keys stop verifying immediately after the configured grace
  period expires.
- AC-4: Tenant/provider routing for key lookup is derived from trusted routing
  metadata, not unsigned body fields.
- AC-5: Provider-specific canonicalization matches each provider contract.
- AC-6: Verification failure audits are forensically useful.
- AC-7: The test suite covers adversarial tenant, replay, rotation, and
  canonicalization boundaries.
- AC-8: Constant-time comparison and bounded dual-key grace helpers are valid
  and should not be flagged as defects.

## Spec Hash

`spec-webhook-signature-rotation-v1-vwx234`
