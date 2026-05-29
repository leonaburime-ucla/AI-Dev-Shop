from __future__ import annotations

from datetime import datetime, timezone

from src.authz_graph import (
    AuditLog,
    AuthorizationGraph,
    Resource,
    RoleAssignment,
    bounded_role_walk,
)


def make_resource(tenant_id: str = "tenant-a") -> Resource:
    return Resource(
        id=f"{tenant_id}-case-001",
        tenant_id=tenant_id,
        resource_type="support_case",
        sensitivity="restricted",
    )


def test_direct_same_tenant_permission_allows_access() -> None:
    audit = AuditLog()
    graph = AuthorizationGraph(
        [
            RoleAssignment(
                user_id="agent-1",
                tenant_id="tenant-a",
                role_id="support_agent",
                permissions=frozenset({"case:read"}),
            )
        ],
        audit,
    )

    assert graph.can_access("agent-1", make_resource(), "case:read") is True
    assert audit.entries[-1].allowed is True


def test_direct_cross_tenant_assignment_is_denied() -> None:
    graph = AuthorizationGraph(
        [
            RoleAssignment(
                user_id="agent-1",
                tenant_id="tenant-b",
                role_id="support_agent",
                permissions=frozenset({"case:read"}),
            )
        ],
        AuditLog(),
    )

    assert graph.can_access("agent-1", make_resource("tenant-a"), "case:read") is False


def test_same_tenant_delegated_role_allows_access() -> None:
    graph = AuthorizationGraph(
        [
            RoleAssignment(
                user_id="agent-1",
                tenant_id="tenant-a",
                role_id="support_delegate",
                permissions=frozenset(),
            ),
            RoleAssignment(
                user_id="system",
                tenant_id="tenant-a",
                role_id="support_reader",
                permissions=frozenset({"case:read"}),
                delegated_from_role="support_delegate",
            ),
        ],
        AuditLog(),
    )

    assert graph.can_access("agent-1", make_resource("tenant-a"), "case:read") is True


def test_break_glass_is_same_tenant_and_expiring() -> None:
    audit = AuditLog()
    graph = AuthorizationGraph([], audit)
    graph.grant_break_glass(
        user_id="incident-lead",
        tenant_id="tenant-a",
        permission="case:read",
        reason="customer outage SEV-1",
        now=datetime.now(timezone.utc),
    )

    assert graph.can_access("incident-lead", make_resource("tenant-a"), "case:read") is True
    assert graph.can_access("incident-lead", make_resource("tenant-b"), "case:read") is False


def test_external_policy_payload_with_scope_allows_access() -> None:
    graph = AuthorizationGraph(
        [
            RoleAssignment(
                user_id="agent-1",
                tenant_id="tenant-a",
                role_id="support_agent",
                permissions=frozenset({"case:read"}),
            )
        ],
        AuditLog(),
    )

    assert (
        graph.can_access(
            "agent-1",
            make_resource("tenant-a"),
            "case:read",
            policy_payload={
                "policy_id": "support-read-v2",
                "version": 7,
                "tenant_scope": "tenant-a",
                "permissions": ["case:read"],
            },
        )
        is True
    )


def test_bounded_walk_stops_at_max_depth() -> None:
    assignments = [
        RoleAssignment(
            user_id="system",
            tenant_id="tenant-a",
            role_id="r1",
            permissions=frozenset(),
            delegated_from_role="r0",
        ),
        RoleAssignment(
            user_id="system",
            tenant_id="tenant-a",
            role_id="r2",
            permissions=frozenset(),
            delegated_from_role="r1",
        ),
        RoleAssignment(
            user_id="system",
            tenant_id="tenant-a",
            role_id="r3",
            permissions=frozenset(),
            delegated_from_role="r2",
        ),
    ]

    assert bounded_role_walk(assignments, "r0", "tenant-a", max_depth=1) == ["r1", "r2"]
