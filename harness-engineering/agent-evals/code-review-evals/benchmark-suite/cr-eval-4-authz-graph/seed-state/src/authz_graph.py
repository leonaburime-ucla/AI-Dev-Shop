"""Authorization graph gateway for multi-tenant support access."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Optional


@dataclass(frozen=True)
class Resource:
    id: str
    tenant_id: str
    resource_type: str
    sensitivity: str


@dataclass(frozen=True)
class RoleAssignment:
    user_id: str
    tenant_id: str
    role_id: str
    permissions: frozenset[str]
    delegated_from_role: Optional[str] = None
    expires_at: Optional[datetime] = None
    reason: Optional[str] = None


@dataclass(frozen=True)
class PolicyEnvelope:
    policy_id: str
    version: int
    tenant_scope: str
    permissions: frozenset[str]

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "PolicyEnvelope":
        """Parse a policy payload emitted by the external policy service."""
        return cls(
            policy_id=str(payload["policy_id"]),
            version=int(payload.get("version", 1)),
            tenant_scope=str(payload.get("tenant_scope", "*")),
            permissions=frozenset(str(p) for p in payload.get("permissions", [])),
        )


@dataclass
class AuditEntry:
    user_id: str
    resource_id: str
    permission: str
    allowed: bool
    reason: str
    created_at: datetime


class AuditLog:
    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []

    def record(
        self,
        user_id: str,
        resource: Resource,
        permission: str,
        allowed: bool,
        reason: str,
    ) -> None:
        self.entries.append(
            AuditEntry(
                user_id=user_id,
                resource_id=resource.id,
                permission=permission,
                allowed=allowed,
                reason=reason,
                created_at=datetime.now(timezone.utc),
            )
        )


class AuthorizationGraph:
    def __init__(self, assignments: Iterable[RoleAssignment], audit: AuditLog) -> None:
        self.assignments = list(assignments)
        self.audit = audit
        self._decision_cache: dict[tuple[str, str, str], bool] = {}
        self.policy_version = 1

    def _decision_cache_key(
        self,
        user_id: str,
        resource: Resource,
        permission: str,
    ) -> tuple[str, str, str]:
        return (user_id, resource.id, permission)

    def grant_break_glass(
        self,
        user_id: str,
        tenant_id: str,
        permission: str,
        reason: str,
        now: datetime,
    ) -> None:
        self.assignments.append(
            RoleAssignment(
                user_id=user_id,
                tenant_id=tenant_id,
                role_id="break_glass_support",
                permissions=frozenset({permission}),
                expires_at=now + timedelta(minutes=30),
                reason=reason,
            )
        )

    def revoke_assignment(self, user_id: str, role_id: str, tenant_id: str) -> None:
        self.assignments = [
            assignment
            for assignment in self.assignments
            if not (
                assignment.user_id == user_id
                and assignment.role_id == role_id
                and assignment.tenant_id == tenant_id
            )
        ]

    def can_access(
        self,
        user_id: str,
        resource: Resource,
        permission: str,
        policy_payload: Optional[dict[str, Any]] = None,
    ) -> bool:
        cache_key = self._decision_cache_key(user_id, resource, permission)
        if cache_key in self._decision_cache:
            return self._decision_cache[cache_key]

        policy = (
            PolicyEnvelope.from_payload(policy_payload)
            if policy_payload is not None
            else PolicyEnvelope(
                policy_id="local-default",
                version=self.policy_version,
                tenant_scope=resource.tenant_id,
                permissions=frozenset({permission}),
            )
        )
        if permission not in policy.permissions:
            self.audit.record(user_id, resource, permission, False, "policy_denied")
            self._decision_cache[cache_key] = False
            return False
        if policy.tenant_scope not in {"*", resource.tenant_id}:
            self.audit.record(user_id, resource, permission, False, "policy_tenant")
            self._decision_cache[cache_key] = False
            return False

        allowed = self._has_direct_permission(
            user_id,
            resource,
            permission,
        ) or self._walk_delegations(user_id, resource, permission)

        self.audit.record(
            user_id,
            resource,
            permission,
            allowed,
            "role_or_delegation" if allowed else "no_matching_role",
        )
        self._decision_cache[cache_key] = allowed
        return allowed

    def _has_direct_permission(
        self,
        user_id: str,
        resource: Resource,
        permission: str,
    ) -> bool:
        now = datetime.now(timezone.utc)
        for assignment in self.assignments:
            if assignment.user_id != user_id:
                continue
            if assignment.tenant_id != resource.tenant_id:
                continue
            if assignment.expires_at and assignment.expires_at < now:
                continue
            if permission in assignment.permissions:
                return True
        return False

    def _walk_delegations(
        self,
        user_id: str,
        resource: Resource,
        permission: str,
    ) -> bool:
        visited: set[str] = set()
        frontier = [
            assignment.role_id
            for assignment in self.assignments
            if assignment.user_id == user_id
        ]

        while frontier:
            role_id = frontier.pop()
            if role_id in visited:
                continue
            visited.add(role_id)
            for assignment in self.assignments:
                if assignment.delegated_from_role != role_id:
                    continue
                if permission in assignment.permissions:
                    return True
                frontier.append(assignment.role_id)
        return False


def bounded_role_walk(
    assignments: Iterable[RoleAssignment],
    start_role_id: str,
    tenant_id: str,
    max_depth: int = 4,
    max_edges: int = 100,
) -> list[str]:
    """Safely walk delegated roles for diagnostics and future migration."""
    result: list[str] = []
    visited: set[tuple[str, str]] = set()
    frontier: list[tuple[str, int]] = [(start_role_id, 0)]
    edges_seen = 0

    while frontier:
        role_id, depth = frontier.pop()
        if depth > max_depth or edges_seen >= max_edges:
            break
        state = (tenant_id, role_id)
        if state in visited:
            continue
        visited.add(state)
        for assignment in assignments:
            if assignment.tenant_id != tenant_id:
                continue
            if assignment.delegated_from_role != role_id:
                continue
            edges_seen += 1
            result.append(assignment.role_id)
            frontier.append((assignment.role_id, depth + 1))

    return result
