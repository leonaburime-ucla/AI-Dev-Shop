import { createRateLimiter } from "../rate-limiter";

describe("createRateLimiter", () => {
  // ---------------------------------------------------------------------------
  // Construction validation
  // ---------------------------------------------------------------------------
  describe("input validation", () => {
    it("throws when windowMs is zero", () => {
      expect(() => createRateLimiter({ windowMs: 0, maxRequests: 10 })).toThrow(
        "windowMs must be a positive number",
      );
    });

    it("throws when windowMs is negative", () => {
      expect(() =>
        createRateLimiter({ windowMs: -1, maxRequests: 10 }),
      ).toThrow("windowMs must be a positive number");
    });

    it("throws when maxRequests is zero", () => {
      expect(() =>
        createRateLimiter({ windowMs: 1000, maxRequests: 0 }),
      ).toThrow("maxRequests must be a positive integer");
    });

    it("throws when maxRequests is fractional", () => {
      expect(() =>
        createRateLimiter({ windowMs: 1000, maxRequests: 2.5 }),
      ).toThrow("maxRequests must be a positive integer");
    });
  });

  // ---------------------------------------------------------------------------
  // checkLimit
  // ---------------------------------------------------------------------------
  describe("checkLimit", () => {
    it("returns allowed with full remaining for unknown client", () => {
      let tick = 1000;
      const limiter = createRateLimiter(
        { windowMs: 60_000, maxRequests: 5 },
        { now: () => tick },
      );

      const status = limiter.checkLimit("client-a");
      expect(status.allowed).toBe(true);
      expect(status.remaining).toBe(5);
      expect(status.resetAt).toBeInstanceOf(Date);
      expect(status.resetAt.getTime()).toBe(1000 + 60_000);
    });

    it("returns resetAt based on oldest timestamp in the window", () => {
      let tick = 1000;
      const limiter = createRateLimiter(
        { windowMs: 60_000, maxRequests: 5 },
        { now: () => tick },
      );

      limiter.recordRequest("c1"); // t=1000
      tick = 2000;
      limiter.recordRequest("c1"); // t=2000

      const status = limiter.checkLimit("c1");
      expect(status.resetAt.getTime()).toBe(1000 + 60_000);
    });
  });

  // ---------------------------------------------------------------------------
  // recordRequest
  // ---------------------------------------------------------------------------
  describe("recordRequest", () => {
    it("allows requests under the limit and decrements remaining", () => {
      let tick = 0;
      const limiter = createRateLimiter(
        { windowMs: 60_000, maxRequests: 3 },
        { now: () => tick },
      );

      const r1 = limiter.recordRequest("c1");
      expect(r1.allowed).toBe(true);
      expect(r1.remaining).toBe(2);

      tick = 100;
      const r2 = limiter.recordRequest("c1");
      expect(r2.allowed).toBe(true);
      expect(r2.remaining).toBe(1);

      tick = 200;
      const r3 = limiter.recordRequest("c1");
      expect(r3.allowed).toBe(true);
      expect(r3.remaining).toBe(0);
    });

    it("blocks requests at the limit", () => {
      let tick = 0;
      const limiter = createRateLimiter(
        { windowMs: 60_000, maxRequests: 2 },
        { now: () => tick },
      );

      limiter.recordRequest("c1");
      tick = 10;
      limiter.recordRequest("c1");
      tick = 20;

      const blocked = limiter.recordRequest("c1");
      expect(blocked.allowed).toBe(false);
      expect(blocked.remaining).toBe(0);
    });

    it("does not record timestamp when request is rejected", () => {
      let tick = 0;
      const limiter = createRateLimiter(
        { windowMs: 60_000, maxRequests: 1 },
        { now: () => tick },
      );

      limiter.recordRequest("c1"); // fills the limit
      tick = 10;
      limiter.recordRequest("c1"); // rejected — should not store

      const stats = limiter.getStats();
      expect(stats.totalRequests).toBe(1); // only the one that was allowed
    });
  });

  // ---------------------------------------------------------------------------
  // Sliding window expiry (deterministic, no setTimeout)
  // ---------------------------------------------------------------------------
  describe("sliding window expiry", () => {
    it("expires old timestamps after the window elapses", () => {
      let tick = 0;
      const limiter = createRateLimiter(
        { windowMs: 100, maxRequests: 2 },
        { now: () => tick },
      );

      limiter.recordRequest("c1"); // t=0
      tick = 10;
      limiter.recordRequest("c1"); // t=10

      // Both within window — should be blocked
      tick = 50;
      expect(limiter.checkLimit("c1").allowed).toBe(false);

      // Advance past the window for t=0 (windowMs=100, so t>100 expires t=0)
      tick = 101;
      const status = limiter.checkLimit("c1");
      expect(status.allowed).toBe(true);
      expect(status.remaining).toBe(1); // t=10 is still valid
    });

    it("fully expires a client and removes them from stats", () => {
      let tick = 0;
      const limiter = createRateLimiter(
        { windowMs: 100, maxRequests: 5 },
        { now: () => tick },
      );

      limiter.recordRequest("c1"); // t=0
      tick = 200; // well past the window

      const stats = limiter.getStats();
      expect(stats.activeClients).toBe(0);
      expect(stats.totalRequests).toBe(0);
    });
  });

  // ---------------------------------------------------------------------------
  // reset
  // ---------------------------------------------------------------------------
  describe("reset", () => {
    it("clears a specific client's history", () => {
      let tick = 0;
      const limiter = createRateLimiter(
        { windowMs: 60_000, maxRequests: 2 },
        { now: () => tick },
      );

      limiter.recordRequest("c1");
      limiter.recordRequest("c1");
      expect(limiter.checkLimit("c1").allowed).toBe(false);

      limiter.reset("c1");
      const after = limiter.checkLimit("c1");
      expect(after.allowed).toBe(true);
      expect(after.remaining).toBe(2);
    });

    it("does not affect other clients", () => {
      let tick = 0;
      const limiter = createRateLimiter(
        { windowMs: 60_000, maxRequests: 2 },
        { now: () => tick },
      );

      limiter.recordRequest("c1");
      limiter.recordRequest("c2");
      limiter.reset("c1");

      expect(limiter.getStats().activeClients).toBe(1);
      expect(limiter.checkLimit("c2").remaining).toBe(1);
    });

    it("is a no-op for an unknown client", () => {
      const limiter = createRateLimiter(
        { windowMs: 60_000, maxRequests: 5 },
        { now: () => 0 },
      );
      // Should not throw
      limiter.reset("nonexistent");
      expect(limiter.getStats().activeClients).toBe(0);
    });
  });

  // ---------------------------------------------------------------------------
  // getStats
  // ---------------------------------------------------------------------------
  describe("getStats", () => {
    it("returns zero counts when empty", () => {
      const limiter = createRateLimiter(
        { windowMs: 60_000, maxRequests: 10 },
        { now: () => 0 },
      );

      const stats = limiter.getStats();
      expect(stats.activeClients).toBe(0);
      expect(stats.totalRequests).toBe(0);
    });

    it("counts across multiple clients", () => {
      let tick = 0;
      const limiter = createRateLimiter(
        { windowMs: 60_000, maxRequests: 100 },
        { now: () => tick },
      );

      limiter.recordRequest("c1");
      tick = 1;
      limiter.recordRequest("c2");
      tick = 2;
      limiter.recordRequest("c2");

      const stats = limiter.getStats();
      expect(stats.activeClients).toBe(2);
      expect(stats.totalRequests).toBe(3);
    });

    it("excludes expired entries from counts", () => {
      let tick = 0;
      const limiter = createRateLimiter(
        { windowMs: 100, maxRequests: 100 },
        { now: () => tick },
      );

      limiter.recordRequest("c1"); // t=0
      tick = 50;
      limiter.recordRequest("c2"); // t=50

      tick = 101; // c1's request at t=0 is expired, c2's at t=50 is still valid
      const stats = limiter.getStats();
      expect(stats.activeClients).toBe(1);
      expect(stats.totalRequests).toBe(1);
    });
  });

  // ---------------------------------------------------------------------------
  // Defaults (no options object)
  // ---------------------------------------------------------------------------
  describe("defaults", () => {
    it("works without options object (uses real clock)", () => {
      const limiter = createRateLimiter({ windowMs: 60_000, maxRequests: 10 });
      const result = limiter.recordRequest("c1");
      expect(result.allowed).toBe(true);
      expect(result.remaining).toBe(9);
      expect(result.resetAt.getTime()).toBeGreaterThan(0);
    });
  });

  // ---------------------------------------------------------------------------
  // Edge / boundary cases
  // ---------------------------------------------------------------------------
  describe("edge cases", () => {
    it("boundary: timestamp exactly at windowMs is expired", () => {
      let tick = 0;
      const limiter = createRateLimiter(
        { windowMs: 100, maxRequests: 5 },
        { now: () => tick },
      );

      limiter.recordRequest("c1"); // t=0
      tick = 100; // exactly windowMs later — t=0 should be expired (0 <= 100-100)
      const status = limiter.checkLimit("c1");
      expect(status.remaining).toBe(5);
      expect(status.allowed).toBe(true);
    });

    it("handles maxRequests of 1", () => {
      let tick = 0;
      const limiter = createRateLimiter(
        { windowMs: 1000, maxRequests: 1 },
        { now: () => tick },
      );

      const r1 = limiter.recordRequest("c1");
      expect(r1.allowed).toBe(true);
      expect(r1.remaining).toBe(0);

      tick = 500;
      const r2 = limiter.recordRequest("c1");
      expect(r2.allowed).toBe(false);

      tick = 1001;
      const r3 = limiter.recordRequest("c1");
      expect(r3.allowed).toBe(true);
    });

    it("handles many clients independently", () => {
      let tick = 0;
      const limiter = createRateLimiter(
        { windowMs: 60_000, maxRequests: 1 },
        { now: () => tick },
      );

      for (let i = 0; i < 50; i++) {
        tick = i;
        const result = limiter.recordRequest(`client-${i}`);
        expect(result.allowed).toBe(true);
      }

      const stats = limiter.getStats();
      expect(stats.activeClients).toBe(50);
      expect(stats.totalRequests).toBe(50);
    });
  });
});
