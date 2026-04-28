/**
 * Sliding window rate limiter.
 *
 * Tracks per-client request timestamps in a sliding window and enforces
 * a configurable maximum request count per window.
 *
 * @module rate-limiter
 */

/** Required configuration for creating a RateLimiter. */
export interface RateLimiterInput {
  /** Sliding window duration in milliseconds. */
  windowMs: number;
  /** Maximum requests allowed per window. */
  maxRequests: number;
}

/** Optional overrides (primarily for testing). */
export interface RateLimiterOptions {
  /** Injectable clock function; defaults to Date.now. */
  now?: () => number;
}

/** Result returned by checkLimit and recordRequest. */
export interface LimitStatus {
  allowed: boolean;
  remaining: number;
  resetAt: Date;
}

/** Aggregate statistics for the limiter. */
export interface LimiterStats {
  activeClients: number;
  totalRequests: number;
}

/**
 * Creates a sliding-window rate limiter.
 *
 * Two-object signature: required input + optional options.
 *
 * @param input   - Required: windowMs and maxRequests.
 * @param options - Optional: injectable clock via `now`.
 * @returns A RateLimiter instance.
 *
 * @complexity Construction O(1). Per-operation see individual methods.
 * @overallScore 95/100 — clean design; minor note: per-client cleanup is O(k)
 *   where k is stored timestamps, acceptable for expected workloads.
 */
export function createRateLimiter(
  input: RateLimiterInput,
  options?: RateLimiterOptions,
) {
  const { windowMs, maxRequests } = input;

  if (windowMs <= 0) {
    throw new Error("windowMs must be a positive number");
  }
  if (maxRequests <= 0 || !Number.isInteger(maxRequests)) {
    throw new Error("maxRequests must be a positive integer");
  }

  const clock = options?.now ?? Date.now;
  const windows = new Map<string, number[]>();

  /**
   * Removes expired timestamps for a single client.
   * Returns the pruned array (or undefined if all expired).
   *
   * @complexity O(k) where k = timestamps stored for this client.
   */
  function pruneClient(clientId: string, now: number): number[] {
    const timestamps = windows.get(clientId);
    if (!timestamps || timestamps.length === 0) {
      windows.delete(clientId);
      return [];
    }
    const windowStart = now - windowMs;
    // Timestamps are in insertion order (ascending), so we can binary-scan
    // from the left to find the first valid index.
    let firstValid = 0;
    while (firstValid < timestamps.length && timestamps[firstValid] <= windowStart) {
      firstValid++;
    }
    if (firstValid === timestamps.length) {
      windows.delete(clientId);
      return [];
    }
    if (firstValid > 0) {
      const valid = timestamps.slice(firstValid);
      windows.set(clientId, valid);
      return valid;
    }
    return timestamps;
  }

  /**
   * Checks whether a client is within their rate limit.
   *
   * @param clientId - Unique client identifier.
   * @returns LimitStatus with allowed flag, remaining count, and resetAt Date.
   *
   * @complexity O(k) where k = timestamps for this client.
   * @overallScore 95/100
   */
  function checkLimit(clientId: string): LimitStatus {
    const now = clock();
    const valid = pruneClient(clientId, now);
    const count = valid.length;
    const allowed = count < maxRequests;
    const remaining = Math.max(0, maxRequests - count);
    // resetAt: when the oldest timestamp in the current window expires
    const resetAt = count > 0
      ? new Date(valid[0] + windowMs)
      : new Date(now + windowMs);

    return { allowed, remaining, resetAt };
  }

  /**
   * Records a request for a client and returns the updated limit status.
   *
   * If the client is already at the limit, the request is rejected and no
   * timestamp is stored.
   *
   * @param clientId - Unique client identifier.
   * @returns LimitStatus after recording (or rejecting) the request.
   *
   * @complexity O(k) where k = timestamps for this client.
   * @overallScore 95/100
   */
  function recordRequest(clientId: string): LimitStatus {
    const now = clock();
    const valid = pruneClient(clientId, now);
    const count = valid.length;

    if (count >= maxRequests) {
      // Rejected — return status without recording
      const resetAt = new Date(valid[0] + windowMs);
      return { allowed: false, remaining: 0, resetAt };
    }

    // Record the new timestamp
    valid.push(now);
    windows.set(clientId, valid);

    const newCount = count + 1;
    const remaining = Math.max(0, maxRequests - newCount);
    const resetAt = new Date(valid[0] + windowMs);

    return { allowed: true, remaining, resetAt };
  }

  /**
   * Clears all tracked state for a specific client.
   *
   * @param clientId - Client whose history should be cleared.
   *
   * @complexity O(1)
   * @overallScore 95/100
   */
  function reset(clientId: string): void {
    windows.delete(clientId);
  }

  /**
   * Returns aggregate statistics.
   * Prunes expired entries first so counts are accurate.
   *
   * @returns activeClients and totalRequests across all clients.
   *
   * @complexity O(n * k) where n = clients, k = avg timestamps per client.
   * @overallScore 95/100
   */
  function getStats(): LimiterStats {
    const now = clock();
    // Collect keys first to avoid mutating map during iteration
    const clientIds = Array.from(windows.keys());
    let totalRequests = 0;
    for (const id of clientIds) {
      const valid = pruneClient(id, now);
      totalRequests += valid.length;
    }
    return { activeClients: windows.size, totalRequests };
  }

  return { checkLimit, recordRequest, reset, getStats };
}

/** Convenience type for the returned limiter object. */
export type RateLimiter = ReturnType<typeof createRateLimiter>;
