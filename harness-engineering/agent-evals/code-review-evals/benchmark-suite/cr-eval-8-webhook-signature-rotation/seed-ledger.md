# Seed Ledger - cr-eval-8-webhook-signature-rotation (CR Staff+)

**Eval ID**: benchmark-suite / cr-eval-8-webhook-signature-rotation
**Purpose**: Test Code Review agent on multi-tenant webhook verification,
signature rotation, replay prevention, canonicalization, and audit defects that
look locally security-conscious but fail across trust boundaries.
**Difficulty**: Hard - evidence is distributed across source, tests, project
brief, and fake Programmer handoff.

## Seeds

### SEED-CR-48

Tenant routing falls back to unsigned JSON payload fields when route metadata is
missing. Correct review flags cross-tenant signature verification through an
untrusted boundary.

Evidence: `src/webhook_rotation.py` (`WebhookVerifier._resolve_tenant`) and
`project-brief.md` (AC-4).

### SEED-CR-49

Replay nonce cache keys omit tenant and provider. Correct review flags
cross-tenant collision and replay-window confusion, even though single-tenant
replay tests pass.

Evidence: `src/webhook_rotation.py` (`NonceCache._cache_key`) and
`tests/test_webhook_rotation.py` (single tenant/provider).

### SEED-CR-50

Timestamp tolerance uses absolute clock skew and can accept future-dated events
that keep replay material valid longer than intended. Correct review flags the
temporal replay hazard.

Evidence: `src/webhook_rotation.py` (`WebhookVerifier._timestamp_allowed`) and
project timestamp requirements.

### SEED-CR-51

Legacy signing keys are tried whenever configured, even after the rotation grace
period expires. Correct review flags indefinite legacy-secret acceptance.

Evidence: `src/webhook_rotation.py` (`WebhookVerifier.verify`) and fake handoff
rotation claim.

### SEED-CR-52

The verifier canonicalizes JSON for every provider, including providers whose
contract signs the raw request body. Correct review flags the serialization
contract mismatch.

Evidence: `src/webhook_rotation.py` (`_bytes_to_sign`) and provider
requirements in `project-brief.md`.

### SEED-CR-53

Audit logs record verification result and provider but omit tenant source, key
version, nonce, timestamp, canonicalization method, and failure reason. Correct
review treats this as a security forensics defect.

Evidence: `src/webhook_rotation.py` (`AuditLog.record`) and fake handoff audit
claim.

### SEED-CR-54

Tests cover valid signatures, same-tenant replay, stale events, and in-grace
legacy keys but omit cross-tenant body/header mismatch, future timestamps,
post-grace legacy keys, raw-body signatures, and audit completeness.

Evidence: `tests/test_webhook_rotation.py` and fake handoff coverage claim.

### SEED-CR-NC-11

`constant_time_compare` uses `hmac.compare_digest` after a length check for
malformed input. Correct review should not misflag it as an avoidable timing
side channel for fixed-length HMACs.

Evidence: `src/webhook_rotation.py` (`constant_time_compare`) and
`tests/test_webhook_rotation.py` (`test_constant_time_compare_accepts_equal_digest`).

### SEED-CR-NC-12

`DualKeyGraceVerifier` accepts the old key only inside an explicit grace window.
Correct review should not misflag it as the indefinite legacy-secret fallback.

Evidence: `src/webhook_rotation.py` (`DualKeyGraceVerifier`) and
`tests/test_webhook_rotation.py` (`test_dual_key_grace_verifier_rejects_after_expiry`).

## Scoring Guide

| Score | Criteria |
|-------|----------|
| CAUGHT | CR identifies the seeded issue and its production/security consequence. |
| PARTIAL | CR identifies a related concern but misses the causal chain or severity. |
| MISSED | CR does not flag the issue. |
| FALSE_POSITIVE | CR flags a negative-control behavior as a defect. |
