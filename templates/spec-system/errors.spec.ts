/**
 * Error Code Registry Spec: <feature-name>
 *
 * SPEC PACKAGE FILE: templates/spec-system/errors.spec.ts
 * Part of the spec-system package. See templates/spec-system/ for all required files.
 *
 * Spec ID:      SPEC-<NNN>
 * Feature:      FEAT-<NNN>-<short-feature-name>
 * Version:      <semver>
 * Content Hash: <sha256 — recompute on every edit>
 * Last Edited:  <ISO-8601 UTC>
 *
 * PURPOSE: This file is the single source of truth for all error codes, their
 * payloads, HTTP status mappings, retry eligibility, and user-facing message
 * guidance for this feature. It is the authoritative registry that:
 *   - Defines every error code as a const enum (for exhaustive switch coverage)
 *   - Defines the payload shape for each error code
 *   - Maps each error code to an HTTP status code
 *   - Declares whether each error is safe to retry automatically
 *   - Provides user-facing message guidance (what to say vs what not to say)
 *   - Documents which layer owns each error (API layer, orchestrator, client-side)
 *
 * This file is consumed by:
 *   - The TDD Agent (to write error path tests — one test per error code)
 *   - The Programmer Agent (to implement error production and handling)
 *   - The UI Agent (to map error codes to display messages)
 *   - The Code Review Agent (to verify every error path is covered)
 *   - api.spec.ts (ApiErrorCode references codes defined here)
 *
 * RULE: Every error code that can be thrown or returned by this feature MUST
 * appear in this file. An error that is not in this registry is not a valid
 * error for this feature.
 */

// ---------------------------------------------------------------------------
// Error Code Enum
// ---------------------------------------------------------------------------

/**
 * All error codes for this feature.
 *
 * Format: "<DOMAIN>_<CATEGORY>_<SPECIFIC>" in SCREAMING_SNAKE_CASE.
 * Domain: short identifier for the feature area (e.g., "INVOICE", "BATCH", "AUTH").
 * Category: class of error (e.g., "NOT_FOUND", "INVALID", "FORBIDDEN", "LIMIT").
 * Specific: optional further qualifier when category alone is ambiguous.
 *
 * Groups:
 *   1xx — Resource / entity errors (not found, conflict, stale)
 *   2xx — Validation errors (input shape, format, value constraints)
 *   3xx — Authorization errors (auth, permission, scope)
 *   4xx — External dependency errors (API, storage, network)
 *   5xx — Internal / unexpected errors
 *   6xx — Client-side / UI errors (no network, cancelled, timeout on client)
 *
 * NOTE: The numeric grouping is for documentation convention only — error codes
 * are strings, not numbers.
 */
export const ERROR_CODES = {
  // --- 1xx: Resource errors ---

  /**
   * The requested resource does not exist, or the caller does not have
   * permission to know it exists (ambiguous 404/403).
   */
  RESOURCE_NOT_FOUND: 'RESOURCE_NOT_FOUND',

  /**
   * The parent resource required for this operation does not exist.
   */
  PARENT_NOT_FOUND: 'PARENT_NOT_FOUND',

  /**
   * The operation would create a resource that conflicts with an existing one.
   * Example: duplicate name within the same parent.
   */
  RESOURCE_CONFLICT: 'RESOURCE_CONFLICT',

  /**
   * The resource was modified after the caller last read it.
   * Returned when an optimistic concurrency check fails.
   */
  RESOURCE_STALE: 'RESOURCE_STALE',

  // --- 2xx: Validation errors ---

  /**
   * The request body, query parameter, or path parameter fails validation.
   * The payload includes field-level details (see ErrorPayload.VALIDATION_ERROR).
   */
  VALIDATION_ERROR: 'VALIDATION_ERROR',

  /**
   * The name field is invalid — blank, too short, too long, or contains
   * disallowed characters.
   */
  INVALID_NAME: 'INVALID_NAME',

  /**
   * A field value is outside the allowed numeric range.
   * The payload specifies which field and the allowed bounds.
   */
  VALUE_OUT_OF_RANGE: 'VALUE_OUT_OF_RANGE',

  /**
   * A required field is absent from the request.
   */
  MISSING_REQUIRED_FIELD: 'MISSING_REQUIRED_FIELD',

  // --- 3xx: Authorization errors ---

  /**
   * No valid authentication credential was provided, or the credential has expired.
   */
  UNAUTHENTICATED: 'UNAUTHENTICATED',

  /**
   * The caller is authenticated but lacks the required permission or scope
   * for this operation.
   */
  FORBIDDEN: 'FORBIDDEN',

  /**
   * The caller has exceeded their rate limit for this endpoint.
   * The payload includes when the rate limit resets.
   */
  RATE_LIMIT_EXCEEDED: 'RATE_LIMIT_EXCEEDED',

  // --- 4xx: External dependency errors ---

  /**
   * An upstream service required for this operation returned an error.
   * The payload includes which dependency failed.
   * This error is retryable.
   */
  UPSTREAM_ERROR: 'UPSTREAM_ERROR',

  /**
   * An upstream service did not respond within the timeout window.
   * This error is retryable.
   */
  UPSTREAM_TIMEOUT: 'UPSTREAM_TIMEOUT',

  /**
   * The storage layer returned an error.
   * This error may be retryable depending on the storage error type.
   */
  STORAGE_ERROR: 'STORAGE_ERROR',

  // --- 5xx: Internal errors ---

  /**
   * An unexpected error occurred. Safe to retry — the server was not in
   * a known bad state. Correlation ID is always present.
   */
  INTERNAL_ERROR: 'INTERNAL_ERROR',

  /**
   * The feature is temporarily unavailable (e.g., maintenance mode, circuit breaker open).
   * Retryable after the retry-after interval in the response headers.
   */
  SERVICE_UNAVAILABLE: 'SERVICE_UNAVAILABLE',

  // --- 6xx: Client-side errors ---

  /**
   * The request was cancelled by the client (user navigated away, component unmounted).
   * Not an error in the traditional sense — should be handled silently.
   */
  REQUEST_CANCELLED: 'REQUEST_CANCELLED',

  /**
   * The client detected a network connectivity issue before the request was sent.
   * Retryable when connectivity is restored.
   */
  NETWORK_OFFLINE: 'NETWORK_OFFLINE',

  /**
   * The client-side timeout for this operation was exceeded before a response arrived.
   * Distinct from UPSTREAM_TIMEOUT (which is a server-side timeout).
   * Retryable.
   */
  CLIENT_TIMEOUT: 'CLIENT_TIMEOUT',
} as const;

export type ErrorCode = typeof ERROR_CODES[keyof typeof ERROR_CODES];

// ---------------------------------------------------------------------------
// Error Payload Interfaces
// ---------------------------------------------------------------------------

/**
 * Base payload shared by all errors.
 * Every error must include at minimum these fields.
 */
export interface BaseErrorPayload {
  /**
   * The error code. Consumers switch on this field.
   * Matches a key in ERROR_CODES.
   */
  code: ErrorCode;

  /**
   * Human-readable message. For logging and display guidance — do not parse programmatically.
   */
  message: string;

  /**
   * ISO-8601 UTC timestamp of when the error was created.
   */
  occurredAt: string;

  /**
   * Correlation ID for distributed tracing.
   * Always present for server-side errors.
   * null for client-side errors that never reached the server.
   */
  correlationId: string | null;
}

/**
 * Payload for VALIDATION_ERROR, INVALID_NAME, VALUE_OUT_OF_RANGE,
 * MISSING_REQUIRED_FIELD — any validation failure with field-level detail.
 */
export interface ValidationErrorPayload extends BaseErrorPayload {
  code:
    | typeof ERROR_CODES.VALIDATION_ERROR
    | typeof ERROR_CODES.INVALID_NAME
    | typeof ERROR_CODES.VALUE_OUT_OF_RANGE
    | typeof ERROR_CODES.MISSING_REQUIRED_FIELD;

  /**
   * One or more field-level errors.
   * At least one field must be present for a validation error to be meaningful.
   */
  fields: ValidationFieldError[];
}

/**
 * A single field-level validation error.
 */
export interface ValidationFieldError {
  /** The request field path. Dot-notation for nested fields. Example: "options.maxRetries". */
  field: string;

  /** A human-readable description of the validation failure. */
  reason: string;

  /**
   * For VALUE_OUT_OF_RANGE: the allowed min/max bounds.
   * Absent for other validation error types.
   */
  bounds?: {
    min?: number;
    max?: number;
  };
}

/**
 * Payload for RATE_LIMIT_EXCEEDED.
 * Includes when the rate limit resets so the client can back off.
 */
export interface RateLimitErrorPayload extends BaseErrorPayload {
  code: typeof ERROR_CODES.RATE_LIMIT_EXCEEDED;

  /**
   * ISO-8601 UTC timestamp of when the rate limit window resets.
   * The client should not retry before this time.
   */
  resetAt: string;

  /**
   * The number of seconds until the rate limit resets.
   * Convenience field — equivalent to (resetAt - now) in seconds.
   */
  retryAfterSeconds: number;
}

/**
 * Payload for UPSTREAM_ERROR and UPSTREAM_TIMEOUT.
 * Includes which dependency failed, to aid debugging without exposing internals.
 */
export interface UpstreamErrorPayload extends BaseErrorPayload {
  code:
    | typeof ERROR_CODES.UPSTREAM_ERROR
    | typeof ERROR_CODES.UPSTREAM_TIMEOUT;

  /**
   * Human-readable name of the upstream dependency that failed.
   * Example: "Payment gateway", "Storage service".
   * Must NOT expose internal hostnames, URLs, or implementation details.
   */
  dependency: string;
}

/**
 * Payload for RESOURCE_STALE.
 * Includes the current version so the client can re-fetch and retry.
 */
export interface ResourceStaleErrorPayload extends BaseErrorPayload {
  code: typeof ERROR_CODES.RESOURCE_STALE;

  /**
   * The resource ID that is stale.
   */
  resourceId: string;

  /**
   * The current server-side version of the resource.
   * The client should re-fetch this version before retrying the operation.
   */
  currentVersion: number;
}

/**
 * Union of all typed error payloads.
 * Errors not listed in specific payload types use BaseErrorPayload.
 */
export type AnyErrorPayload =
  | ValidationErrorPayload
  | RateLimitErrorPayload
  | UpstreamErrorPayload
  | ResourceStaleErrorPayload
  | BaseErrorPayload;

// ---------------------------------------------------------------------------
// HTTP Status Mapping
// ---------------------------------------------------------------------------

/**
 * Maps each error code to the HTTP status code returned by the API.
 *
 * Rules:
 *   - 400: malformed request (syntax error before business logic runs)
 *   - 401: unauthenticated (no valid credential)
 *   - 403: forbidden (authenticated but not permitted)
 *   - 404: resource not found (also used for permission-ambiguous not-found)
 *   - 409: conflict (resource state conflict)
 *   - 422: unprocessable entity (syntactically valid but semantically invalid)
 *   - 429: rate limit exceeded
 *   - 500: unexpected server error
 *   - 502: bad gateway / upstream error
 *   - 503: service unavailable
 *   - 504: gateway timeout / upstream timeout
 *
 * Client-side errors (6xx group) have no HTTP status — they never reach the server.
 * Use null for client-side errors.
 */
export const ERROR_HTTP_STATUS: Record<ErrorCode, number | null> = {
  RESOURCE_NOT_FOUND:      404,
  PARENT_NOT_FOUND:        404,
  RESOURCE_CONFLICT:       409,
  RESOURCE_STALE:          409,
  VALIDATION_ERROR:        422,
  INVALID_NAME:            422,
  VALUE_OUT_OF_RANGE:      422,
  MISSING_REQUIRED_FIELD:  422,
  UNAUTHENTICATED:         401,
  FORBIDDEN:               403,
  RATE_LIMIT_EXCEEDED:     429,
  UPSTREAM_ERROR:          502,
  UPSTREAM_TIMEOUT:        504,
  STORAGE_ERROR:           500,
  INTERNAL_ERROR:          500,
  SERVICE_UNAVAILABLE:     503,
  REQUEST_CANCELLED:       null,  // client-side only
  NETWORK_OFFLINE:         null,  // client-side only
  CLIENT_TIMEOUT:          null,  // client-side only
};

// ---------------------------------------------------------------------------
// Retry Eligibility
// ---------------------------------------------------------------------------

/**
 * Whether each error is safe to retry automatically without user intervention.
 *
 * Rules:
 *   - true: the same request can be retried — the failure was transient or environmental
 *   - false: retrying without a change will produce the same error
 *   - 'after-user-action': retryable only after the user takes a corrective action
 *     (e.g., re-authenticates, fixes input, refreshes stale data)
 */
export const ERROR_RETRY_ELIGIBILITY: Record<ErrorCode, boolean | 'after-user-action'> = {
  RESOURCE_NOT_FOUND:      false,
  PARENT_NOT_FOUND:        false,
  RESOURCE_CONFLICT:       false,
  RESOURCE_STALE:          'after-user-action',    // retry after re-fetch
  VALIDATION_ERROR:        'after-user-action',    // retry after fixing input
  INVALID_NAME:            'after-user-action',
  VALUE_OUT_OF_RANGE:      'after-user-action',
  MISSING_REQUIRED_FIELD:  'after-user-action',
  UNAUTHENTICATED:         'after-user-action',    // retry after re-auth
  FORBIDDEN:               false,
  RATE_LIMIT_EXCEEDED:     true,                   // retry after resetAt timestamp
  UPSTREAM_ERROR:          true,
  UPSTREAM_TIMEOUT:        true,
  STORAGE_ERROR:           true,                   // may be transient
  INTERNAL_ERROR:          true,
  SERVICE_UNAVAILABLE:     true,                   // retry after retry-after interval
  REQUEST_CANCELLED:       true,                   // re-issue if still needed
  NETWORK_OFFLINE:         true,                   // retry when connectivity restored
  CLIENT_TIMEOUT:          true,
};

// ---------------------------------------------------------------------------
// Error Ownership
// ---------------------------------------------------------------------------

/**
 * Which layer is responsible for producing each error.
 *
 * 'api'         — produced and returned by the server API layer
 * 'orchestrator' — produced by the client-side orchestrator (before or after API call)
 * 'client'      — produced by client-side code (network layer, timeout logic, cancel logic)
 *
 * Ownership determines where the error is created and where it should be caught first.
 */
export const ERROR_OWNERSHIP: Record<ErrorCode, 'api' | 'orchestrator' | 'client'> = {
  RESOURCE_NOT_FOUND:      'api',
  PARENT_NOT_FOUND:        'api',
  RESOURCE_CONFLICT:       'api',
  RESOURCE_STALE:          'api',
  VALIDATION_ERROR:        'api',
  INVALID_NAME:            'api',
  VALUE_OUT_OF_RANGE:      'api',
  MISSING_REQUIRED_FIELD:  'api',
  UNAUTHENTICATED:         'api',
  FORBIDDEN:               'api',
  RATE_LIMIT_EXCEEDED:     'api',
  UPSTREAM_ERROR:          'api',
  UPSTREAM_TIMEOUT:        'api',
  STORAGE_ERROR:           'api',
  INTERNAL_ERROR:          'api',
  SERVICE_UNAVAILABLE:     'api',
  REQUEST_CANCELLED:       'client',
  NETWORK_OFFLINE:         'client',
  CLIENT_TIMEOUT:          'client',
};

// ---------------------------------------------------------------------------
// User-Facing Message Guidance
// ---------------------------------------------------------------------------

/**
 * Guidance for human-readable messages shown to end users.
 *
 * Rules:
 *   - 'do' specifies what the message SHOULD communicate
 *   - 'dont' specifies what the message MUST NOT include
 *   - 'suggestedMessage' is a starting point — copywriters may refine tone
 *   - Messages must never expose internal system details, stack traces,
 *     database errors, or service names
 *
 * The Programmer Agent must implement message generation consistent with this guidance.
 * The Code Review Agent must reject messages that violate the 'dont' rules.
 */
export const ERROR_MESSAGE_GUIDANCE: Record<
  ErrorCode,
  { do: string; dont: string; suggestedMessage: string }
> = {
  RESOURCE_NOT_FOUND: {
    do: 'Tell the user the item could not be found and suggest they refresh.',
    dont: 'Do not reveal whether the resource exists for others or was deleted.',
    suggestedMessage: 'The item could not be found. It may have been deleted or moved.',
  },
  PARENT_NOT_FOUND: {
    do: 'Tell the user the context (parent) for this action no longer exists.',
    dont: 'Do not expose what the parent resource is internally called.',
    suggestedMessage: 'The context for this action no longer exists. Please refresh and try again.',
  },
  RESOURCE_CONFLICT: {
    do: 'Tell the user that an item with the same name already exists and ask them to use a different name.',
    dont: 'Do not expose the ID or owner of the conflicting resource.',
    suggestedMessage: 'An item with this name already exists. Please choose a different name.',
  },
  RESOURCE_STALE: {
    do: 'Tell the user the item was updated by someone else and ask them to refresh before retrying.',
    dont: 'Do not say "optimistic concurrency failure" or reference version numbers.',
    suggestedMessage: 'This item was recently updated. Please refresh the page and try again.',
  },
  VALIDATION_ERROR: {
    do: 'Show field-level errors for each field in the fields array.',
    dont: 'Do not show a generic "validation failed" message — always show specific field errors.',
    suggestedMessage: 'Please correct the errors above and try again.',
  },
  INVALID_NAME: {
    do: 'Tell the user the name is invalid and what the constraints are.',
    dont: 'Do not say "regex failed" or expose the validation rule as a pattern.',
    suggestedMessage: 'The name must be between 1 and 255 characters and cannot be blank.',
  },
  VALUE_OUT_OF_RANGE: {
    do: 'Tell the user the allowed range for the specific field.',
    dont: 'Do not say "out of bounds" without specifying the field and allowed range.',
    suggestedMessage: 'The value for {field} must be between {min} and {max}.',
  },
  MISSING_REQUIRED_FIELD: {
    do: 'Tell the user which field is required.',
    dont: 'Do not say "null pointer" or expose the internal field name if it differs from the UI label.',
    suggestedMessage: '{field} is required.',
  },
  UNAUTHENTICATED: {
    do: 'Tell the user their session has expired and redirect to sign-in.',
    dont: 'Do not show technical token expiry details or JWT errors.',
    suggestedMessage: 'Your session has expired. Please sign in again to continue.',
  },
  FORBIDDEN: {
    do: 'Tell the user they do not have permission for this action and suggest contacting an admin.',
    dont: 'Do not list the required permissions or roles.',
    suggestedMessage: 'You do not have permission to perform this action. Contact your administrator if you need access.',
  },
  RATE_LIMIT_EXCEEDED: {
    do: 'Tell the user they have made too many requests and when they can try again.',
    dont: 'Do not expose the rate limit quota or window duration.',
    suggestedMessage: 'Too many requests. Please wait a moment before trying again.',
  },
  UPSTREAM_ERROR: {
    do: 'Tell the user a dependency is temporarily unavailable and ask them to retry.',
    dont: 'Do not name the specific upstream service.',
    suggestedMessage: 'A required service is temporarily unavailable. Please try again in a moment.',
  },
  UPSTREAM_TIMEOUT: {
    do: 'Tell the user the request took too long and ask them to retry.',
    dont: 'Do not mention timeout values or service names.',
    suggestedMessage: 'The request took too long. Please try again.',
  },
  STORAGE_ERROR: {
    do: 'Tell the user something went wrong and ask them to retry.',
    dont: 'Do not mention databases, storage, or disk errors.',
    suggestedMessage: 'Something went wrong while saving. Please try again.',
  },
  INTERNAL_ERROR: {
    do: 'Tell the user something unexpected happened, provide the correlation ID for support, and ask them to retry.',
    dont: 'Do not expose stack traces, service names, or internal error messages.',
    suggestedMessage: 'Something unexpected happened. If the problem persists, contact support with reference: {correlationId}.',
  },
  SERVICE_UNAVAILABLE: {
    do: 'Tell the user the service is temporarily unavailable and when to try again if known.',
    dont: 'Do not expose deployment or maintenance details.',
    suggestedMessage: 'The service is temporarily unavailable. Please try again shortly.',
  },
  REQUEST_CANCELLED: {
    do: 'Handle silently — do not show an error message to the user.',
    dont: 'Do not display any toast or banner for a cancellation.',
    suggestedMessage: '(no user-facing message — handle silently)',
  },
  NETWORK_OFFLINE: {
    do: 'Tell the user their device is offline and to check connectivity.',
    dont: 'Do not show technical network error details.',
    suggestedMessage: 'You appear to be offline. Please check your connection and try again.',
  },
  CLIENT_TIMEOUT: {
    do: 'Tell the user the request timed out and ask them to try again.',
    dont: 'Do not expose client-side timeout configuration values.',
    suggestedMessage: 'The request timed out. Please try again.',
  },
};

// ---------------------------------------------------------------------------
// Error Coverage Requirements
// ---------------------------------------------------------------------------

/**
 * Requirements for test coverage of error paths.
 * The TDD Agent must write at least one test for each entry.
 */
export const ERROR_COVERAGE_REQUIREMENTS = {
  'Every error code in ERROR_CODES must have at least one test that produces it': true,
  'Every error code must be handled in the orchestrator (not silently swallowed)': true,
  'Every error code with isRetryable=true must have a retry test': true,
  'RATE_LIMIT_EXCEEDED must have a test verifying resetAt is surfaced to the consumer': true,
  'RESOURCE_STALE must have a test verifying the optimistic update is rolled back': true,
  'REQUEST_CANCELLED must have a test verifying no error is shown to the user': true,
  'INTERNAL_ERROR must have a test verifying correlationId is included in the error output': true,
  'VALIDATION_ERROR must have a test verifying field-level errors are surfaced correctly': true,
} as const;
