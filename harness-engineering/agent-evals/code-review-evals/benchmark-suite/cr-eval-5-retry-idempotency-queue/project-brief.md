# Retry Idempotency Queue - Project Brief

## Overview

A partner delivery worker consumes payment and fulfillment messages from a
partitioned queue. The worker is responsible for bounded retries, idempotent
side effects, poison-message isolation, rebalance safety, backpressure, and
audit evidence that lets operators distinguish duplicates from replay,
retries, and new deliveries.

This eval is intentionally focused on Code Review depth. The code is locally
plausible and the happy-path tests pass, but production failures emerge only
when retry windows, idempotency TTLs, consumer rebalances, poison messages, and
downstream degradation interact.

## Requirements

### Functional Requirements

1. Transient downstream failures retry with bounded exponential backoff, jitter,
   and a hard maximum attempt count.
2. Idempotency keys suppress duplicate side effects across the entire partner
   replay window, including delayed retries and queue redelivery.
3. Permanent decode or validation failures are quarantined to a dead-letter
   sink without blocking the tenant partition.
4. Partition rebalances never allow an old and new consumer owner to execute
   the same side effect outside an idempotent sink boundary.
5. Backpressure applies to both fresh fetches and retry scheduling so degraded
   dependencies cannot create an unbounded in-memory retry queue.
6. Delivery logs and metrics include attempt number, idempotency key, tenant,
   partition, replay classification, and DLQ result.
7. Tests must cover retry caps, idempotency windows, poison-message isolation,
   rebalance replay, and degraded-downstream backpressure.

### Acceptance Criteria

- AC-1: Successful deliveries record a receipt and are deduped on replay.
- AC-2: Transient failures schedule a retry without exceeding retry budgets.
- AC-3: Idempotency windows are at least as long as the documented partner
  replay window.
- AC-4: Poison messages move to a DLQ and do not stall later partition work.
- AC-5: Rebalance and replay cases do not duplicate side effects.
- AC-6: Backpressure prevents unbounded retry growth while downstream is
  degraded.
- AC-7: Observability exposes the fields required to reconstruct retry and
  dedupe decisions.
- AC-8: Correct bounded backpressure and idempotent duplicate-return helpers
  are valid and should not be flagged as defects.

## Spec Hash

`spec-retry-idempotency-queue-v1-mno345`
