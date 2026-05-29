# Seed Ledger - cr-eval-5-retry-idempotency-queue (CR Staff+)

**Eval ID**: benchmark-suite / cr-eval-5-retry-idempotency-queue
**Purpose**: Test Code Review agent on retry, idempotency, poison-message,
rebalance, and backpressure defects that pass local queue-worker tests but fail
under production delivery and replay conditions.
**Difficulty**: Hard - evidence is distributed across source, tests, project
brief, and fake Programmer handoff.

## Seeds

### SEED-CR-27

Retry scheduling uses exponential delay but ignores the configured cap and
jitter. Correct review flags retry amplification under shared partner outages.

Evidence: `src/retry_queue.py` (`RetryPolicy.delay_for`,
`QueueConsumer._schedule_retry`) and the handoff claim that retries are capped
and jittered.

### SEED-CR-28

The idempotency retention window is shorter than the documented partner replay
window, so delayed replay can execute a second side effect after the dedupe
record expires. Correct review treats this as a data-loss/duplicate-effect
window, not a harmless cache TTL.

Evidence: `src/retry_queue.py` (`IdempotencyStore`, `QueueConsumer`) and
`project-brief.md` (AC-3).

### SEED-CR-29

Permanent message failures are put back on the retry path instead of being
quarantined to the DLQ, blocking partition progress behind poison messages.
Correct review distinguishes this from the max-attempt transient DLQ path.

Evidence: `src/retry_queue.py` (`QueueConsumer.process_batch`) and
`tests/test_retry_queue.py` (no permanent-failure path).

### SEED-CR-30

Side effects are executed before the consumer checkpoint is fenced by the
current partition owner epoch. Correct review flags duplicate effects during
rebalance or replay, even though single-consumer tests pass.

Evidence: `src/retry_queue.py` (`QueueConsumer.process_batch`,
`QueueConsumer.claim_partitions`, `_ack`).

### SEED-CR-31

Backpressure pauses fresh fetches but retry scheduling continues to append to an
in-memory retry queue. Correct review flags resource exhaustion during degraded
downstream periods.

Evidence: `src/retry_queue.py` (`BackpressureMonitor`,
`QueueConsumer._schedule_retry`).

### SEED-CR-32

Delivery events record success, retry, and DLQ outcomes but omit idempotency
key, attempt ID, tenant, partition owner epoch, and replay classification.
Correct review treats this as an operational forensic gap.

Evidence: `src/retry_queue.py` (`QueueConsumer.events`) and fake handoff
observability claim.

### SEED-CR-33

Tests cover success, simple duplicates, and one transient retry but omit retry
jitter/cap, delayed replay after idempotency expiry, permanent poison messages,
rebalance duplicate effects, and backpressure retry growth.

Evidence: `tests/test_retry_queue.py` and fake handoff coverage claim.

### SEED-CR-NC-05

`BackpressureMonitor` is a bounded sliding-window helper that correctly signals
when fetches should pause. Correct review should not misflag it as message
dropping.

Evidence: `src/retry_queue.py` (`BackpressureMonitor`) and
`tests/test_retry_queue.py` (`test_backpressure_monitor_signals_pause`).

### SEED-CR-NC-06

`IdempotentReceiptCache` intentionally returns the prior receipt for duplicate
keys. Correct review should not misflag this as skipped delivery or lost work.

Evidence: `src/retry_queue.py` (`IdempotentReceiptCache`) and
`tests/test_retry_queue.py` (`test_idempotent_receipt_cache_returns_prior`).

## Scoring Guide

| Score | Criteria |
|-------|----------|
| CAUGHT | CR identifies the seeded issue and its production consequence. |
| PARTIAL | CR identifies a related concern but misses the causal chain or severity. |
| MISSED | CR does not flag the issue. |
| FALSE_POSITIVE | CR flags a negative-control behavior as a defect. |
