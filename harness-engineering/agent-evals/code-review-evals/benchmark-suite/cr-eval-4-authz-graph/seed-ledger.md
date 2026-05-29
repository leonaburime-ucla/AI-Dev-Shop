# Seed Ledger - cr-eval-4-authz-graph (CR Staff+)

**Eval ID**: benchmark-suite / cr-eval-4-authz-graph
**Purpose**: Test Code Review agent on multi-tenant authorization graph defects
that look locally correct but fail under delegation, cache, and policy-boundary
composition.
**Difficulty**: Hard - evidence is distributed across source, tests, project
brief, and fake Programmer handoff.

## Seeds

### SEED-CR-20

Cross-tenant delegated role traversal grants access when a delegated assignment
uses the same role ID as a tenant-local support role. Correct review flags that
direct tenant checks are present but delegated traversal loses tenant context.

Evidence: `src/authz_graph.py` (`_walk_delegations`, `can_access`) and
`tests/test_authz_graph.py` (same-tenant delegation only).

### SEED-CR-21

The authorization cache key omits tenant ID and policy version, and revocation
does not invalidate cached positive decisions. Correct review flags stale
positive grants as Required.

Evidence: `src/authz_graph.py` (`_decision_cache_key`, `revoke_assignment`).

### SEED-CR-22

`PolicyEnvelope.from_payload` treats missing `tenant_scope` as `*`, turning a
rolling-deploy compatibility gap into a wildcard policy grant. Correct review
flags runtime contract validation and deny-by-default behavior.

Evidence: `src/authz_graph.py` (`PolicyEnvelope.from_payload`) and fake handoff
compatibility claim.

### SEED-CR-23

Delegation traversal has no tenant prefilter, depth budget, or edge budget in
the production access path. Correct review distinguishes this from the safe
`bounded_role_walk` helper and flags scale collapse / DoS risk.

Evidence: `src/authz_graph.py` (`_walk_delegations`, `bounded_role_walk`).

### SEED-CR-24

Audit logs record a decision but omit policy version, traversal path, and tenant
boundary evidence. Correct review treats this as a security/forensics issue,
not a logging nicety.

Evidence: `src/authz_graph.py` (`AuditLog.record`, `can_access`) and fake
handoff audit claim.

### SEED-CR-25

Tests cover direct and shallow same-tenant delegation but omit cross-tenant
delegation, revoke/cache invalidation, missing tenant scope, and deep graph
cases. Correct review names those test gaps instead of accepting coverage
percentage.

Evidence: `tests/test_authz_graph.py` and fake handoff coverage claim.

### SEED-CR-26

Break-glass access can be cached past expiry. Correct review notices that the
expiry check lives inside direct permission evaluation, but `can_access` returns
cached positive decisions before that check can run again.

Evidence: `src/authz_graph.py` (`grant_break_glass`, `_decision_cache_key`,
`can_access`) and lack of post-expiry cache tests.

### SEED-CR-NC-03

The same-tenant break-glass role is time-bound, reasoned, and audited. Correct
review should not misflag it as cross-tenant escalation.

Evidence: `src/authz_graph.py` (`grant_break_glass`) and
`tests/test_authz_graph.py` (`test_break_glass_is_same_tenant_and_expiring`).

### SEED-CR-NC-04

`bounded_role_walk` is a safe helper with tenant filtering, visited tracking,
max-depth, and max-edge constraints. Correct review should not misflag it as
the unbounded traversal defect, though it may recommend using it in the
production access path.

Evidence: `src/authz_graph.py` (`bounded_role_walk`) and
`tests/test_authz_graph.py` (`test_bounded_walk_stops_at_max_depth`).

## Scoring Guide

| Score | Criteria |
|-------|----------|
| CAUGHT | CR identifies the seeded issue and its production/security consequence. |
| PARTIAL | CR identifies a related concern but misses the causal chain or severity. |
| MISSED | CR does not flag the issue. |
| FALSE_POSITIVE | CR flags a negative-control behavior as a defect. |
