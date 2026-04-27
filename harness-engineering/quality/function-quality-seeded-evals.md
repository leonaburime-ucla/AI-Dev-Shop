# Function Quality Seeded Evals

Version: 2.0.0
Last Updated: 2026-04-26

Use this plan to test whether Programmer, Code Review, and Refactor apply the
coding foundations, implementation guardrails, testable design rules, and
function-quality assessment discipline under pressure.

This doc now sits under the generic isolation framework and coverage model:

- `harness-engineering/quality/agent-isolation-eval-framework.md`
- `harness-engineering/quality/eval-coverage-model.md`

## Why This Was Reworked

The earlier seeded evals proved that planted-defect testing works, but they were
still too easy to over-interpret:

- one-seed-per-item designs were clean but unrealistically isolated
- `Easy / Medium / Hard` existed without structural calibration
- reported percentages could hide missing bug classes and missing controls
- small suites could look authoritative even when they were still pilot-scale

This version fixes that by making bug nature, seed structure, controls, and
saved runs mandatory parts of the eval design.

## Status Labels For Function-Quality Suites

Use these labels explicitly:

| Label | Minimum bar |
|---|---|
| `exploratory` | Seeds exist, but no explicit coverage matrix or no saved reruns |
| `pilot` | Matrix exists, but fewer than 30 seeds or missing advanced structures |
| `benchmark` | 36+ seeds, controls present, all tiers covered, 3 saved runs |
| `stable benchmark` | 54+ seeds, regression pack preserved through later framework changes |

An 18-seed suite can still be useful, but it is pilot evidence, not a stable
capability benchmark.

## Required Artifacts

Each suite should include the generic framework files:

- `coverage-matrix.tsv`
- `seed-catalog.tsv`
- `seed-ledger.md`
- `controls.md`
- `run-manifest.tsv`
- `run-results.tsv`
- `reports/coordinator-eval-summary.md`

Use the templates under `harness-engineering/quality/templates/`.

Validate the suite with:

```bash
python3 harness-engineering/validators/validate_eval_suite.py <suite-dir> --require-run-results --min-runs 3
```

For a regression-only rerun pack that intentionally re-tests only previously
missed or partial seeds, validate with:

```bash
python3 harness-engineering/validators/validate_eval_suite.py <suite-dir> --suite-kind targeted_regression --require-run-results --min-runs 3
```

This is the efficient rerun path. Do not re-run cleanly caught seeds after
every framework tweak.

## Function-Quality Coverage Axes

### 1. Domain Dimensions

These are still the core function-quality dimensions that seeds should exercise.

| Dimension | Typical failure pressure |
|---|---|
| Stable boundaries | positional args, boolean flags, unstable return contracts |
| Explicit dependencies | hidden clock, random, env, cache, module state |
| Pure logic vs effects | logging, I/O, or mutation inside decision logic |
| Single responsibility | orchestration, validation, persistence, and routing collapsed together |
| Small testable units | branch-heavy units with no seams |
| Predictable errors | mixed `null` / `false` / throw / strings for one failure class |
| Typed/stable result | shape-shifting outputs and leaked third-party errors |
| Hidden branching | environment or time-based behavior with no contract |
| Complexity and scale | quadratic loops, recursion, unbounded memory |
| I/O shape | N+1 calls, per-item external operations, hidden retries |
| Resource bounds | no chunking, timeout, payload cap, or retry cap |
| Idempotency | retries duplicate writes or effects |
| Concurrency safety | shared mutable cache, singleton state, order dependence |
| Determinism | real time, real randomness, sleep-based tests |
| Observability for effects | missing or unsafe logs, metrics, or traces |
| Security/privacy | PII logging, unsafe interpolation, caller-owned identifiers |
| Extension point | adding a rule requires editing core orchestration |
| Deletion/refactor signal | oversized logic with no structural fix path |
| Test anti-patterns | brittle mocks, implementation assertions, shared fixtures |
| Adversarial aggregate behavior | repeated keys, combined totals, ordering changes, partial invalid batches |
| Function scoring | inflated `100/100` or skeptical review theater |
| Documentation noise | excessive helper-level scoring that hides meaning |
| Handoff/reporting | missing score tables, risk disclosure, or coverage evidence |
| Comment-code mismatch | names or docs contradict actual behavior |
| Out-of-scope over-engineering | extra features beyond brief or spec |
| Loop termination off-by-one | fencepost arithmetic and index boundary errors |

### 2. Bug-Nature Mix

Do not stop at dimension tagging. Each suite should also tag bug nature using
the taxonomy in `eval-coverage-model.md`.

For function-quality work, the most important natures are usually:

- `omission`
- `boundary_error`
- `semantic_mismatch`
- `type_contract_error`
- `missing_test`
- `anti_pattern`
- `hidden_dependency`
- `state_leak`
- `invariant_violation`
- `cosmetic_fix`
- `severity_misclassification`

### 3. Seed-Structure Mix

Function-quality suites should not be mostly `single`.

Use all of these across a benchmark suite:

| Structure | Function-quality example |
|---|---|
| `single` | One obvious hidden `Date.now()` dependency |
| `combined` | N+1 I/O plus missing timeout in the same batch loop |
| `layered` | Type looseness hides a deeper aggregation bug |
| `distributed` | Caller, helper, and test together reveal the issue |
| `camouflaged` | Confident handoff claims score skepticism already passed |
| `interference` | One rule pushes cleanup while another pushes severity escalation |

If the suite lacks `combined`, `layered`, and `distributed` coverage, it is
still testing the easy version of the problem.

## Difficulty Calibration For This Domain

Use the generic calibration rules, with these domain-specific heuristics:

- **Easy**: one file, one issue, direct symptom
- **Medium**: caller + callee, or code + test, or one combined seed
- **Hard**: aggregate invariant, deceptive handoff, layered defect, or
  multi-file reasoning with plausible local correctness

Good Hard seeds in this domain usually involve:

- aggregate invariants
- false confidence from tests or score tables
- naming or comment camouflage
- distributed evidence across code, tests, and handoff artifacts

## Minimum Suite Shape

For Programmer, Code Review, and Refactor, use this as the default target:

| Tier | Minimum seed count | Structural expectation |
|---|---|---|
| Easy | 12 | Mostly `single`, plus at least one positive and one negative control |
| Medium | 12 | `combined` and `distributed` required |
| Hard | 12 | `layered`, `camouflaged`, or `interference` required |

That gives a 36-seed benchmark floor. A more stable target is 54 seeds:

- 18 Easy
- 18 Medium
- 18 Hard

This is the point where per-seed variance matters less than it does in tiny
6-seed tiers.

## Full Benchmark Runs vs Targeted Regression Runs

Use both, but do not confuse them:

1. **Full benchmark runs**
   Use these to establish or re-certify capability claims. They re-score every
   seed in the suite and must include controls.
2. **Targeted regression runs**
   Use these after a prompt/skill/guard change. Re-run only the seeds that were
   previously `MISSED` or `PARTIAL` for the target agent. Save at least 3 runs
   per unresolved seed and record the exact LLM/model in `run-manifest.tsv`.

Targeted regression runs answer:

- did the fix improve the specific misses?
- did the same seed remain unstable across multiple runs?

They do **not** answer:

- what is the agent's new full benchmark score?
- did false-positive behavior regress on previously clean controls?

Those questions still require a later full benchmark recertification pass.

## Project Shapes

Use multiple mini-project shapes so failures stay attributable:

1. **Rule engine / validator**
   Tests aggregate behavior, extension points, deterministic ordering, stable
   errors, and score calibration.
2. **Batch processor**
   Tests resource bounds, idempotency, retries, cancellation, per-item I/O, and
   observability.
3. **Adapter boundary**
   Tests typed errors, raw SDK leaks, privacy-safe logging, timeouts, and retry
   contracts.
4. **Stateful cache or scheduler**
   Tests concurrency safety, hidden state, determinism, and cleanup discipline.
5. **Security-sensitive formatter/query builder**
   Tests trust boundaries, unsafe interpolation, and privacy exposure.
6. **Transfer/accounting workflow**
   Tests invariants, rollback/compensation, partial failure, and boundary math.

## Agent-Specific Input Modes

### Programmer

Programmer receives raw brownfield code plus a brief. This is already an
isolation pattern, but it now must satisfy the same matrix and rerun rules as
other agents.

Key target pressure:

- hidden dependencies
- resource bounds
- aggregate invariants
- anti-pattern removal
- test design realism

### Code Review

Code Review receives pre-staged buggy code plus a fabricated Programmer handoff.

Required pressure:

- `camouflaged` seeds where the handoff sounds trustworthy
- `interference` seeds where one rule competes with another
- regression seeds for any previously promoted guard
- negative controls so review does not become "flag everything"

### Refactor

Refactor receives working code plus a review report.

Required pressure:

- `cosmetic_fix` traps
- `layered` behavior drift
- `distributed` dependency breakage
- missing test updates after structural changes

## Scoring

Use the generic scoring model:

- `CAUGHT = 1.0`
- `PARTIAL = 0.5`
- `MISSED = 0.0`
- `FALSE_POSITIVE = 0.0`

But report these domain-specific views too:

- per-dimension catch rate
- per-bug-nature catch rate
- per-structure catch rate
- per-tier catch rate
- aggregate invariant catch rate
- test-quality false-confidence catch rate

Do not headline a single combined percentage if those breakdowns are missing.

## Promotion Rules

Apply `failure-promotion-policy.md`, but add this interpretation:

- if a miss repeats across structures, prefer a framework or validator fix over
  a narrow guard
- if a guard fix improves one seed and destabilizes another, the missing piece
  is usually regression-pack coverage, not more prompt text
- if a suite cannot explain its blind spots in matrix terms, it is not ready to
  drive durable guard promotion

## Operational Rule

Any future summary claiming Programmer or Code Review capability from a
function-quality suite should say whether the suite is exploratory, pilot,
benchmark, or stable benchmark. If the label is omitted, treat the claim as
under-specified.
