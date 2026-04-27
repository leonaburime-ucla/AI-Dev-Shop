# Agent Isolation Eval Framework

Version: 2.0.0
Last Updated: 2026-04-26

## Purpose

Define a repeatable, agent-agnostic harness for testing any AI Dev Shop agent
in isolation. Each agent receives controlled inputs with seeded defects and a
hidden ledger scores what the agent caught, missed, misclassified, or invented.

Pipeline evals measure end-to-end quality but hide individual agent capability.
Isolation evals measure independent capability.

## What Changed In v2.0.0

The earlier framework proved the isolation pattern, but it still left critical
gaps:

- seed coverage was not driven by an explicit matrix
- bug nature and seed structure were mixed together
- difficulty tiers were descriptive, not calibrated
- rerun data was discussed in chat but not required as a saved artifact
- suites could look strong while still missing layered, distributed, or
  false-positive checks

This version fixes that by making coverage, controls, and persisted run data
first-class requirements.

## Core Principle

**Controlled input, hidden ledger, explicit coverage model, persisted run data,
post-hoc scoring.**

Every isolation eval now follows this structure:

1. **Coordinator designs a coverage matrix** before writing seeds
2. **Coordinator fabricates inputs** that look like natural upstream output
3. **Agent runs in a fresh context** with no knowledge of the eval
4. **Hidden seed metadata and narrative ledger** define what should be caught
5. **Run results are persisted** for every pass, not summarized from memory
6. **Coordinator scores against saved artifacts** and promotes guards only from
   reproducible evidence

The source of truth for the matrix model is
`harness-engineering/quality/eval-coverage-model.md`.

---

## Required Suite Artifacts

New suites should use this layout:

```text
.local-artifacts/agent-evals/<suite-id>/
  coverage-matrix.tsv          # required: planned coverage cells (suite-level)
  seed-catalog.tsv             # required: machine-readable seed metadata (suite-level)
  seed-ledger.md               # required: hidden narrative ledger (suite-level)
  controls.md                  # required: positive/negative/regression controls (suite-level)
  run-manifest.tsv             # required once runs begin (suite-level)
  run-results.tsv              # required once runs begin (suite-level)
  <eval-name>/                 # one directory per mini-project
    project-brief.md           # what the agent sees
    seed-state/                # immutable fixture: the pre-seeded project snapshot
      src/                     #   source code with planted defects
      specs/                   #   spec artifacts (if applicable)
      reports/                 #   fake upstream handoffs
    runs/                      # created by prepare_eval_run.py (never hand-edited)
      <run-id>/                #   fresh copy of seed-state/ for one run
        src/
        specs/
        reports/
          <agent>-output.md    #   agent's actual output lands here
    prompts/                   # optional: exact prompts used for dispatch
  reports/
    coordinator-eval-summary.md
```

### Suite-Level vs Per-Eval Artifacts

The six TSV/MD files at the suite root (`coverage-matrix.tsv`,
`seed-catalog.tsv`, `seed-ledger.md`, `controls.md`, `run-manifest.tsv`,
`run-results.tsv`) describe the **entire suite** and reference seeds across all
mini-projects.

Each `<eval-name>/` subdirectory contains the **per-project fixtures**: the
actual code, specs, and handoffs the agent will see. The `seed-state/`
directory inside each eval is the immutable snapshot — it is never modified
during a run.

`prepare_eval_run.py` copies `seed-state/` into `runs/<run-id>/` so each run
gets a fresh working directory. This keeps the benchmark inputs stable across
reruns.

```bash
# Prepare all evals in the suite for a new run:
python3 harness-engineering/quality/scripts/prepare_eval_run.py <suite-dir> <run-id>

# Prepare only one specific eval:
python3 harness-engineering/quality/scripts/prepare_eval_run.py <suite-dir> <run-id> --eval <eval-name>
```

### Scoring a Suite

After runs are scored into `run-results.tsv`, generate the aggregate metrics:

```bash
python3 harness-engineering/quality/scripts/score_eval_suite.py <suite-dir>

# With baseline comparison for attention-budget regression detection:
python3 harness-engineering/quality/scripts/score_eval_suite.py <suite-dir> \
  --baseline-results <path-to-previous-run-results.tsv>
```

The scorer computes all required suite-level metrics, emits a status label, and
writes the report to stdout or an optional output file.

Legacy suites may keep markdown-only ledgers, but new benchmark claims should
not rely on them alone.

## Coverage Matrix Format

`coverage-matrix.tsv` is the suite-level plan. One row represents one target
cell in the coverage model.

```text
cell_id  agent  agent_dimension  bug_nature  seed_structure  difficulty  requirement  rationale  seed_ids
```

Required columns:

- `cell_id`: stable identifier such as `CR-SPEC-INV-HARD-01`
- `agent`: target agent name, for example `code-review`
- `agent_dimension`: the skill dimension that should catch the seed
- `bug_nature`: taxonomy value from `eval-coverage-model.md`
- `seed_structure`: taxonomy value from `eval-coverage-model.md`
- `difficulty`: `Easy`, `Medium`, or `Hard`
- `requirement`: `required`, `optional`, or `pruned`
- `rationale`: why this cell matters or why it was pruned
- `seed_ids`: comma-separated seed IDs once the cell is populated

Use `pruned` only when a combination is nonsensical for that agent. Do not
leave gaps implicit.

## Seed Catalog Format

`seed-catalog.tsv` is the machine-readable seed inventory. It complements the
human-readable `seed-ledger.md`.

```text
seed_id  eval_name  agent  agent_dimension  skill_source  agent_guard  bug_nature  seed_structure  difficulty  control_type  expected_severity  false_positive_risk  evidence_path  detail_ref  matrix_cell_id
```

Required columns:

- `seed_id`: stable identifier such as `SEED-CR-17`
- `eval_name`: the eval bucket or mini-project name
- `agent`: target agent
- `agent_dimension`: dimension expected to catch the issue
- `skill_source`: specific skill file and section
- `agent_guard`: agent-level guard that should catch it, or `none`
- `bug_nature`: taxonomy value
- `seed_structure`: taxonomy value
- `difficulty`: `Easy`, `Medium`, or `Hard`
- `control_type`: `standard`, `positive_control`, `negative_control`, or
  `regression`
- `expected_severity`: `Critical`, `Required`, or `Recommended`
- `false_positive_risk`: `None`, `Low`, `Medium`, or `High`
- `evidence_path`: repo-local path or file:line
- `detail_ref`: row/section reference into `seed-ledger.md`
- `matrix_cell_id`: target coverage cell

Keep the long-form seeded issue narrative, deception notes, and expected signal
in `seed-ledger.md`. Keep normalized fields in `seed-catalog.tsv`.

## Run Manifest Format

Every scored run must declare which agent/model executed it and which seeds it
was intended to cover.

```text
run_id  agent  llm_family  model_id  model_label  cli_name  cli_version  selection_source  run_scope  target_seed_ids  workdir  prompt_path  output_path  executed_at
```

Required columns:

- `run_id`: stable identifier used in `run-results.tsv`
- `agent`: target agent, for example `programmer`
- `llm_family`: provider or family label such as `openai`, `anthropic`, or
  `google`
- `model_id`: exact model identifier used for the run
- `model_label`: human-readable display label
- `cli_name`: execution surface such as `codex-cli` or `claude-code`
- `cli_version`: CLI version string used for diagnostics
- `selection_source`: how the model was chosen, for example
  `per_run_override`, `host_config`, or `smoke_test_discovery`
- `run_scope`: `benchmark_full` or `targeted_regression`
- `target_seed_ids`: `all` for a full benchmark pass, otherwise a
  comma-separated seed subset
- `workdir`: run-specific working directory
- `prompt_path`: exact prompt used
- `output_path`: where the agent's saved output lives
- `executed_at`: ISO-8601 UTC timestamp

This is how rerun claims stay attributable to a specific LLM/model instead of
being summarized from chat memory.

## Run Results Format

Every scored run must be persisted in `run-results.tsv`.

```text
run_id  seed_id  result  severity_correct  reviewer_notes
```

Rules:

- one row per seed per run
- `result` must be `CAUGHT`, `PARTIAL`, `MISSED`, or `FALSE_POSITIVE`
- `severity_correct` must be `yes`, `no`, or `na`
- every `run_id` must exist in `run-manifest.tsv`
- a benchmark claim requires at least 3 distinct `benchmark_full` runs after
  any agent, skill, or prompt change
- a targeted regression claim requires at least 3 distinct
  `targeted_regression` runs for each unresolved seed being re-tested

If the run data is not saved, the claim is exploratory, not benchmark-grade.

## Two Rerun Loops

Use two different rerun modes on purpose:

1. **Benchmark full runs**
   Re-test the full suite when establishing or re-certifying benchmark claims.
   These runs must score every seed in the suite.
2. **Targeted regression runs**
   Re-test only the previously missed or partial seeds after a guard, prompt,
   or skill change. Do not waste reruns on seeds that were already stable.

Targeted regression runs are valid evidence for "did we fix the misses?" They
are not a replacement for periodic full-suite benchmark re-certification.

## Control Packs

Benchmark suites must include all three internal control types:

- `positive_control`: obvious must-catch seeds that verify the agent is awake
- `negative_control`: plausible-looking non-bugs that measure false positives
- `regression`: seeds preserved specifically to ensure earlier capability does
  not disappear when new guards are added

`controls.md` should list which seeds belong to each pack and why.

Targeted regression packs may be regression-only. In that mode, `controls.md`
must say which baseline benchmark suite they derive from and why only the
unresolved seeds were re-run.

## Difficulty Rules

Difficulty is no longer a vibe label. Use the calibration rules in
`eval-coverage-model.md`.

At minimum:

- **Easy**: one artifact or one location; no serious deception required
- **Medium**: cross-function or cross-artifact; at least one competing cue
- **Hard**: layered, distributed, semantic, ambiguity-based, or deception-heavy

If a seed is labeled `Hard`, its structure should justify the label.

## Scoring Rubric

Per seed:

| Score | Definition | Numeric |
|---|---|---|
| `CAUGHT` | Correct issue at correct severity/classification | 1.0 |
| `PARTIAL` | Related concern, but wrong severity, scope, or explanation | 0.5 |
| `MISSED` | Issue not flagged at all | 0.0 |
| `FALSE_POSITIVE` | Agent flagged a non-issue | 0.0 and counts against FPR |

Required suite-level reporting:

- mean score per run
- per-seed catch rate across saved runs
- severity accuracy across saved runs
- false positive rate
- per-difficulty breakdown
- per-bug-nature breakdown
- per-seed-structure breakdown
- per-dimension breakdown

Do not headline a single-run number as the capability score after a framework
change. Report the saved multi-run aggregate.

## Validation

Use the suite validator before claiming the suite is ready:

```bash
python3 harness-engineering/validators/validate_eval_suite.py <suite-dir> --require-run-results --min-runs 3
```

The validator checks:

- required suite files exist
- coverage cells are explicit
- required cells are populated by seeds
- seed metadata uses valid taxonomy values
- benchmark suites have positive, negative, and regression controls
- benchmark suites include advanced structures and difficulty spread
- saved run data covers exactly the seeds declared by each run manifest row

If the validator fails, the suite is not benchmark-ready.

---

## Agent-Specific Input Designs

### Code Review Agent

**Input**: Pre-staged code with remaining bugs plus a fake Programmer handoff.

**Target coverage**:

- all Code Review dimensions
- bug natures such as invariant violation, semantic mismatch, omission, and
  severity misclassification
- structures beyond `single`, especially `camouflaged`, `distributed`, and
  `interference`

**Required control pressure**:

- regression seeds for previously promoted guards
- negative controls to verify CR does not invent issues in clean sections

### Programmer Agent

**Input**: Brownfield code plus a project brief.

**Target coverage**:

- coding foundations
- implementation guardrails
- function quality assessment
- both local defects and cross-record aggregate behavior

Programmer evals are still isolation evals, but they now need the same matrix,
control packs, and saved run-results as other agents.

### Spec Agent

**Input**: Vague or contradictory brief.

**Target coverage**:

- omission
- contradiction
- boundary ambiguity
- invariant omission
- implicit dependency
- untestable acceptance criteria

Strong Spec evals should lean heavily on `layered`, `camouflaged`, and
`interference` seeds because high-quality spec work is mostly judgment, not
surface bug spotting.

### Refactor Agent

**Input**: Working code plus review guidance.

**Target coverage**:

- cosmetic-fix traps
- behavior drift
- wrong abstraction target
- distributed dependency breakage
- test upkeep misses

### Architect, Security, TDD, Red Team

These agents should use the same structure: explicit matrix first, then seed
design, then saved multi-run scoring. Do not invent agent-specific suite rules
that bypass the shared coverage model.

---

## Harness Execution Protocol

### Before the eval

1. Define the suite's target dimensions.
2. Build `coverage-matrix.tsv`.
3. Mark nonsensical combinations as `pruned` with rationale.
4. Create `seed-catalog.tsv` and `seed-ledger.md`.
5. Define `positive_control`, `negative_control`, and `regression` packs in
   `controls.md`.
6. Stage the eval directory and upstream-deception artifacts.
7. Run `validate_eval_suite.py` without run requirements to catch schema and
   coverage issues before dispatch.

### During the eval

8. Dispatch the agent in a fresh context.
9. Let the agent produce its normal output with no intervention.
10. Score the run into `run-results.tsv`.

### After the eval

11. Re-run at least 3 times after any framework, guard, or prompt change.
12. Generate `coordinator-eval-summary.md` from saved run data.
13. Promote guards only from repeated, persisted misses or Critical one-offs
    according to `failure-promotion-policy.md`.

### Iteration

14. When Easy saturates, add harder structures before adding more Easy seeds.
15. When a new guard fixes one seed but destabilizes another, add or strengthen
    regression seeds rather than assuming the latest run is representative.
16. Retire low-signal seeds only after they stay stable across 3 or more
    benchmark runs and still leave the coverage matrix satisfied.

## Metrics To Track

| Metric | Definition | Target |
|---|---|---|
| Independent catch rate | Mean caught score across saved runs | Agent-dependent, but never single-run only |
| False positive rate | False positives / total findings | 0% for benchmark claims |
| Severity accuracy | Correct severity / caught-or-partial seeds | > 90% |
| Per-tier catch rate | Catch rate by `Easy`, `Medium`, `Hard` | Visible in every summary |
| Per-structure catch rate | Catch rate by structure type | Visible in every summary |
| Per-bug-nature catch rate | Catch rate by bug taxonomy | Visible in every summary |
| Run variance | Spread across saved runs | Should shrink over time |
| Matrix completion | Covered required cells / required cells | 100% |

## Definition Of Done

A suite is close to trustworthy when all of these are true:

1. every required coverage cell is explicit and populated
2. bug nature and seed structure are both tracked
3. positive, negative, and regression controls exist
4. at least 3 saved runs exist after the latest framework change
5. every run is persisted in `run-results.tsv`
6. the suite validator passes
7. the summary is derived from saved artifacts, not chat recollection

## Legacy Note

Earlier suites in this repo are still useful, but unless they are migrated to
the matrix-plus-runs model they should be treated as exploratory or pilot
evidence, not as stable benchmark infrastructure.

## Relationship To Other Harness Docs

- `eval-coverage-model.md` — canonical taxonomy and coverage rules
- `function-quality-seeded-evals.md` — domain-specific application for
  Programmer, Code Review, and Refactor
- `failure-promotion-policy.md` — promotion rules for repeated failures
- `agent-performance-scorecard.md` — roll-up view after suites are benchmarked
