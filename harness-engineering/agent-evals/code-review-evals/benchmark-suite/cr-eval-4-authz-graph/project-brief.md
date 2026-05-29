# Authz Graph Gateway - Project Brief

## Overview

A multi-tenant authorization gateway evaluates whether support and operations
users can access customer resources. The gateway combines direct role
assignments, delegated support roles, break-glass emergency access, policy
payloads from an external policy service, and an audit log used by incident
response.

This eval is intentionally focused on Code Review depth. The code is
professional-looking and locally plausible, but several production failures
emerge only when tenant boundaries, delegation graphs, cache invalidation, and
external policy payloads interact.

## Requirements

### Functional Requirements

1. Direct role assignments grant permissions only inside the assignment tenant.
2. Delegated support roles may grant permissions only when every edge in the
   delegation path stays inside the resource tenant.
3. Break-glass access is allowed only when tenant-scoped, unexpired, and
   accompanied by a reason for audit.
4. Policy payloads from the policy service must be deny-by-default when tenant
   scope is missing or malformed.
5. Authorization decisions may be cached, but cache keys and invalidation must
   include tenant and policy-version boundaries.
6. Authorization audit logs must allow incident responders to reconstruct the
   path, tenant, permission, and policy version that produced an allowed
   decision.
7. Delegation traversal must remain bounded by tenant, max depth, and max edge
   count so imported enterprise role graphs cannot collapse the service.

### Acceptance Criteria

- AC-1: Direct same-tenant role assignment grants allowed permissions.
- AC-2: Direct cross-tenant role assignment never grants access.
- AC-3: Delegated support access never crosses tenant boundaries.
- AC-4: Revoked assignments and policy-version changes invalidate positive
  authorization decisions.
- AC-5: Missing tenant scope in external policy payloads denies access.
- AC-6: Audit entries include decision path and policy version for allowed
  access.
- AC-7: Delegation traversal has explicit tenant, depth, and edge constraints.
- AC-8: Same-tenant break-glass access with expiry, reason, and audit metadata
  is valid and should not be flagged as a defect.

## Spec Hash

`spec-authz-graph-v1-jkl012`
