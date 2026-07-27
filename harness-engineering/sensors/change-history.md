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

## Action-on-Fail

| Finding | Severity | Action |
|---|---|---|
| A file enters `T0` | Escalation | Observer reports; Refactor proposal recommended |
| Sustained churn rise in one module across 3+ windows | Escalation | Observer reports systemic instability |
| Revert frequency in a module above the repo's 90th percentile | Escalation | Observer reports; likely inadequate test coverage |
| Ownership concentration at 100% in a critical module | Advisory | knowledge-risk note to the human |
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

## Related

- `code-structure-quality.md` — supplies the complexity half of the hotspot join
- `agents/observer/skills.md` — owns scheduled sensor passes
- `agents/refactor/skills.md` — consumes hotspot tiers as targeting input
