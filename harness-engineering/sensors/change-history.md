# Sensor: Change History

Tracks **code churn, change frequency, revert frequency, and fix frequency** per
file and module, and joins them with complexity to produce a **hotspot ranking**
for Refactor targeting.

The research this harness draws on is consistent on one point: process metrics
predict defects better than static code metrics. This sensor supplies that layer.

## Sensor Definition

- **Class**: `computational`
- **Timing**: **scheduled only** — never a PR gate
- **Owner**: Observer → routes to Refactor and to the human for prioritization
- **Artifact**: `<ADS_MEMORY_ROOT>/.local-artifacts/sensors/change-history-<timestamp>.json`
- **Tooling**: **no executable command slot.** Pure `git log`; metrics 11,
  revert frequency, and fix frequency work on every repo with history. **Metric
  12 (previous defects per module) optionally requires one host declaration,
  `defect_link_pattern`** — without it that field is `null`, not zero. Do not
  read "no slot" as "no host cooperation at all."

## Why this never gates a PR

A change is not worse because the file it touches changes often. Churn is a
signal about **where to look**, not about whether this diff is acceptable.
Blocking on it would punish work in exactly the areas that need the most work.

It also produces nothing useful on greenfield code — which is most of what an AI
dev shop writes — so its value is concentrated in brownfield adoption and
long-lived repos.

## Metrics

All computed over a configurable window (default: 180 days).

| Metric | Definition | Command shape |
|---|---|---|
| **Change frequency** | commits touching the file | `git log --since=<window> --name-only --pretty=format: -- <path>` |
| **Code churn** | lines added + deleted | `git log --since=<window> --numstat --pretty=format: -- <path>` |
| **Revert frequency** | commits reverting a change to the file | `git log --since=<window> --grep='^Revert' --name-only` |
| **Fix frequency** | commits marked as fixes touching the file | `git log --since=<window> --grep='^fix' -i --name-only` |
| **Author count** | distinct authors | `git log --since=<window> --format='%ae' -- <path> \| sort -u` |
| **Ownership concentration** | share of commits by the top author | derived |
| **Co-change coupling** | files that change together — see below | `git log --since=<window> --name-only --no-merges` |

**Churn, change frequency, and revert frequency require no commit convention** —
they are computable on any repo. **Fix frequency does**: it depends on the host
using a recognizable marker (`fix:` conventional commits, or an issue-linking
convention). Where no convention exists, report fix frequency as `null` rather
than guessing, and say so in the artifact.

**"Previous defects per module"** — the strongest predictor in the literature —
requires commit-to-defect linking (an issue tracker reference in commit
messages). Most repos do not have this. This sensor reports it **only** when the
host declares a `defect_link_pattern` (e.g. `Fixes #\d+`); otherwise the field is
`null` and fix frequency is the available proxy. Do not present fix frequency as
a defect count.

## Hotspot Ranking

Joins this sensor's output with `code-structure-quality.md` artifacts.

```text
hotspot tier = f(change frequency, cognitive complexity)
```

**Ordered tiers, not a weighted score.** The research's suggested weighted
formula (`0.25×churn + 0.20×defects + …`) is invented precision — the weights are
assumed and calibrating them needs an outcome dataset this harness does not
collect. Tiers give the same ranking without the false authority:

**The tier input is "high change frequency", not "high churn".** This file
defines churn as *lines added + deleted* and change frequency as *commits
touching the file* — two different quantities — and the tier system uses the
commit count. An earlier draft called that input "high churn," which meant the
headline term of the tier table named the metric it does not use, ten lines from
the definition that says the two are not interchangeable. Two Observers reading
different sentences produced different tiers, defeating the reproducibility this
section exists for.

Read `T0`/`T1` as **high change frequency** throughout.

**"High" means the top quartile of this repository, not an absolute number.**
Absolute commit counts are meaningless across repos — 20 commits in 180 days is
high for a stable library and low for an active service. Define it relative to
the measured population:

- **High change frequency** = commits touching the file at or above the **75th
  percentile** of files in scope over the window.
- **Low change frequency** = below that percentile.
- The percentile is computed over files with at least one commit in the window;
  files with zero commits are `T3` by definition and are excluded from the
  distribution so they do not drag the quartile down.
- **Scope for the percentile** is the analyzed file set — state it in the
  artifact. A percentile computed over a subtree and one computed over the whole
  repo are different measurements and must not be compared across runs.
- **Module aggregation** — each metric aggregates as its own definition requires,
  and they are not interchangeable:
  - **Churn** (lines added + deleted) sums its files' **line counts**. An earlier
    draft summed commit counts here, which silently substituted change frequency
    for churn — two different metrics defined ten lines apart in this file.
  - **Change frequency** counts **distinct commit IDs** touching any file in the
    module. Summing per-file commit counts double-counts a single commit that
    touches five files in the same module, inflating exactly the large modules
    most likely to be flagged.
  - **Revert and fix frequency** aggregate as distinct commit IDs, same reason.
  - **Complexity** is the **maximum** of its functions' cognitive values, not the
    mean — one unmaintainable function makes a module hard to change regardless
    of how many simple siblings dilute the average.
  - State the module boundary used (directory, package manifest, or declared
    ownership glob) in the artifact.

| Tier | Condition | Meaning |
|---|---|---|
| `T0` | high change frequency **and** above complexity band | changes often, hard to change — refactor first |
| `T1` | high change frequency, within band | changes often, currently manageable — watch |
| `T2` | low change frequency, above band | complex but stable — refactoring may not pay |
| `T3` | low change frequency, within band | leave alone |

The 75th-percentile cut is a **starting value, not a calibrated one** — the same
caveat that applies to every threshold in this program. It is stated numerically
so two Observers produce the same tiers, not because the number is validated.

`T2` is the tier most often mis-prioritized: a complex file nobody touches is
rarely worth the risk of refactoring it.

Ranking is **advisory input to Refactor**, never a quality verdict and never a
block.

## Co-Change Coupling

Two files that always change together have a dependency. When the import graph
shows an edge between them, that dependency is declared and the pairing is
unremarkable. When it shows nothing, the dependency is real and undeclared —
the empirical form of a hidden coupling, and the one structural signal no
import-graph tool can produce.

This is the git-derived half of "related files should be grouped."
`<AI_DEV_SHOP_ROOT>/skills/package-extensibility/references/diagnostics.md`
(D12) owns the change-set measures that come from a ledger and routes the
history-derived one here, because this sensor owns git-derived signals. Do not
add a second git detector elsewhere — a rule with two homes drifts.

**Reference implementation:**
`<AI_DEV_SHOP_ROOT>/harness-engineering/sensors/scripts/co_change.py`. It is a
diagnostic, exits 0, and needs no command slot — like the rest of this sensor it
runs on `git log` alone.

### Definitions

For a pair of files A and B over the window, where `revs_X` is the number of
commits touching X:

```text
support    = commits touching both A and B
coupling   = support ÷ max(revs_A, revs_B)      symmetric
confidence = support ÷ revs_A                   asymmetric, one direction
```

**`coupling` divides by the busier file, not the quieter one.** Dividing by the
quieter file lets any hot file manufacture a perfect score against everything it
brushes past: a config touched in 200 commits and a helper touched in 3, all 3
alongside the config, reads as 1.00 coupling and is nothing. The two
`confidence` values are reported alongside because the asymmetry is the
interesting part — a helper that never moves without its caller, while the
caller often moves alone, is a different finding from two files genuinely welded
together.

### What is excluded, and why

Each of these is a way to report coupling that no one would recognise:

- **Merge commits.** A merge's file list is the union of a whole branch, which
  would pair every file in a feature with every other one.
- **Bulk commits** above a file cap (default 50, applied *after* filtering).
  Reformats, license sweeps and directory moves pair everything with
  everything. The count of dropped commits is reported — silently discarding
  evidence is how a diagnostic starts lying.
- **A named set of lockfiles and generated suffixes.** They co-change with
  everything that touches their generator; the pair is real and means nothing.
  **This is a fixed list, not general detection of generated code** — a
  project's own `generated/`, `proto/` or codegen output is *not* excluded
  unless the caller passes it to `--exclude`. Read a top pair involving
  machine-written files as a filtering gap, not a finding.
- **Same-module pairs**, by default. Files in one directory changing together
  is the expected case, not a finding.
- **Shallow clones entirely.** Git reports a shallow boundary commit as touching
  every file in the snapshot, so one commit would pair the whole tree at
  coupling 1.00. The sensor reports `INACTIVE` rather than that artefact.

### Reading the result

A pair is only interesting once the import graph has been asked about it. Three
states, and conflating the last two is the error to avoid:

| Link | Meaning |
|---|---|
| `linked` | an import edge already explains the pair — not a finding |
| `hidden` | co-change with no import edge, **both components present in the graph** — the finding |
| `ungraphed` | **either** component is missing from the import graph, typically an unread language |
| `same-module` | the pair does not cross a component boundary |
| `unknown` | no import graph was supplied |

**`unknown` is not `hidden`, and `ungraphed` is not `hidden`.** Without an
import graph nothing can be called an undeclared dependency; reporting one
anyway converts a coverage gap into a finding.

**`hidden` requires BOTH components to be in the graph.** If either is missing,
the scanner never read it, so no edge to it could have been observed and its
absence is evidence of nothing. Requiring only *one* endpoint to be present —
an earlier rule — made a Python component paired with a Go component come back
`hidden`, escalating "this language was never scanned" as an undeclared
dependency. A **truncated** graph is rejected outright for the same reason:
every missing component makes its pairs look unlinked.

The script takes the JSON from
`<AI_DEV_SHOP_ROOT>/skills/codebase-analysis/scripts/main_sequence.py` as its
import graph, at **component granularity** — so a `hidden` pair means no import
edge between the two *components*, which is a coarser claim than "these two
files do not import each other" and must not be reported as the finer one.

### Thresholds

Defaults are `support >= 5` and `coupling >= 0.5`. Both are **starting values,
not calibrated ones** — the same caveat that applies to every threshold in this
program. They are stated numerically so two Observers produce the same pairs,
which is a different property from being correct.

### Inactive is a result, and it is not zero

Four different facts used to print as one "no commits" line. They are reported
separately because they call for different responses:

| Status | Meaning |
|---|---|
| `ok` | measured |
| `shallow` | shallow clone; deepen it, or pass `--allow-shallow` and distrust every row |
| `no-history` | the repository genuinely has no commits |
| `empty-window` | the repository has commits, none in this window — **check `--since`** |
| `git-error` | git failed; this is never a clean scan |

`empty-window` exists because **git does not reject an unparseable date.** It
substitutes one, so a typo in `--since` silently measures a window nobody chose.
A year outside git's representable range is worse still: it overflows and
returns the entire history.

Commits dropped by the file cap and commits touching only excluded files are
counted and reported separately too. A window whose every commit was a bulk
sweep is not an empty repository, and saying so hid the reason.

### Why this never gates

Same reason as the rest of this sensor: co-change describes where a codebase is
awkward, not whether a diff is acceptable. It is also the metric most likely to
push toward a **worse** design if enforced — the obvious way to satisfy it is to
merge two files that change together, which is right when they are one concern
and wrong when they are two concerns sharing a release cadence. It reports; a
human decides.

## Action-on-Fail

| Finding | Severity | Action |
|---|---|---|
| A file enters `T0` | Escalation | Observer reports; Refactor proposal recommended |
| Sustained churn rise in one module across 3+ windows | Escalation | Observer reports systemic instability |
| Revert frequency in a module above the repo's 90th percentile | Escalation | Observer reports; likely inadequate test coverage |
| Ownership concentration at 100% in a critical module | Advisory | knowledge-risk note to the human |
| A `hidden` co-change pair crossing a declared architecture boundary | Escalation | Observer reports; Software Architect adjudicates whether the boundary or the coupling is wrong |
| A `hidden` co-change pair sustained across 3+ windows | Advisory | Observer reports; Refactor targeting input |
| No git history (shallow clone) | Advisory | sensor inactive; say so rather than reporting zeros |

## Known Limitations

- **Greenfield blindness.** Produces nothing meaningful until a repo has history.
  Expect it to be inert on new work.
- **Rename opacity.** `git log --follow` handles single-file renames; large
  restructures break continuity and will read as new files with no history.
- **Fix frequency is a proxy, not a defect count**, and is `null` without a commit
  convention. Do not let it be reported as defects.
- **Windowing is arbitrary.** 180 days is a default, not a calibrated value. So
  are the 75th/90th percentile cuts — they are specified numerically so the
  sensor is reproducible across Observers, which is a different property from
  being correct.
- **Percentiles are repo-relative.** A `T0` in a healthy repo and a `T0` in a
  chaotic one mean different things. Tiers rank within a repository; they do not
  compare across them.
- **Unvalidated.** No evidence yet that these tiers predict anything in this
  harness specifically.
- **Co-change cannot distinguish coupling from cadence.** Two files edited in
  the same commit because they are one concern, and two edited together because
  one person batches unrelated work, produce identical evidence. The measure
  ranks candidates for a human to read; it does not identify a dependency.
- **Co-change is blind to the reason a pair is `hidden`.** A missing import edge
  can mean an undeclared dependency, a deliberate duplication, a shared external
  contract, or a language the import scanner does not read. Only the last is
  detected, and it is reported as `ungraphed`.
- **Renames are detected but not followed.** The rename commit reports only the
  new path, so no file is ever paired with its own former name. But commits
  before the rename still carry the old path, so a renamed file's history is
  **split across two names** and both halves under-report. Stitching that
  identity is not implemented. Note this is the opposite of an earlier claim
  that rename *detection* should be off: with `--no-renames` git emits both the
  old and the new path on the rename commit, which manufactures exactly the
  false pair that option was said to prevent.
- **Path exclusion is a fixed list.** See "What is excluded" — project-specific
  generated directories need `--exclude`.

## Related

- `code-structure-quality.md` — supplies the complexity half of the hotspot join
- `dependency-structure.md` — the declared import graph a `hidden` pair is judged against
- `scripts/co_change.py` — reference implementation of the co-change metrics
- `agents/observer/skills.md` — owns scheduled sensor passes
- `agents/refactor/skills.md` — consumes hotspot tiers as targeting input
- `<AI_DEV_SHOP_ROOT>/skills/package-extensibility/references/diagnostics.md` — D12 routes its history-derived measure here
