/**
 * API Contract Spec: <feature-name>
 *
 * SPEC PACKAGE FILE: templates/spec-system/api.spec.ts
 * Part of the spec-system package. See templates/spec-system/ for all required files.
 *
 * Spec ID:      SPEC-<NNN>
 * Feature:      FEAT-<NNN>-<short-feature-name>
 * Version:      <semver>
 * Content Hash: <sha256 — recompute on every edit>
 * Last Edited:  <ISO-8601 UTC>
 *
 * PURPOSE: This file defines the API contract for this feature as TypeScript types.
 * It is the authoritative source of truth for:
 *   - Endpoint paths and HTTP methods
 *   - Request payload shapes
 *   - Response payload shapes
 *   - Error codes and their payloads
 *   - Authentication requirements
 *   - Rate limit policy
 *
 * This file is consumed by:
 *   - The TDD Agent (to write integration tests against the contract)
 *   - The Programmer Agent (to implement the endpoint)
 *   - The Architect Agent (to validate integration contracts)
 *   - The Code Review Agent (to verify implementation matches contract)
 */

// ---------------------------------------------------------------------------
// Endpoint Registry
// ---------------------------------------------------------------------------

/**
 * All endpoint paths and methods defined by this feature.
 * Add one entry per endpoint. Use route parameter syntax for dynamic segments.
 *
 * Example:
 *   GET_INVOICE:    { method: 'GET',    path: '/invoices/:invoiceId' }
 *   CREATE_INVOICE: { method: 'POST',   path: '/invoices' }
 *   DELETE_INVOICE: { method: 'DELETE', path: '/invoices/:invoiceId' }
 */
export const API_ENDPOINTS = {
  /** <one-line description of what this endpoint does> */
  EXAMPLE_ACTION: {
    method: 'POST' as const,
    path: '/api/v1/<resource>',
  },
  /** <one-line description> */
  EXAMPLE_GET: {
    method: 'GET' as const,
    path: '/api/v1/<resource>/:id',
  },
} as const;

export type ApiEndpoint = typeof API_ENDPOINTS[keyof typeof API_ENDPOINTS];

// ---------------------------------------------------------------------------
// Authentication & Authorization
// ---------------------------------------------------------------------------

/**
 * Authentication requirements for all endpoints in this feature.
 * Each endpoint entry must appear here. Omitting an endpoint here is an error.
 */
export const API_AUTH_REQUIREMENTS = {
  /**
   * EXAMPLE_ACTION requires:
   *   - Bearer JWT token in Authorization header
   *   - Token must include scope: "feature:write"
   *   - Roles permitted: ["admin", "editor"]
   */
  EXAMPLE_ACTION: {
    authRequired: true,
    tokenType: 'Bearer JWT' as const,
    requiredScopes: ['feature:write'],
    permittedRoles: ['admin', 'editor'],
  },
  /**
   * EXAMPLE_GET requires:
   *   - Bearer JWT token in Authorization header
   *   - Token must include scope: "feature:read"
   *   - Roles permitted: ["admin", "editor", "viewer"]
   */
  EXAMPLE_GET: {
    authRequired: true,
    tokenType: 'Bearer JWT' as const,
    requiredScopes: ['feature:read'],
    permittedRoles: ['admin', 'editor', 'viewer'],
  },
} as const;

// ---------------------------------------------------------------------------
// Rate Limits
// ---------------------------------------------------------------------------

/**
 * Rate limit policy per endpoint.
 * window: duration of the rate limit window in seconds
 * maxRequests: maximum number of requests allowed in the window per identity (user or API key)
 * burstAllowance: short burst above maxRequests before throttling kicks in (0 = no burst)
 * keyedBy: what the rate limit is keyed on ("userId" | "apiKey" | "ip" | "tenantId")
 */
export const API_RATE_LIMITS = {
  /** EXAMPLE_ACTION: write operations are rate-limited more aggressively */
  EXAMPLE_ACTION: {
    window: 60,         // seconds
    maxRequests: 30,
    burstAllowance: 5,
    keyedBy: 'userId' as const,
  },
  /** EXAMPLE_GET: read operations allow higher throughput */
  EXAMPLE_GET: {
    window: 60,         // seconds
    maxRequests: 300,
    burstAllowance: 50,
    keyedBy: 'userId' as const,
  },
} as const;

// ---------------------------------------------------------------------------
// Request Schemas
// ---------------------------------------------------------------------------

/**
 * Request body for EXAMPLE_ACTION (POST /api/v1/<resource>).
 *
 * All fields are required unless marked optional with `?`.
 * All string fields have explicit length constraints documented in the JSDoc.
 */
export interface ExampleActionRequest {
  /**
   * Unique identifier of the <parent resource> this action targets.
   * Format: UUID v4.
   * Example: "3f2c1a9e-45b2-4f88-9b3d-1234567890ab"
   */
  parentId: string;

  /**
   * Human-readable name for the created resource.
   * Min length: 1 character. Max length: 255 characters.
   * Must not be blank (whitespace-only strings are rejected).
   */
  name: string;

  /**
   * Optional configuration overrides. If omitted, defaults defined in
   * behavior.spec.md Default Values table are applied.
   */
  options?: ExampleActionOptions;
}

/**
 * Optional configuration block within ExampleActionRequest.
 */
export interface ExampleActionOptions {
  /**
   * Whether to notify subscribers on completion.
   * Default: true (see behavior.spec.md).
   */
  notifyOnComplete?: boolean;

  /**
   * Maximum number of retry attempts if the operation fails transiently.
   * Min: 0. Max: 5. Default: 3.
   */
  maxRetries?: number;
}

/**
 * Path parameters for EXAMPLE_GET (GET /api/v1/<resource>/:id).
 */
export interface ExampleGetPathParams {
  /**
   * Unique identifier of the resource to retrieve.
   * Format: UUID v4.
   */
  id: string;
}

/**
 * Query parameters for EXAMPLE_GET (GET /api/v1/<resource>/:id).
 * All query params are optional unless noted.
 */
export interface ExampleGetQueryParams {
  /**
   * If true, includes soft-deleted resources in the response.
   * Default: false. Only permitted for users with role "admin".
   */
  includeDeleted?: boolean;

  /**
   * Comma-separated list of fields to include in the response.
   * If omitted, the full object is returned.
   * Example: "id,name,status"
   */
  fields?: string;
}

// ---------------------------------------------------------------------------
// Response Schemas
// ---------------------------------------------------------------------------

/**
 * Successful response body for EXAMPLE_ACTION (201 Created).
 *
 * The response always contains the full representation of the created resource.
 * Partial responses are not returned for mutating operations.
 */
export interface ExampleActionResponse {
  /**
   * The newly created resource.
   */
  data: ExampleResource;

  /**
   * ISO-8601 UTC timestamp of when the resource was created server-side.
   * Example: "2026-02-23T14:00:00.000Z"
   */
  createdAt: string;

  /**
   * Correlation ID for distributed tracing. Matches the X-Correlation-ID
   * response header. Use this in bug reports and support tickets.
   */
  correlationId: string;
}

/**
 * Successful response body for EXAMPLE_GET (200 OK).
 */
export interface ExampleGetResponse {
  /**
   * The requested resource.
   */
  data: ExampleResource;

  /**
   * ISO-8601 UTC timestamp of the last modification to this resource.
   */
  lastModifiedAt: string;

  /**
   * ETag value for conditional requests (If-None-Match).
   * Format: W/"<hash>" (weak ETag).
   */
  etag: string;
}

/**
 * The canonical shape of a <resource> object returned by this API.
 * This type is the single source of truth for the API-visible resource shape.
 * Internal database representations may differ — only this shape is contractual.
 */
export interface ExampleResource {
  /** UUID v4. Immutable after creation. */
  id: string;

  /** UUID v4 of the parent resource. Immutable after creation. */
  parentId: string;

  /** Human-readable name. 1–255 characters. */
  name: string;

  /** Current lifecycle status of the resource. */
  status: ExampleResourceStatus;

  /** ISO-8601 UTC timestamp of creation. */
  createdAt: string;

  /** ISO-8601 UTC timestamp of last modification. */
  updatedAt: string;

  /**
   * Optional metadata block. Present only if the resource was created
   * with options, and only if the caller has scope "feature:read:meta".
   */
  metadata?: ExampleResourceMetadata;
}

/** Lifecycle status values for ExampleResource. */
export type ExampleResourceStatus =
  | 'pending'
  | 'active'
  | 'completed'
  | 'failed'
  | 'archived';

/**
 * Metadata block attached to a resource.
 * Only visible to callers with scope "feature:read:meta".
 */
export interface ExampleResourceMetadata {
  /** Number of retry attempts consumed so far. */
  retryCount: number;

  /** ISO-8601 UTC timestamp of the last retry attempt, or null if none. */
  lastRetryAt: string | null;

  /** Whether subscriber notifications were sent. */
  notified: boolean;
}

// ---------------------------------------------------------------------------
// Error Codes
// ---------------------------------------------------------------------------

/**
 * All error codes this API can return.
 *
 * Cross-reference: errors.spec.ts for full per-code payload definitions,
 * HTTP status mappings, and retry eligibility.
 *
 * Format: "<DOMAIN>_<CATEGORY>_<SPECIFIC>" in SCREAMING_SNAKE_CASE.
 */
export const API_ERROR_CODES = {
  /** The parentId does not refer to an existing parent resource. */
  PARENT_NOT_FOUND: 'PARENT_NOT_FOUND',

  /** The name field fails validation (blank, too short, or too long). */
  INVALID_NAME: 'INVALID_NAME',

  /** The caller does not have the required scope or role. */
  FORBIDDEN: 'FORBIDDEN',

  /** No valid authentication token was provided. */
  UNAUTHENTICATED: 'UNAUTHENTICATED',

  /** Rate limit exceeded for this caller. */
  RATE_LIMIT_EXCEEDED: 'RATE_LIMIT_EXCEEDED',

  /** The resource with the given id does not exist. */
  RESOURCE_NOT_FOUND: 'RESOURCE_NOT_FOUND',

  /** A resource with the same name already exists under this parent. */
  DUPLICATE_NAME: 'DUPLICATE_NAME',

  /** An unexpected server-side error occurred. Safe to retry. */
  INTERNAL_ERROR: 'INTERNAL_ERROR',
} as const;

export type ApiErrorCode = typeof API_ERROR_CODES[keyof typeof API_ERROR_CODES];

/**
 * Standard error response envelope returned for all non-2xx responses.
 * This shape is consistent across all endpoints in this feature.
 */
export interface ApiErrorResponse {
  /**
   * Machine-readable error code. Consumers switch on this field, not on
   * `message` (which is for humans and may change).
   */
  error: ApiErrorCode;

  /**
   * Human-readable description of the error. For display or logging only.
   * Do not parse this string programmatically.
   */
  message: string;

  /**
   * Optional field-level validation details.
   * Present when error is INVALID_NAME or similar validation errors.
   */
  details?: ApiErrorDetail[];

  /**
   * Correlation ID for distributed tracing. Matches the X-Correlation-ID
   * response header. Include this in support tickets.
   */
  correlationId: string;
}

/**
 * A single field-level validation error detail.
 */
export interface ApiErrorDetail {
  /** The request field path that failed validation. Example: "options.maxRetries" */
  field: string;

  /** A human-readable description of the validation failure. */
  reason: string;
}

// ---------------------------------------------------------------------------
// HTTP Status Mapping
// ---------------------------------------------------------------------------

/**
 * Maps each error code to the HTTP status code the API returns.
 * Defined here so the TDD Agent can assert on HTTP status in integration tests.
 */
export const API_ERROR_HTTP_STATUS: Record<ApiErrorCode, number> = {
  PARENT_NOT_FOUND:   404,
  INVALID_NAME:       422,
  FORBIDDEN:          403,
  UNAUTHENTICATED:    401,
  RATE_LIMIT_EXCEEDED: 429,
  RESOURCE_NOT_FOUND: 404,
  DUPLICATE_NAME:     409,
  INTERNAL_ERROR:     500,
};

// ---------------------------------------------------------------------------
// Idempotency
// ---------------------------------------------------------------------------

/**
 * Idempotency policy per endpoint.
 * supported: true means the endpoint accepts an Idempotency-Key header.
 * keyHeader: the header name used to pass the idempotency key.
 * ttl: how long (in seconds) an idempotency key is retained server-side.
 */
export const API_IDEMPOTENCY = {
  EXAMPLE_ACTION: {
    supported: true,
    keyHeader: 'Idempotency-Key',
    ttl: 86400, // 24 hours
  },
  EXAMPLE_GET: {
    supported: false,
  },
} as const;
