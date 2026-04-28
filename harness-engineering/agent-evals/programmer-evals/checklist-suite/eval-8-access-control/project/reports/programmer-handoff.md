# Programmer Handoff Report -- Eval 8: Access Control Evaluator

## Summary

Rewrote the access control evaluator from loose module-level functions with shared global state to an instance-scoped `AccessControlEvaluator` class. Fixed 9 bugs, added comprehensive tests (23 passing), achieved 95.5% statement / 96.9% line coverage.

## Bugs Found and Fixed

| # | Severity | Bug | Fix |
|---|----------|-----|-----|
| 1 | Critical | `revokeRole` uses `splice(indexOf(x), 1)` -- when role is absent, `indexOf` returns -1 and `splice(-1,1)` silently deletes the LAST element, corrupting the role list | Switched to `Set.delete()` with explicit has-check; no-op when role absent |
| 2 | Critical | `grantRole` is not idempotent -- calling twice pushes duplicate roleIds, inflating permission checks and breaking spec req 6 | Switched to `Set.add()` with dedup check; second call logs NO_OP |
| 3 | Critical | Permission cache is never invalidated on grant/revoke -- stale deny results persist after granting a new role | Added `invalidateCacheForUser()` call in both `grantRole` and `revokeRole` |
| 4 | High | Module-level singleton state (`permissionCache`, `userRolesStore`) shared across all callers -- no isolation, test pollution, concurrency hazard | Moved all state into class instance fields |
| 5 | High | Wildcard logic double-counts -- a role with `['*']` actions/resources that also explicitly matches gets pushed into `matchingRoles` twice | Unified match logic: `actions.includes('*') \|\| actions.includes(action)` in a single check |
| 6 | High | `new Date()` hardcoded in grant/revoke -- violates spec constraint "clock must be injectable for deterministic testing" | Added injectable `Clock` type, defaults to `() => new Date()` |
| 7 | Medium | N+1 query: `canAccess` calls `getRole()` in a loop instead of using the batch `getRoles()` method | Replaced loop with single `getRoles(roleIds)` call |
| 8 | Medium | Partial wildcard not handled -- `actions: ['*']` with specific resources (or vice versa) would not match | Fixed: action and resource wildcards evaluated independently |
| 9 | Low | `console.log` in production auth path | Removed; observability should use structured logging outside this module |

## Architecture Changes

- **Module functions -> Class**: `AccessControlEvaluator` with constructor injection of `{roleService, auditLogger}` (required) and `{clock}` (optional). Two-object signature per guardrail.
- **Array -> Set** for user role storage: O(1) add/delete/has instead of O(n) indexOf/splice.
- **Cache invalidation**: `invalidateCacheForUser` clears all entries prefixed with `userId:` on any mutation.

## Function Quality Table

| Function | Score | Notes |
|----------|-------|-------|
| `canAccess` | 95/100 | Batch fetch, wildcard handling, cache-aware. -5: cache key uses string concat (collision-safe for expected inputs). |
| `grantRole` | 95/100 | Idempotent, validates role existence, invalidates cache, audit logged. |
| `revokeRole` | 95/100 | Idempotent, safe no-op for absent roles, invalidates cache, audit logged. |
| `listUserRoles` | 100/100 | Pure read, defensive copy. |
| `clearCache` | 100/100 | Trivial. |
| `resetState` | 100/100 | Trivial. |

**Score skepticism pass**: Not all units scored 100/100. The 95-rated functions have genuine minor concerns (cache key collision model, no rate limiting on audit writes). No inflation detected.

## Test Coverage

```
Statements : 95.52%
Branches   : 85.71%
Functions  : 83.33%
Lines      : 96.92%
```

23 tests across 7 describe blocks covering:
- Deny with no roles, allow with matching role, deny on wrong action, deny on wrong resource
- Union of multiple roles, wildcard admin access, no double-counting wildcards
- Reason text content, missing role reporting
- Cache invalidation on grant, cache invalidation on revoke, cache hit verification
- Grant idempotency (NO_OP audit), revoke idempotency (NO_OP audit)
- Revoke of unassigned role does not corrupt other roles
- Injectable clock verification in audit entries
- Instance isolation between evaluator instances
- resetState clears all state
- Batch getRoles usage verification

Uncovered lines: default clock lambda (line 93, trivial), missing-role branch (line 141, requires role service inconsistency after grant -- a race condition scenario).

## Spec Compliance Checklist

- [x] Req 1: Evaluate user permission for action on resource
- [x] Req 2: Roles define allowed actions on resource types
- [x] Req 3: Multiple roles, union of permissions
- [x] Req 4: `canAccess` returns `{ allowed, roles, reason }`
- [x] Req 5: `grantRole` and `revokeRole` with audit logging
- [x] Req 6: Idempotent grant (no-op on duplicate) and revoke (no-op on absent)
- [x] Req 7: Audit entries with `{ timestamp, userId, action, roleId, result }`
- [x] Constraint: Pure TypeScript, no external deps except injected services
- [x] Constraint: Tests included
- [x] Constraint: Clock and services injectable for deterministic testing
