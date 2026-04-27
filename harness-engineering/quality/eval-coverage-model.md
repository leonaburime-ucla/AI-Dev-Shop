# Eval Coverage Model

Version: 1.0.0
Last Updated: 2026-04-26

## Purpose

Make eval gaps visible before agents are scored.

Without a coverage model, seeded evals drift toward whatever bugs are easiest to
invent and score. That produces attractive percentages but weak trust.

This model defines four separate coverage axes:

1. **Agent dimension**: which skill or review dimension should catch the issue
2. **Bug nature**: what kind of defect or trap it is
3. **Seed structure**: how the defect is arranged in the artifacts
4. **Difficulty**: how much evidence synthesis or deception is required

The matrix is not a full Cartesian product. Some combinations are nonsense and
should be marked `pruned`. The point is to make pruning explicit instead of
invisible.

## Bug Nature Taxonomy

Use these values in `coverage-matrix.tsv` and `seed-catalog.tsv`.

| Bug nature | What it means | Example |
|---|---|---|
| `contradiction` | Code or artifact says the opposite of the spec | Admin override records the wrong actor |
| `omission` | Required behavior is missing | No rate limiting, no rollback, no timeout |
| `boundary_error` | Inclusive/exclusive, off-by-one, or threshold mistake | `>=` vs `>` on capacity |
| `semantic_mismatch` | Names, comments, or docs lie about behavior | Comment says rate limited, code is not |
| `severity_misclassification` | Issue is found but downplayed | Invariant break labeled Recommended |
| `cosmetic_fix` | Claimed fix does not change behavior structurally | Comments-only debt-band fix |
| `type_contract_error` | Return shape, type, or interface contract is unstable or wrong | Raw SDK error leaks across boundary |
| `missing_test` | A required scenario is not tested or is weakly asserted | No error-path test, fake cleanup |
| `anti_pattern` | Known harmful implementation pattern | Catch-all error handling, N+1 I/O |
| `hidden_dependency` | Behavior depends on implicit global state or environment | `Date.now()` inside decision logic |
| `dead_code` | Unused or unreachable code hides drift or inflates confidence | Legacy helper never used |
| `state_leak` | State bleeds across records, calls, or tests | Global fake timers without cleanup |
| `invariant_violation` | Multi-step behavior can break a promised invariant | Transfer loses quantity on partial failure |

If a suite introduces a new recurring defect class, add it here rather than
smuggling it into prose.

## Seed Structure Taxonomy

These values describe how the defect is arranged, not what the defect is.

| Structure | What it tests | Example |
|---|---|---|
| `single` | One isolated defect in one place | One obvious missing validation |
| `combined` | Multiple defects co-exist in one unit | N+1 plus missing idempotency in one function |
| `layered` | One defect masks another | Type mismatch hides deeper logic bug |
| `distributed` | Evidence is split across files or artifacts | Spec, caller, and callee must all be read |
| `camouflaged` | Narrative or naming misdirects the agent | Confident handoff claims fix is complete |
| `interference` | Two rules compete for attention or classification | One rule nudges Recommended while another should force Required |

If a suite only uses `single`, it is not exercising realistic review pressure.

## Difficulty Calibration

Difficulty is derived from evidence synthesis and deception load, not how
impressive the seeded bug sounds.

| Tier | Calibration rule |
|---|---|
| `Easy` | One artifact or one location; direct evidence; no serious deception required |
| `Medium` | Requires 2-3 locations, or one location plus one deceptive cue, or one combined seed |
| `Hard` | Requires cross-file synthesis, ambiguity judgment, layered masking, strong camouflage, or rule interference |

Promote a seed to `Hard` only when at least one of these is true:

- evidence is distributed across 3 or more locations
- the issue is layered or interference-based
- the happy path works and the failure only appears under context
- the handoff, naming, or surrounding comments actively mislead the agent

## Matrix Rules

Every benchmark-grade suite should satisfy these minimum rules:

1. **Dimension baseline**: each target dimension gets at least one `Easy` +
   `single` cell so basic competency is measured.
2. **Structure pressure**: each target dimension gets at least one non-`single`
   cell from `combined`, `layered`, `distributed`, `camouflaged`, or
   `interference`.
3. **Difficulty spread**: the suite covers all three difficulty tiers.
4. **High-risk repetition**: high-risk natures such as `omission`,
   `boundary_error`, `hidden_dependency`, `state_leak`, and
   `invariant_violation` should not appear only once across the whole suite
   unless explicitly justified.
5. **Explicit pruning**: if a dimension-nature-structure combination does not
   make sense, mark it `pruned` with a rationale.

## Control Requirements

Benchmark-grade suites also require non-seed controls:

- **Positive controls**: obvious must-catch checks that prove the agent is not
  asleep or off-topic.
- **Negative controls**: realistic non-bugs that the agent should not flag.
- **Regression pack**: preserved seeds that previously caught a failure and must
  remain stable after framework updates.
- **Clean control**: at least one clean or mostly clean section so the agent is
  not rewarded for over-reporting.

## Per-Dimension Seed Density

Suite-level seed floors (36, 54) prevent tiny suites from posing as benchmarks,
but they do not prevent all seeds from clustering in one or two dimensions.

Rules:

- Each **target dimension** should have at least 5 seeds if the suite is pilot
  and at least 8 seeds if the suite claims benchmark status.
- If a dimension has fewer than 5 seeds, document why in the coverage matrix
  rationale column (e.g., the dimension only applies to a narrow project shape).
- Do not compensate for a thin dimension by adding more Easy seeds to an already
  saturated dimension.

The validator warns when any target dimension falls below these floors.

## Negative-Control Calibration

Requiring "at least one negative control" is structurally weak. A suite with 50
real seeds and 2 negative controls cannot meaningfully measure over-reporting
tendency.

Rules:

- Benchmark suites must include negative controls totaling at least **15%** of
  the standard seed count (rounded up). For a 36-seed benchmark, that means at
  least 6 negative controls.
- Negative controls should span multiple dimensions and difficulty tiers, not
  cluster in one easy bucket.
- If the false-positive rate computed from negative controls is unstable across
  runs, add more negative controls before adding more standard seeds.

The validator enforces the 15% floor for benchmark suites.

## Cross-Dimension Stability (Attention-Budget Metric)

Adding rules or seeds to one dimension can redistribute an LLM agent's attention
and destabilize previously stable seeds in other dimensions. This happened in
practice: promoting guards for CR-13/15/16 improved their catch rates but caused
CR-17 to regress from stable to 63%.

Regression seeds partially cover this, but they are not the same as an explicit
stability metric.

Rules:

1. **Baseline run set**: before applying a framework change, record the per-seed
   catch rate from the most recent benchmark runs. This is the baseline.
2. **Post-change run set**: after applying the change, record the same metric
   from the new benchmark runs.
3. **Stability delta**: for each seed, compute `post_catch_rate -
   baseline_catch_rate`. Any seed that drops by more than **0.3** (e.g., from
   1.0 to 0.67 or lower) is flagged as a **stability regression**.
4. **Cross-dimension check**: if the regressed seed is in a different dimension
   from the changed rules, flag it as an **attention-budget regression** — the
   change shifted attention away from another capability.

The scorer reports:

- number of stability regressions (any seed that dropped > 0.3)
- number of attention-budget regressions (stability regressions in a different
  dimension from the change)
- the specific seeds and dimensions involved

A suite with attention-budget regressions is not ready for benchmark
recertification until the regressions are resolved or explained.

To use this metric, pass a baseline run-results file to the scorer:

```bash
python3 harness-engineering/quality/scripts/score_eval_suite.py <suite-dir> \
  --baseline-results <path-to-previous-run-results.tsv>
```

## Statistical Rules

Coverage alone is not enough. Use these run rules:

1. Any suite used to justify a guard, prompt, or skills change needs at least 3
   saved runs after that change.
2. Report per-seed catch rate, not just one suite headline number.
3. Use false positive rate and severity accuracy alongside catch rate.
4. If results swing materially across runs, treat that as a stability problem in
   the eval system, not just an agent problem.
5. Use **targeted regression reruns** for previously unresolved seeds after a
   narrow change. Do not re-run already stable passes unless you are doing a
   full benchmark recertification.
6. A targeted regression pack is not a substitute for a benchmark suite. It is
   a fast follow-up instrument for misses and partials only.

## Status Labels

Use these labels when describing a suite:

| Label | Meaning |
|---|---|
| `exploratory` | Missing matrix coverage, controls, or saved multi-run data |
| `pilot` | Has seeds and some structure, but not enough coverage to claim stability |
| `benchmark` | Matrix complete, controls present, 3 saved runs, validator passes |
| `stable benchmark` | Benchmark plus repeated regression stability over later framework changes |

Do not describe exploratory or pilot suites as proof of stable capability.

## Practical Targeting

You do not need to fill every imaginable cell. You do need to know which cells
you intentionally left empty and why.

The right question is not "did we reach 100%?" The right question is "what bug
types, structures, and difficulty conditions are still untested or only tested
once?"
