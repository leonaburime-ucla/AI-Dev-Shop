# Sensor: Changed-Code Coverage

Measures **what fraction of the branches this change added or modified is
actually exercised by tests**, computed against the merge base.

This is metric 9 of the code-quality program. It did not previously exist. It was
recorded as covered by `coverage-quality.md`, which measures something different
— see the section below, because the distinction is the entire reason this file
exists.

## Sensor Definition

- **Class**: `computational`
- **Timing**: PR only. There is no scheduled mode — "changed code" is undefined
  outside the context of a change.
- **Producer**: **TestRunner** — emits the raw coverage report as a side effect
  of the suite run it already owns
- **Computer / PR owner**: **Code Inspection** — recomputes the diff-coverage
  arithmetic itself on every reviewed change
- **Artifact**: `<ADS_MEMORY_ROOT>/.local-artifacts/sensors/changed-code-coverage-<feature-id>-<timestamp>.json`

## What this measures, and what `coverage-quality.md` measures

These are three different numbers and the harness previously conflated the first
two:

| Metric | Question it answers | Where |
|---|---|---|
| **Suite coverage** | what fraction of the whole codebase is covered? | `skills/test-design/SKILL.md` hard gates (98/90/80) |
| **Coverage trend / delta** | did the overall percentage move, and on which files? | `coverage-quality.md` |
| **Changed-code coverage** (this file) | of the branches *this diff touched*, how many are exercised? | here |

Suite coverage can sit at 98% while a diff adds twelve wholly untested branches —
the denominator is large enough to absorb them. Trend coverage can show "no
drop" for the same diff, because a small number of new uncovered branches against
a large covered base rounds away. **Only this sensor asks the question the
reviewer actually cares about**, which is whether the new logic is tested.

`coverage-quality.md` remains valid for what it does — trends, critical-path
judgment, zero-coverage file detection. It is not a changed-code gate and must
not be cited as one.

### Reconciling the two coverage policies

`skills/test-design/SKILL.md` declares suite gates *"non-negotiable; takes
precedence over all other coverage guidance."* `coverage-quality.md` says
*"coverage alone is never a hard blocker."* Both statements are in force and they
appear to conflict. They do not, once scoped — and the scope is stated here
because neither file states it:

- **`test-design`'s 98/90/80 gates are suite-level project policy**, evaluated by
  TestRunner on the whole suite, configurable per project at pipeline start.
  They are a property of the repository, not of a diff.
- **`coverage-quality`'s "never a hard blocker" applies to trend and critical-path
  findings**, which are inferential and scheduled.
- **This sensor governs the diff.** It does not raise or lower either of the
  above.

Where `test-design`'s suite gate and this sensor disagree — a diff with
well-covered changes landing in a repo below 98% overall, or the reverse — both
findings are reported separately and neither is folded into the other. Reporting
one number for three questions is what produced the confusion.

## Metrics

Computed over the changed executable lines and branches between the merge base
and head.

| Field | Definition |
|---|---|
| `changed_branches_total` | executable branches in added or modified lines |
| `changed_branches_covered` | of those, exercised at least once by the suite |
| `changed_branch_ratio` | covered / total; `null` when total is 0 |
| `changed_lines_total` / `changed_lines_covered` / `changed_line_ratio` | same, for statements — secondary, reported for context |
| `per_file` | the same five fields **per changed file** — mandatory, see gaming below |
| `uncovered_changed_branches` | the actionable output. Identity granularity is **format-dependent** — full `(file, line, block, branch)` from lcov, `file, line, missed_count/total` from Cobertura and JaCoCo. See the line/branch gap section |

**Branch coverage is the primary field and line coverage is context.** A changed
line can be fully "covered" while only one arm of its condition ever executes;
that is the case this sensor exists to catch.

## Not delta-gated — and why this one is the exception

Every other gate in this program blocks only on new-or-worsened values against
the merge base. **This one evaluates the diff absolutely**, and the difference is
deliberate:

- The other gates measure properties of code that mostly predates the change, so
  a delta rule is what separates "this change made it worse" from "this code was
  already like that."
- Changed-code coverage measures *only* code the change touched. There is no
  legacy portion to grandfather. A modified line is this change's responsibility
  whether or not the function around it was covered before.

Consequently a diff that edits a line inside a long-uncovered function **does**
count that line. That is intended: touching untested code is when you find out
it's untested, and it is the cheapest moment to fix it. It is also the reason the
floor is a floor and not a ratchet.

## Threshold

| Parameter | Default | Meaning |
|---|---|---|
| `changed_branch_ratio` floor | **80%** | below this, a finding is raised — applied to the aggregate **and to each changed file independently** |
| Minimum branches to evaluate a unit | **5** | below this the ratio is too noisy to gate on; falls through to the line rule instead of escaping |
| Per-file floor | same 80%, per changed file meeting the 5-branch minimum | a file below the floor is a finding **even when the aggregate passes** |
| Per-file zero-coverage rule | any changed file with branch ratio `0` and **≥ 1** changed branch | absolute — a branch that never executed is never excused by line coverage |
| Line-based fallback, small unit | `changed_line_ratio` below the floor, **no line minimum** | applies when branch data exists but the unit has **0-4** branches — a branchless changed unit is a small unit, not branch-null tooling |
| Line-based fallback, branch-null tooling | `changed_line_ratio` below the floor with ≥ 15 changed lines | applies when `changed_branch_ratio` is `null` |

**The floor is per-file, not only aggregate.** An aggregate-only floor is
defeated by padding: well-covered boilerplate anywhere in the diff lifts the
total while the new logic stays untested. A per-file floor closes cross-file
padding. It does **not** close same-file padding — covered boilerplate added to
the *same file* as the untested logic still lifts that file's ratio. Where the
tooling supports it, apply the floor **per changed hunk or per changed function**;
that is the granularity at which padding stops paying. Per-file is the practical
minimum, not the complete answer, and the residual is real.

**Nothing escapes by being small — and the fallback carries no line minimum when
branch data exists.** This took two attempts. The first draft said small units
"report it, do not gate it," which let sub-5-branch code land at 0%. The fix
routed them to the line rule — but the line rule had its own 15-line minimum, so
a 4-branch, 12-line unit at 25% coverage still triggered nothing while this
paragraph claimed the hole was closed. The 15-line minimum now applies **only**
to genuinely branch-null tooling, where there is no branch signal to fall back
from and the line ratio alone is too noisy on a tiny diff.

Worked corners, all of which are findings:

| Unit | Result |
|---|---|
| 4 branches, 1 covered (25%), 12 changed lines | finding — small-unit line fallback, no minimum |
| 2 branches, 0 covered, 14 changed lines | finding — zero rule, regardless of line coverage |
| 2 branches, 0 covered, 14 lines **all covered** | finding — line coverage cannot launder an untaken branch |
| 1 branch, 0 covered, 10 lines all covered | finding — one untaken branch is enough |
| 2 branches, 2 covered, 6 changed lines | **not** a finding — small and fully covered |
| 0 branches, comment-only change | **not** a finding — negative control |

These are regression cases in
`<AI_DEV_SHOP_ROOT>/harness-engineering/gate-logic/test_reference.py`; the
arithmetic there is normative if this prose ever drifts from it again.

**80% is a starting value, not a calibrated one**, consistent with every other
threshold in this program. It is stated numerically so two reviewers get the same
answer, which is a different property from being correct.

## Gaming vectors

The aggregate ratio is the gameable part, and this is the one metric in the set
whose denominator the author controls directly.

- **Denominator padding.** Adding well-covered boilerplate to the same diff lifts
  the aggregate above the floor while the genuinely new logic stays untested.
  **This is why `per_file` is mandatory and the per-file zero-coverage rule
  exists** — the aggregate alone cannot detect it. A diff whose aggregate passes
  while one changed file sits at 0% is reported on that basis.
- **Coverage-ignore directives** (`/* istanbul ignore */`, `# pragma: no cover`)
  on changed lines — removes branches from the denominator. `REQUIRED` integrity
  finding — `INT-2` in the gate registry — and is never capped.
- **Adding files to the coverage config's exclude list** — same rule.
- **Deleting or skipping a test** to remove a failing branch from the run —
  same rule.
- **Assertion-free tests** that execute a branch without checking anything.
  Coverage cannot see this by construction; it is Code Inspection's Dimension 3
  judgment and mutation testing's job, not this sensor's. Stated so this sensor
  is not mistaken for evidence that the tests are good.

## Tools

The host declares a command in the `diff_coverage` slot of
`<AI_DEV_SHOP_ROOT>/framework/contracts/computational-controls.md`.

### The line/branch gap — read before declaring a tool

**The common diff-coverage tools report changed *lines*, not changed *branches*.**
`diff-cover` attributes a coverage report to the diff and reports covered and
uncovered **diff lines**; it is not a branch-level diff tool. Codecov's and
Coveralls' *patch* status are likewise line-based by default.

So the primary metric this sensor defines — `changed_branches_total` /
`changed_branches_covered` — **is not produced by the recommended tools out of the
box.** That gap is stated here rather than discovered by a host whose declared
command silently reports a line ratio under a branch field name.

What partly closes it: branch data already exists in the coverage report, and a
**branch-aware adapter** intersects it with the diff's changed line ranges. That
adapter is a small amount of host work; no listed tool does it for you today.

**But the three formats are not equivalent, and only one supports per-branch
identity.** An earlier draft claimed all three emit identities, and named JaCoCo
fields that do not exist:

| Format | Carries | Ratio? | Per-branch identity? |
|---|---|---|---|
| **lcov** | `BRDA:<line>,<block>,<branch>,<taken>` — one record per branch | yes | **yes** — `(file, line, block, branch)`; an instrumenter ordinal, locatable but not nameable |
| **Cobertura** | `condition-coverage="50% (1/2)"` per line | yes | **no** — a per-line ratio. Only a condition index, and only where a producer extension (e.g. coverage.py's `missing-branches`) adds one |
| **JaCoCo** | per-line `mb`/`cb` attributes, `<counter type="BRANCH" missed covered/>` aggregates | yes | **no** — counts only. At a line with `mb="1" cb="1"` you cannot say *which* arm is uncovered |

The tokens `MISSEDBRANCHES`/`COVEREDBRANCHES` appear in no JaCoCo output; XML uses
`counter type="BRANCH"` plus per-line `mb`/`cb`, and CSV uses
`BRANCH_MISSED`/`BRANCH_COVERED`. A host implementing from the old text would have
grepped for fields that do not exist.

**So `uncovered_changed_branches` is best-effort per format, not mandatory
everywhere:**

- **lcov** — full ordinal identity per uncovered branch.
- **Cobertura** — condition index where the producer supplies one, otherwise
  `file, line, missed_count/total`.
- **JaCoCo** — `file, line, missed_count/total`. Per-branch identity is
  structurally unavailable; a Java host is conformant without it.

The **ratio** — which is what the gate arithmetic needs — is genuinely
implementable on all three. Only the actionable identity degrades.

| Layer | Required | Emits |
|---|---|---|
| **Branch layer** (primary) | yes, where the report carries branch records | `changed_branches_total`, `changed_branches_covered`, per-branch identities to the extent the format above allows |
| **Line layer** (secondary, context) | always | `changed_lines_total`, `changed_lines_covered` |

So the contract is a **capability**, not a tool:

> Declare a command that produces a coverage report in one of the formats above,
> with branch recording enabled, and intersect it with the changed-line ranges.
> If no slot is declared, this sensor is `inactive` — say so rather than
> reporting zero.

Two host facts decide which layer is available, and both must be recorded with
the result:

- **Branch recording is usually opt-in.** A run that did not enable it produces a
  valid report with no branch records, which reads exactly like fully covered
  code. Absence of branch records is not evidence of coverage.
- **Some toolchains have no branch mode at all.** On those the branch layer is
  structurally unavailable, not misconfigured, and the line layer is the whole
  result.

**When only the line layer is available**, report `changed_branch_ratio` as
`null`, gate on `changed_line_ratio` against the same floor, and label the finding
as line-based. Do **not** report a line ratio in a branch field — that is `INT-7`
under `<AI_DEV_SHOP_ROOT>/harness-engineering/quality/gate-validation-status.md`.

**Line-only is valid only where the toolchain emits no branch data.** Go's cover
tool is the clear case. It is **not** valid to declare `diff-cover` alone while
the host's own coverage report already contains `BRDA:` records, `mb`/`cb`
attributes, or `condition-coverage` — that is declining the primary metric, not
lacking it, and it is a **Required workflow declaration defect**. Without this
rule the branch layer is "required" in name only: any host preferring less work
gates on lines forever, at the same floor, and the case this sensor exists to
catch — one arm of a condition covered, the other never — is never detected.
Check the produced report for branch records before accepting a line-only
declaration.

**A slot that emits only an aggregate project percentage is a declaration
defect.** That is `coverage-quality.md`'s metric, not this one.

## Custody — the honest split

Coverage cannot follow the plain "the consumer recomputes everything" rule,
because producing a coverage report requires running the test suite, which is
expensive and is TestRunner's job. Rather than quietly exempt it, the work splits
at the point where cost changes:

| Step | Cost | Owner |
|---|---|---|
| Run the suite, emit a raw coverage report | expensive | **TestRunner** |
| Attribute that report to the diff and compute the ratios | **cheap** — a report plus a git diff | **Code Inspection, unconditionally** |

Code Inspection never accepts a diff-coverage *number* from anyone; it recomputes the
arithmetic itself from the raw report and its own `git diff` against the merge
base. What it cannot do is verify the raw report was produced by a real,
unmodified suite run without re-running the suite.

**That residual is real and is not closed here** — same limit
`code-structure-quality.md` states about the reviewing agent. Closing it needs a
trust boundary outside the agent-controlled workspace: a required CI job that
produces the coverage artifact with retained logs. Until a host provides that, a
coverage report is trusted input, and this sensor's guarantee is "the attribution
is correct," not "the report is authentic."

## Conformance Fixtures (required before this sensor may report a clean result)

| Fixture | Expectation |
|---|---|
| A diff adding a function with an `if/else` where only the `if` arm is tested | `changed_branches_total = 2`, `covered = 1`, ratio `0.5` |
| A diff adding a fully-tested function | ratio `1.0`, and the branches appear in the denominator — proves attribution reaches new files |
| A diff modifying one line inside a long-uncovered legacy function | that line counted as changed and uncovered — proves no accidental grandfathering |
| A diff touching only comments and whitespace | `changed_branches_total = 0`, ratio `null`, **no finding** — negative control |
| A coverage report older than the head commit | `INCONCLUSIVE` — proves staleness is detected rather than silently attributed |

A ratio of `1.0` computed from a report that covers none of the changed files is
`INCONCLUSIVE`, not `PASS`. As everywhere else in this harness, an unexercised
detector is not a clean result.

## Severity

| Finding | Severity | Disposition |
|---|---|---|
| Aggregate `changed_branch_ratio` below floor, ≥ 5 changed branches | `High` | `REQUIRED` |
| Any changed file below floor, ≥ 5 changed branches | `High` | `REQUIRED` |
| Changed file at 0% branch coverage with ≥ 1 changed branch | `High` | `REQUIRED` |
| `changed_line_ratio` below floor, **no line minimum**, when the unit has 0-4 changed branches | `High` | `REQUIRED` |
| `changed_line_ratio` below floor with ≥ 15 changed lines, when `changed_branch_ratio` is `null` (branch-null tooling) | `High` | `REQUIRED` |
| New coverage-ignore directive or exclusion on changed code | `High` | `REQUIRED` — `INT-2`, never capped |
| Test deleted, renamed, or skipped, removing changed code from the run | `High` | `REQUIRED` — `INT-5`, never capped |
| Floor lowered or branch minimum raised — where it affects an observed finding, or at any time without recorded approval | `High` | `REQUIRED` — `INT-2`, never capped |
| A line ratio reported in a branch field | `High` | `REQUIRED` — `INT-7`, never capped |
| Line-only declaration while the produced report contains branch records | `High` | `REQUIRED` (workflow) — declining the primary metric, not lacking it |
| Coverage report stale, missing, or not covering changed files | — | `INCONCLUSIVE`, never `PASS` |
| Slot undeclared | — | sensor `inactive`; note it in the report |

**Dispositions in this table apply at `validated` status.** This gate's current
status is in
`<AI_DEV_SHOP_ROOT>/harness-engineering/quality/gate-validation-status.md`; while
it is `unvalidated`, every `REQUIRED` above is capped at `RECOMMENDED`. Canonical
integrity findings (`INT-1`…`INT-9`) are never capped.

**A ratio of 1.0 earns no credit.** It establishes that every changed branch
executed at least once. It says nothing about whether anything was asserted.

## Brownfield

This sensor is the friendliest in the set to brownfield adoption: it never looks
at untouched code, so a repo at 12% overall coverage starts clean and is asked
only to test what it changes. That is the intended adoption path — the suite-level
gates in `test-design` are the ones that hurt on a legacy repo, and they are a
separate policy with a separate configuration.

## Known Limitations

- **Coverage measures execution, not verification.** A test that runs a branch
  and asserts nothing scores identically to one that asserts correctly. Mutation
  testing (`mutation-quality.md`) is the control for that; this sensor is not.
- **Branch attribution depends on the report's granularity.** Some tools report
  line coverage only, or collapse ternaries and short-circuits. Where branch data
  is absent, report `changed_branch_ratio` as `null` and fall back to the line
  ratio with an explicit note — do not silently present line coverage as branch
  coverage.
- **Per-hunk flooring is not specified, and applying it naively would weaken the
  gate.** The same-file padding residual is real: covered boilerplate added to
  the same file as untested logic still lifts that file's ratio. Per-hunk or
  per-function flooring is the correct answer in principle, but this document
  does not define unit selection, branch-to-unit mapping, aggregation, or a
  fixture — and mechanically applying the current thresholds per hunk would make
  nearly every unit fall under the branch minimum, universalising the small-unit
  path rather than tightening anything. Per-file is the enforced baseline and the
  residual stands; treat "apply it per hunk" as an open design item, not guidance
  to implement.
- **Diff attribution is line-based.** A change that moves a covered function
  without editing it can appear as fully changed and uncovered until the report
  is regenerated. Rename detection mitigates this; large restructures still read
  noisily.
- **The 80% floor and the 5-branch minimum are uncalibrated.**
- **The raw report is trusted input.** See Custody.

## Related

- `<AI_DEV_SHOP_ROOT>/framework/contracts/computational-controls.md` — the `diff_coverage` slot
- `coverage-quality.md` — trends and critical-path judgment; a different metric, not this one
- `mutation-quality.md` — whether the tests that ran actually verify anything
- `<AI_DEV_SHOP_ROOT>/skills/test-design/SKILL.md` — suite-level project gates
- `<AI_DEV_SHOP_ROOT>/harness-engineering/quality/coverage-integrity-policy.md` — the exclusion and directive rules
- `<AI_DEV_SHOP_ROOT>/harness-engineering/quality/gate-validation-status.md` — this gate's blocking authority
