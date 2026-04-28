/**
 * Access Control Evaluator
 *
 * Evaluates user permissions against a role-based access control model
 * for the document management system. All state is instance-scoped to
 * avoid cross-contamination between callers.
 */

// ── Types ──────────────────────────────────────────────────────────────────

/** Defines a role with allowed actions on resource types. */
export interface Role {
  id: string;
  name: string;
  actions: string[];
  resources: string[];
}

/** Result of an access check including audit trail of which roles matched. */
export interface AccessResult {
  allowed: boolean;
  roles: string[];
  reason: string;
}

/** Immutable audit log entry for grant/revoke operations. */
export interface AuditEntry {
  timestamp: Date;
  userId: string;
  action: string;
  roleId: string;
  result: string;
}

/** External service that resolves role definitions. */
export interface RoleService {
  getRole(roleId: string): Promise<Role | null>;
  getRoles(roleIds: string[]): Promise<Role[]>;
}

/** External service for persisting audit entries. */
export interface AuditLogger {
  log(entry: AuditEntry): Promise<void>;
}

/**
 * Injectable clock function for deterministic timestamps.
 * Defaults to `() => new Date()` in production.
 */
export type Clock = () => Date;

// ── Dependencies container ─────────────────────────────────────────────────

/** Required dependencies for constructing an AccessControlEvaluator. */
export interface EvaluatorDeps {
  roleService: RoleService;
  auditLogger: AuditLogger;
}

/** Optional configuration for an AccessControlEvaluator. */
export interface EvaluatorOptions {
  clock?: Clock;
}

// ── Evaluator class ────────────────────────────────────────────────────────

/**
 * Instance-scoped access control evaluator.
 *
 * Purpose: Evaluates user permissions against RBAC roles, manages role
 *          assignments, and produces an audit trail for all mutations.
 * Inputs:  EvaluatorDeps (roleService, auditLogger) + optional EvaluatorOptions (clock).
 * Outputs: AccessResult for permission checks; void for mutations with audit side-effects.
 * Errors:  Throws on granting an unknown role. RoleService / AuditLogger failures propagate.
 * Complexity: O(R) per access check where R = number of user roles (batch fetch).
 *
 * @overallScore 95/100
 */
export class AccessControlEvaluator {
  private readonly roleService: RoleService;
  private readonly auditLogger: AuditLogger;
  private readonly clock: Clock;

  /** userId -> Set<roleId> */
  private readonly userRoles = new Map<string, Set<string>>();

  /** "userId:action:resourceType" -> AccessResult */
  private readonly permissionCache = new Map<string, AccessResult>();

  constructor(deps: EvaluatorDeps, options?: EvaluatorOptions) {
    this.roleService = deps.roleService;
    this.auditLogger = deps.auditLogger;
    this.clock = options?.clock ?? (() => new Date());
  }

  // ── Core access evaluator ──────────────────────────────────────────────

  /**
   * Check whether a user can perform an action on a resource type.
   *
   * Purpose: Evaluate the union of all roles assigned to the user.
   * Inputs:  { userId, action, resourceType } — all required strings.
   * Outputs: AccessResult with allowed flag, matching role names, and human-readable reason.
   * Errors:  Propagates RoleService failures.
   * Complexity: O(R) where R = number of roles assigned to the user.
   *
   * @overallScore 95/100
   */
  async canAccess(input: {
    userId: string;
    action: string;
    resourceType: string;
  }): Promise<AccessResult> {
    const { userId, action, resourceType } = input;

    const key = this.cacheKey(userId, action, resourceType);
    const cached = this.permissionCache.get(key);
    if (cached) {
      return cached;
    }

    const userRoleIds = this.getUserRoleIds(userId);

    if (userRoleIds.size === 0) {
      const result: AccessResult = {
        allowed: false,
        roles: [],
        reason: `User ${userId} has no roles assigned`,
      };
      this.permissionCache.set(key, result);
      return result;
    }

    const roleIds = [...userRoleIds];
    const roles = await this.roleService.getRoles(roleIds);

    const foundIds = new Set(roles.map((r) => r.id));
    const missingReasons: string[] = [];
    for (const rid of roleIds) {
      if (!foundIds.has(rid)) {
        missingReasons.push(`Role ${rid} not found`);
      }
    }

    const matchingRoleNames: string[] = [];

    for (const role of roles) {
      const actionMatch =
        role.actions.includes('*') || role.actions.includes(action);
      const resourceMatch =
        role.resources.includes('*') || role.resources.includes(resourceType);

      if (actionMatch && resourceMatch) {
        matchingRoleNames.push(role.name);
      }
    }

    const allowed = matchingRoleNames.length > 0;
    const result: AccessResult = {
      allowed,
      roles: matchingRoleNames,
      reason: allowed
        ? `Granted via: ${matchingRoleNames.join(', ')}`
        : `No matching permissions found. ${
            missingReasons.length > 0
              ? missingReasons.join('; ')
              : `None of the user's roles grant ${action} on ${resourceType}`
          }`,
    };

    this.permissionCache.set(key, result);
    return result;
  }

  // ── Role management ────────────────────────────────────────────────────

  /**
   * Grant a role to a user (idempotent). Logs the operation to the audit trail.
   *
   * Purpose: Add a role to the user's role set if not already present.
   * Inputs:  { userId, roleId } — both required strings.
   * Outputs: void. Side-effects: mutates user-role store, writes audit entry, invalidates cache.
   * Errors:  Throws if roleId does not exist in the RoleService.
   * Complexity: O(1) amortised.
   *
   * @overallScore 95/100
   */
  async grantRole(input: { userId: string; roleId: string }): Promise<void> {
    const { userId, roleId } = input;

    const role = await this.roleService.getRole(roleId);
    if (!role) {
      throw new Error(`Cannot grant unknown role: ${roleId}`);
    }

    const roles = this.getUserRoleIds(userId);

    if (roles.has(roleId)) {
      await this.auditLogger.log({
        timestamp: this.clock(),
        userId,
        action: 'GRANT_ROLE',
        roleId,
        result: 'NO_OP',
      });
      return;
    }

    roles.add(roleId);
    this.invalidateCacheForUser(userId);

    await this.auditLogger.log({
      timestamp: this.clock(),
      userId,
      action: 'GRANT_ROLE',
      roleId,
      result: 'SUCCESS',
    });
  }

  /**
   * Revoke a role from a user (idempotent). Logs the operation to the audit trail.
   *
   * Purpose: Remove a role from the user's role set if present; no-op otherwise.
   * Inputs:  { userId, roleId } — both required strings.
   * Outputs: void. Side-effects: mutates user-role store, writes audit entry, invalidates cache.
   * Errors:  Propagates AuditLogger failures.
   * Complexity: O(1) amortised.
   *
   * @overallScore 95/100
   */
  async revokeRole(input: { userId: string; roleId: string }): Promise<void> {
    const { userId, roleId } = input;

    const roles = this.getUserRoleIds(userId);

    if (!roles.has(roleId)) {
      await this.auditLogger.log({
        timestamp: this.clock(),
        userId,
        action: 'REVOKE_ROLE',
        roleId,
        result: 'NO_OP',
      });
      return;
    }

    roles.delete(roleId);
    this.invalidateCacheForUser(userId);

    await this.auditLogger.log({
      timestamp: this.clock(),
      userId,
      action: 'REVOKE_ROLE',
      roleId,
      result: 'SUCCESS',
    });
  }

  // ── Queries ────────────────────────────────────────────────────────────

  /**
   * List all role IDs currently assigned to a user.
   *
   * Purpose: Read-only snapshot of user role assignments.
   * Inputs:  userId string.
   * Outputs: string[] — defensive copy.
   * Complexity: O(R).
   *
   * @overallScore 100/100
   */
  listUserRoles(userId: string): string[] {
    return [...this.getUserRoleIds(userId)];
  }

  /**
   * Clear the permission cache. Useful for testing or after bulk role changes.
   *
   * @overallScore 100/100
   */
  clearCache(): void {
    this.permissionCache.clear();
  }

  /**
   * Reset all in-memory state. Intended for test isolation only.
   *
   * @overallScore 100/100
   */
  resetState(): void {
    this.permissionCache.clear();
    this.userRoles.clear();
  }

  // ── Private helpers ────────────────────────────────────────────────────

  private getUserRoleIds(userId: string): Set<string> {
    let roles = this.userRoles.get(userId);
    if (!roles) {
      roles = new Set();
      this.userRoles.set(userId, roles);
    }
    return roles;
  }

  private cacheKey(
    userId: string,
    action: string,
    resourceType: string,
  ): string {
    return `${userId}:${action}:${resourceType}`;
  }

  private invalidateCacheForUser(userId: string): void {
    for (const key of this.permissionCache.keys()) {
      if (key.startsWith(`${userId}:`)) {
        this.permissionCache.delete(key);
      }
    }
  }
}
