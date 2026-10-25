# Sensor: Mutation Quality

Grades test effectiveness by deliberately injecting faults into modified code and checking whether the test suite detects them. A test that passes after code is broken is not protecting anything.

## Sensor Definition

- **Class**: `computational`
- **Timing**: PR (after green suite confirmation) + scheduled (release gate, full-scope)
- **Owner**: TestRunner triggers → Observer tracks trends → routes to TDD agent or Programmer
- **Artifact location**: `<ADS_MEMORY_ROOT>/.local-artifacts/sensors/mutation-quality-<timestamp>.md`

## Detector

The toolkit installs nothing. The host declares a command in the `mutation_tests`
slot of `<ADS_MEMORY_ROOT>/governance/contracts/computational-controls.md`. If no
slot is declared, this sensor is `inactive` (advisory note only) — reported as
absent, never as clean.

So the contract is a **capability**, not a tool:

> Declare a command that mutates a **caller-supplied scope** and emits a killed
> and survived count for it, plus each surviving mutant with its location. If it
> can only mutate the whole project, say so — the scope policy below is then
> unenforceable and the PR-context gate is `inactive`.

| Requirement | Why |
|---|---|
| Accepts a scope placeholder | the PR context mutates touched files only; a command with no scope input cannot express that |
| Emits killed and survived counts for the scope it ran | a score without a denominator cannot be compared between base and head |
| Locates each surviving mutant | a bare score routes to nobody; the surviving mutant is the finding |
| Records the mutation operator set it ran | two operator sets produce different scores from the same tests, so silence means different things |

**Scope placeholders.** A host declares whichever its command accepts; these name
the granularity, not any particular tool:

- `{touched_files}` — file paths of modified source files that have corresponding tests
- `{touched_packages}` — package paths containing modified files
- `{touched_classes}` — fully qualified type names for modified source files

The separator and quoting a command needs are host detail, declared with it.

## Scope Policy

### PR Context (default)

Mutate only files modified in the current work:
- Source files touched by the PR/feature that have corresponding tests
- Exclude generated code, config files, type declarations, and vendored dependencies
- Scope expansion to direct callers: if a touched file's public API changed, include one level of direct importers when the mutation tool supports it and timeout permits

### Scheduled Context (release gate)

Full module or package mutation run. Expensive — run on CI with extended timeout, not in interactive pipeline.

## Threshold Policy

Mutation testing thresholds are progressive, not absolute from day one.

### Comparison base — the merge base, not a stored file

The comparison base is the **VCS merge base**, recomputed each run. There is no
baseline file.

<!-- historical:start -->
An earlier design stored per-module scores in
`<ADS_MEMORY_ROOT>/.local-artifacts/sensors/mutation-baseline.json` and ratcheted
them upward. That file was writable by every agent sharing the workspace, and it
decided whether this gate blocked — so lowering it before measurement was the
cheapest way to pass, and nothing could detect it after the fact. It was the only
persistent, agent-writable artifact with enforcement authority left in the
harness; every other gate had already moved to merge-base recomputation
specifically to remove that surface.
<!-- historical:end -->

On first run for a project: no enforcement, advisory only. There is nothing to
record — the merge base supplies the comparison on every subsequent run.

Recompute base and head with the **same tool and configuration version**. A
mutation score produced by one tool version compared against another is
`INCONCLUSIVE`, not a regression.

### Ongoing Enforcement

When multiple conditions match simultaneously, apply the most severe gate behavior (Hard Blocker > Escalation > Advisory > Pass).

| Condition | Gate Behavior |
|-----------|--------------|
| Mutation score on touched files drops >10% vs baseline | **Hard Blocker** — regression detected |
| Mutation score on touched files is below the ratcheted module floor | **Escalation** — slipped below established quality |
| Mutation score on touched files is below 60% (absolute floor) | **Escalation** — weak tests on modified code |
| Mutation score on touched files is >=60% and <70% | **Advisory** — improvement recommended |
| Mutation score on touched files is >=70% with regression >0% and <=10% | **Advisory** — minor regression noted |
| Mutation score on touched files is >=70% with no regression or improvement | **Pass** |
| Mutation tool is not declared in computational controls | **Advisory** — sensor inactive, logged |
| Mutation run times out | **Escalation** — inconclusive, cannot gate |
| Mutation tool errors or unsupported stack | **Advisory** — sensor degraded |

### No ratchet

<!-- historical:start -->
An earlier design ratcheted a stored floor to `current_score - 5%` once a module
passed 80%. That mechanism required the writable baseline file above, and it
inherited its weakness: the floor an agent must clear was a number that agent
could edit.
<!-- historical:end -->

Backsliding is caught by the merge-base delta instead — a drop against the base
is a regression whether or not the module ever reached 80%. This is strictly
simpler and has no poisonable state, at the cost of not rewarding a module for
historic investment. That trade is deliberate: a floor nobody can forge is worth
more than a floor that remembers.

## Scope is the changed set, not the tested set

A source file in the changed set stays in mutation scope **whether or not it has
a corresponding test**. A changed file with no test yields no mutation evidence,
and *that* is the finding — it must not silently leave the measurement.

Deleting, renaming or skipping a test so its source file drops out of mutation
scope is `INT-5` and blocks regardless of gate status — see
`<AI_DEV_SHOP_ROOT>/harness-engineering/quality/gate-validation-status.md`.
Scoping to "changed files that have tests" made removing evidence the cheapest
way to improve the number.

## Timeout Policy

Mutation testing is expensive. The sensor enforces a timeout to prevent pipeline stalls.

- **PR context**: default 180 seconds per mutated file, max 600 seconds total for the mutation pass
- **Scheduled context**: default 3600 seconds (1 hour) for full runs
- If timeout is reached: kill the process, report partial results, classify as **Escalation** (inconclusive)
- Projects may override timeouts in the `mutation_tests` slot of computational controls

## Run-Validity Pitfalls

A mutation score is only as valid as the run behind it. These pitfalls come from
the same 2026-10-25 run as `<AI_DEV_SHOP_ROOT>/skills/test-design/SKILL.md`
§ Mutation-Derived Input Rules, and each one produced scores that looked real and
were not. Check them before reporting a score or routing a survivor. They are
reporting guidance and do not change the gate tables.

1. **Dry-run test count.** The tool's unmutated initial run must execute as many
   tests as a plain run of the same suite. A lower count means part of the suite
   did not load in the sandbox, and every mutant only that part covers shows as
   uncovered. Trust no score until the counts match or the gap is explained.
2. **Paths in the sandbox.** Tools that copy the project into a temp directory
   break relative aliases, config `extends`, sibling-package paths and paths
   derived from the module's own URL. Use absolute aliases, keep the temp
   directory inside the package, link sibling packages into it, and run from the
   package directory. (For StrykerJS: a relative `tempDirName: ".stryker-tmp"`,
   and `cleanTempDir: false` when sibling packages are linked in.)
3. **Incremental cache.** An incremental mode may not notice config, alias or
   test-set changes, so a corrected rerun can still carry stale results. After
   any such change, force a full run (for example StrykerJS `force`).
4. **Collection errors are kills.** A mutant that breaks a module at import time
   fails its test file before any test runs, and some tools score that as
   survived. Count a collection or import error as a kill. Flag every mutant whose
   tests-completed count is far below the dry run.
5. **Exclusions.** Report every excluded operator and whether type checking was
   off. Excluding string-literal mutants leaves error messages, permission
   strings, ids and string-keyed allowlists unmeasured. With type checking off
   the bias direction is unknown: a mutant can be killed by an incidental runtime
   error. Do not call the score pessimistic or optimistic.
6. **Ignored static mutants.** Mutants in module-level constants (limits, regex
   tables, defaults) are often skipped for speed (for example StrykerJS
   `ignoreStatic`). Report the ignored count next to every score.
7. **False no-coverage.** Per-test coverage can misattribute when tests load
   native drivers or aliased modules. Before calling a file untested, prove that
   a test actually loads the instrumented file.
8. **Scoped test sets.** A run against a narrowed test set misses kills from
   tests outside it, so its scores are lower bounds. Report the narrowed test
   scope and label its scores as lower bounds; a wider suite may kill more
   mutants.
9. **Timeouts.** A timed-out mutant counts as killed in the score. Two
   safeguards apply:
   - Always report the timeout count separately, including mutants marked
     killed only because the test runner timed out.
   - If timeouts are more than about 5% of a file's mutant results, re-run that
     file with a longer timeout before trusting its score. A slow machine can
     fake kills.

   A default per-test timeout can fail the dry run, so raise it for mutation
   runs. Retrying failed tests can hide flaky kills.
10. **Red baselines.** A failing baseline forces tests out of the run, which
    silently unmeasures what they guard. List every excluded test file next to
    the source files it guards. A failing security pin is a finding to report,
    not noise to exclude.
11. **Process limits.** Code run in a child process is invisible to in-process
    instrumentation: its mutants are unmeasured, not untested. Functions
    serialised to strings (for a browser, say) can break instrumentation
    instead. A whole-suite test set can make
    the run many times slower than a scoped one, and static mutants, which run
    against every test, are the slowest.

## What This Sensor Measures

- **Mutation score**: percentage of injected mutants killed by the test suite
- **Survived mutants**: list of mutations that tests did NOT catch (these are real coverage gaps)
- **Equivalent mutants**: mutations that don't change observable behavior (excluded from score)
- **Timeout mutants**: mutations where tests hung (counted as killed — the test noticed something; always reported as a separate count, and a file with more than ~5% timeouts is re-run with a longer timeout before its score is trusted, see Run-Validity Pitfalls item 9)
- **Per-file mutation scores**: for each touched file, individual score and survived mutant details

## Output Format

The sensor produces a structured artifact:

```
## Mutation Quality Report — <feature-id> — <timestamp>

### Summary
- Scope: touched files only / full module
- Files mutated: <count>
- Total mutants: <count>
- Killed: <count> (<pct>%)
- Survived: <count> (<pct>%)
- Timeout: <count>
- Equivalent (excluded): <count>
- Overall mutation score: <pct>%
- Baseline score: <pct>%
- Delta: <+/- pct>%
- Gate result: PASS / ADVISORY / ESCALATION / HARD_BLOCKER

### Per-File Results
| File | Mutants | Killed | Survived | Score | Baseline | Delta | Status |
|------|---------|--------|----------|-------|----------|-------|--------|

### Survived Mutants (Top Priority)
For each survived mutant:
- File and line
- Mutation type (e.g., boundary change, removed call, negated condition)
- What the test suite should have caught
- Suggested test approach

### Gate Decision
<PASS|ADVISORY|ESCALATION|HARD_BLOCKER> — <rationale>
```

## Action-on-Fail

| Finding | Severity | Action |
|---------|----------|--------|
| Score regression >10% on touched files | Hard Blocker | Pipeline stops; TDD or Programmer must add tests for survived mutants |
| Score below ratcheted module floor | Escalation | Coordinator warns; Programmer asked to restore quality to historical levels |
| Score below 60% on touched files | Escalation | Coordinator warns; Programmer asked to improve tests before Code Inspection |
| Score 60-70% on touched files | Advisory | Noted in handoff; Code Inspection informed |
| Score >=70% with minor regression (>0% and <=10%) | Advisory | Noted in handoff; Code Inspection informed of minor regression |
| Mutation tool timeout (inconclusive) | Escalation | Coordinator decides: retry with narrower scope, defer to scheduled run, or waive |
| Survived mutants in critical-path code | Escalation | Even if overall score is above threshold, specific survived mutants in auth/payment/data-integrity paths escalate |

## Routing

1. **PR context (triggered by TestRunner)**:
   - TestRunner runs mutation pass after all suites are green and coverage is evaluated
   - Mutation results included in TestRunner's run report
   - Gate failures route back to Programmer (add tests) or TDD (redesign test approach)
   - Results forwarded to Code Inspection as evidence for test quality dimension

2. **Scheduled context (Observer)**:
   - Observer runs full-module mutation analysis weekly or at release gates
   - Trends tracked in `<ADS_MEMORY_ROOT>/.local-artifacts/sensors/mutation-trends.json`
   - Sustained low scores → tech debt entry
   - Routes to TDD agent for test-plan recommendations

3. **Interaction with coverage sensor**:
   - Coverage answers "what lines are executed by tests?"
   - Mutation answers "would tests catch a bug on those lines?"
   - A file can have 100% coverage and 30% mutation score (tests execute code but don't assert on results)
   - Both sensors together give the full picture of test effectiveness

## Interaction with Audit Subagent

When `/audit-work` spawns an internal verification subagent:
- Mutation quality results are included in the subagent's evidence packet
- A low mutation score on touched files raises the severity weight for findings about test adequacy
- The subagent may cite survived mutants as evidence that claimed correctness lacks verification

## What This Does NOT Cover

- Test design quality (whether tests check the right things conceptually — that's Code Inspection dimension 3)
- Integration/E2E mutation (only unit/integration source mutations in phase 1)
- Performance impact of code mutations
- Security-specific fault injection (that's Red Team territory)
