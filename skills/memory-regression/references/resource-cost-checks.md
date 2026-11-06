# Memory Regression — Resource-Cost Checks (Design, Implementation, Review)

Seven checks for changes that add or alter recurring or retained work, plus the `Cost:` line that reports the result. Load with `SKILL.md` when a change hits a trigger in its When to Use list.

Roles: Software Architect proposes the bounds, Programmer implements them and reports the cost, Code Inspection verifies the path that actually runs. Apply the checks to the changed paths only. Reuse the project's existing scheduler, cache, sampler, and benchmark harness; do not build new ones for this ([Before You Write](../../implementation-guardrails/SKILL.md#before-you-write)).

Owned elsewhere, not restated here:
- Leak patterns (listeners, timers, unbounded caches, unsupervised workers): [antipatterns.md](antipatterns.md)
- Bounded-growth test protocol, forced GC, CI gating: [SKILL.md](../SKILL.md)
- Explicit dependencies, typed failures, deny-on-unknown: [coding-foundations](../../coding-foundations/SKILL.md)
- Scaling sanity checks, query fan-out, collection caps: [implementation-guardrails](../../implementation-guardrails/SKILL.md)
- Latency and throughput validation: [performance-engineering](../../performance-engineering/SKILL.md)

## 1. Calculate the recurring work

- Write the cost as frequency × payload size × copies or scans per run × concurrent consumers, plus the bytes kept afterwards.
- Count reads, serialization, query parameters, writes, and scanning CPU as separate costs. A poll that finds nothing changed still pays for its read and its scan.
- Saving a full snapshot of a growing record on every tick is quadratic in total: the n-th save rewrites everything saved before it. Prefer appends or deltas (check 3).
- When a stream is processed in chunks, the bytes carried between chunks and the overflow behavior both need a limit.
- Redact or sanitize data before it is retained or delivered, not afterwards.
- If a scanner (for example redaction) looks for patterns across chunk boundaries, test two cases. First, long input that never matches: the carried tail must stay bounded and scan time must stay linear. Second, a secret split across two chunks: bounding the carry must not let it through unredacted.

## 2. Read narrowly and check the physical work

- Request the smallest projection that answers the question: metadata for lists, full bodies only on a detail view, existence or aggregate queries for yes/no checks, bounded pages for history.
- Follow the read through storage and serialization. A narrow API response built from a full-row load is not a narrow read.
- `LIMIT 1` bounds the rows returned, not the rows searched. Check the real engine's query plan, especially for the no-match case against a large history of finished records.
- Add indexes through the normal migration path, and confirm a fresh install creates them too. Count the I/O of building the index and any writes it blocks while it builds.

## 3. Avoid repeated full JSON transforms

- Before loading and parsing a body, check a cheap signal such as a version, timestamp, or hash, and skip the work when nothing changed.
- Where the contract allows, use JSON already validated in storage, guarded deltas, or streaming with backpressure instead of parse, modify, and re-serialize.
- A delta path must keep these guarantees:
  - A full-merge fallback that stays authoritative when a delta cannot be applied safely.
  - Ordering points where a consumer must see the complete record before it continues.
  - Correct handling of a text field that keeps growing at its tail.
  - Concurrent-write detection, such as a version check on write.
  - Unicode safety: never split inside a multi-byte character or surrogate pair.
  - A terminal fence: once a record is final, a late delta cannot change it.
- Report "saved" or "persisted" only after the commit succeeds.
- Splicing text in SQL (for example a JSON-set or concatenation function) can still rewrite the whole row and its write-ahead log entry. That saves parsing, not I/O; count the I/O that remains.

## 4. Bound stores and prove a cache is worth having

Extends antipatterns #4 and #11.
- For every cache, queue, history, or buffer, name the key, owner, capacity (bytes, count, or age, as fits), lifetime, invalidation scope, cleanup, behavior on overflow, and the cost of a miss.
- A count cap does not bound memory when single entries can be arbitrarily large. Cap bytes as well, or cap entry size.
- A correct cache can save nothing if unrelated writes keep invalidating it. Measure hit and fallback rates under realistic concurrent use before claiming a saving.
- Respect durability and undo promises. Unless a deletion policy is authorized, a store holding durable work rejects or defers new work at capacity instead of evicting.

## 5. Schedule progress and fence teardown

Extends antipatterns #2 and #9.
- Coalesce writes: each owner has at most one pending write and one trailing timer.
- Choose the cadence by weighing payload cost against how much progress a crash may lose.
- After a write succeeds, or finds nothing changed, schedule the next one only if newer progress exists.
- Retry transient storage failures during quiet periods with a positive minimum delay and a bounded or backed-off policy, never a tight loop.
- On teardown, stop scheduling and clear timers before awaiting cleanup. A promise that resolves after teardown must not restart work for the retired owner.
- Persist the terminal state immediately; never throttle the final write.

## 6. Prove idle before reclaiming anything

Applies before stopping, sleeping, or recycling a process, worker, view, or connection.
- An HTTP response completing does not mean the work it started has finished. Publishing, exporting, uploading, and sending can continue afterwards.
- Hold an activity count per request and release it exactly once, on whichever of finish or close comes first.
- Ask every owner of background work whether it is busy, not just the request layer.
- After an asynchronous idle probe returns, check live activity again. Then close intake with no await between that check and the close, so new work cannot slip in before the graceful stop.
- A busy, failed, or unanswered probe defers reclamation.
- Cancel pending restart work on explicit stop, delete, or quit.
- When a process is replaced, the old process's exit handler must confirm identity before removing anything, so it cannot tear down its replacement's registration.

## 7. Measure comparable workloads against a budget

Extends the SKILL.md core protocol.
- Before claiming a saving, name the metric, units, process scope, runtime and flags, the supported workload, and the acceptance budget.
- Keep RSS, heap, native or external memory, committed memory, and footprint separate. A missing reading is unknown, never zero.
- Compare baseline and changed builds on the production path with the existing harness. Include natural peaks and recovery after idle, plus concurrency, quiet periods, reconnects, and completion of final writes where relevant.
- Forced GC results are supplementary. Unit tests, or a harness that was never run, do not show a saving.
- Measure the CPU and latency side of the tradeoff too ([performance-engineering](../../performance-engineering/SKILL.md)).

## Cost output

When this reference is loaded, the agent's report contains one `Cost:` line per materially affected recurring or retained path:

`Cost: <path/owner>; <frequency × payload × copies/scans × consumers>; retained <bound/lifetime/overflow>; fallback <full work on miss/fallback>; tradeoff <durability/latency>; <ESTIMATED|MEASURED|UNVERIFIED> <evidence, budget result>; next <check>`

- **ESTIMATED**: calculated from the formula and the code, nothing run. Show the inputs.
- **MEASURED**: a comparable baseline and changed run (check 7). Cite the harness or command, metric, units, both readings, and the budget result.
- **UNVERIFIED**: no defensible estimate or measurement yet. `next` names what would settle it.

If the reference was loaded but no recurring or retained path changed, write one `Cost: none — <reason>` line. When the skill was not loaded, add no `Cost:` line.

Code Inspection checks that each label matches its evidence. A MEASURED line without a comparable baseline becomes UNVERIFIED. These checks add no approval gate and no universal numeric threshold; findings use the existing review severity rules.
