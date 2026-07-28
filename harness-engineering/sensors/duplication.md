# Sensor: Duplication

Detects **copy-paste duplication** in changed code and delta-gates newly
introduced clones above a size threshold.

This is the sensor in this set with the **highest false-positive risk and the
most dangerous failure mode when over-enforced**, so its default posture is
narrower than the others: it reports broadly and gates narrowly.

## Sensor Definition

- **Class**: `computational`
- **Timing**: PR (changed files vs. the rest of the tree) + scheduled (whole-repo trend)
- **PR owner**: **Code Inspection** (executes the declared `duplication` slot; same
  custody rule as `code_metrics`)
- **Scheduled owner**: Observer → routes to Refactor
- **Artifact**: `<ADS_MEMORY_ROOT>/.local-artifacts/sensors/duplication-<feature-id>-<timestamp>.json`

## Why this gates narrowly

Duplication is the metric most likely to push an agent toward a **worse** design
than the one it flagged. Three specific reasons, all of which shape the gate:

1. **Two occurrences is not evidence.** The rule of three exists because the
   second occurrence rarely establishes which parts are essential and which are
   incidental. Extracting at two sites regularly produces an abstraction with a
   boolean parameter that means "am I caller A or caller B" — strictly worse than
   the duplication.
2. **Duplication pressure is the mirror image of the fragmentation hole.**
   `code-structure-quality.md` documents that complexity gates push agents toward
   splitting functions into too many tiny helpers. A duplication gate pushes in
   the opposite direction: merging things that only look alike. Both are metric
   satisfaction at the cost of design. Running both gates without acknowledging
   the tension would leave an agent squeezed between them.
3. **Some duplication is structurally correct.** Test setup, fixtures, DTOs,
   migrations, generated clients, and i18n tables duplicate by nature. Coupling
   two tests so a change to one breaks the other is a real cost paid to satisfy a
   number.

So: **coincidental similarity is reported, never gated.** Only large, exact-or-
renamed clones the change actually introduced can block.

## What is counted

Clone types, using the standard taxonomy:

| Type | Meaning | Handled |
|---|---|---|
| **Type-1** | identical apart from whitespace and comments | **gated** |
| **Type-2** | identical apart from identifier/literal renaming | **gated** |
| Type-3 | Type-2 with added, removed, or reordered statements | reported only — tool agreement is poor |
| Type-4 | semantically equivalent, structurally different | not detected by any tool listed; out of scope |

Gating only Type-1 and Type-2 is deliberate. Those are the cases where "this was
copied" is a defensible mechanical claim. Type-3 detection depends on a gap
threshold that differs per tool and per run, and is not a stable basis for a
block.

## Thresholds

**All values below are provisional defaults, not calibrated thresholds.** Like
the complexity bands, they are a starting point pending eval evidence, and a host
may tighten or loosen them in its declaration.

| Parameter | Default | Meaning |
|---|---|---|
| Minimum clone size | **50 tokens** and **5 lines** | below this, matches are noise — import blocks, guard clauses, standard boilerplate |
| Occurrences to gate | **3** | the rule of three; a 2-site clone is reported, never gated |
| Gate scope | changed files only | a clone entirely between untouched files is not this change's finding |

A 2-site clone above the size threshold is a **`RECOMMENDED`** finding with an
explicit note that extracting it may be premature. That wording is required — a
Recommended finding that reads as an instruction to deduplicate reintroduces the
problem the threshold exists to avoid.

## Excluded scopes

These paths duplicate by nature and are excluded by default. Exclusions remain
visible in the artifact.

- Generated and vendored code
- Test fixtures, factories, and setup blocks
- Database migrations
- Type/interface/DTO declarations and schema definitions
- i18n and locale tables
- Lock files and snapshots

Test *bodies* are **not** excluded — three near-identical test bodies are often a
missing parameterized case, which is worth reporting. Test *setup* is excluded,
because coupling setup across tests to satisfy a metric is a known
false-economy.

Adding or broadening an exclusion is `INT-2` in
`<AI_DEV_SHOP_ROOT>/harness-engineering/quality/gate-validation-status.md` — a
finding when it lands in a change where it affects an observed result, or at any
time without recorded human approval.

## Tools

The host declares a command in the `duplication` slot of
`<AI_DEV_SHOP_ROOT>/framework/contracts/computational-controls.md`.

### The scan scope is the whole tree, not the changed files

**This sensor is the one exception to `{files}`-scoped invocation, and getting it
wrong makes the central gate undetectable.**

Clone detection compares fragments *against each other*. A tool given only the
changed files can only find clones **among** those files. The most common real
case — a diff adds a third copy of something that already exists twice in files
it never touched — appears to that tool as a single occurrence, and the
three-site crossing this sensor exists to catch never fires.

So the invocation is:

```text
scan the full source scope at the merge base   -> base clone groups
scan the full source scope at head             -> head clone groups
attribute to the diff by asking whether any site of a group is in changed scope
```

`{files}` narrows the *attribution*, never the *scan*. A declared command that
passes changed files as the tool's scan path is a **declaration defect** and its
zero-finding results are `INCONCLUSIVE`.

This costs more than the other sensors' scoped runs. If a full scan is too slow
for PR context on a large repo, say so and mark the result `INCONCLUSIVE` — do
not narrow the scan and report the result as clean.

So the contract is a **capability**, not a tool:

> Declare a command that emits, for every clone group, **both ends** with file and
> line ranges, scanning the full source root. Prove it with the conformance
> fixtures below. If it cannot, this sensor is `inactive` — say so rather than
> reporting zero.

| Requirement | Why |
|---|---|
| Emits both sites of every clone, with file and line ranges | the delta logic below compares clone groups between base and head; one end is not a group |
| Scans the full source root | a detector pointed at the changed files alone cannot see the other end of a pair, per the scan-scope rule above |
| Records its token and line minimums | what a zero result proves depends on the threshold it ran at |

A detector that cannot emit **stable clone identities across revisions** is still
usable: compare by recomputing at base and head rather than by matching group ids.
Record which mode was used, because the two do not fail the same way.

A command that reports only a duplication *percentage* cannot support this gate
at all.

**A slot whose command emits only an aggregate ratio is a declaration defect.** A
percentage cannot be attributed to a change, cannot be delta-compared, and is the
form of this metric most often gamed by adding undertested files to the
denominator. Report it as a Required workflow finding against the contract.

## Conformance Fixtures (required before this sensor may report a clean result)

**An under-scoped command is indistinguishable from a clean repository.** A
`duplication` command whose glob does not cover the changed files, or that points
the tool at a subtree the change did not touch, exits 0 and emits valid, empty,
parseable JSON. Nothing in the output distinguishes "no clones" from "looked
nowhere." This is the same failure mode `type-safety.md` documents for
un-activated type-aware rules, and it is the cheapest way to defeat this sensor —
cheaper than raising a threshold, which is itself a finding.

| Fixture | Expectation |
|---|---|
| Two files in the **changed scope** containing an identical 60-token function body | reported as one Type-1 clone group with both sites — **proves the command reaches the changed files** |
| The same pair with every identifier renamed | reported as Type-2, same group size |
| A pair 30 tokens long | **not** reported — proves the size threshold is the declared one, not a tool default |
| A three-site group where the third site is added by the diff | breach raised, with `base_occurrences = 2` and `head_occurrences = 3` recorded |
| **Two sites in files the diff does not touch, third site added in a changed file** | breach raised — **proves the scan covers the whole tree, not just `{files}`.** A command scanning only changed files reports one occurrence here and misses the breach entirely |
| A four-site group where the diff adds a fifth site | breach raised — proves growth past three still gates |
| A group standing at three sites that the diff edits without adding a site | **not** a breach — editing duplicated code is not duplicating code |

A zero-clone result without a passing fixture run is `INCONCLUSIVE`, not `PASS`.
Report the difference; do not let an unexercised detector read as a clean result.

Re-run fixtures on any tool or threshold change, and compute base and head with
the same tool version and configuration.

## Gate Logic

Delta-based against the VCS merge base, consistent with every other gate here.
No stored baseline file.

```text
BREACH = a Type-1 or Type-2 clone group exists
         AND at least one of its sites is in the changed scope
         AND the group meets the size threshold
         AND head_occurrences > base_occurrences
         AND head_occurrences >= 3
```

The condition is **growth past the rule of three, not group novelty.** Two
earlier drafts got this wrong in opposite directions and both are worth recording
so neither returns:

<!-- historical: the two rejected predicates, kept so neither returns silently -->
<!-- historical -->
- *"the group is not present in the merge base"* — a two-site group **is** present <!-- historical -->
  at base, so adding the third site failed the condition and the rule-of-three
  catch could never fire.
<!-- historical -->
- *"`base_occurrences < 3`"* — fixed that, but `3 < 3` is false, so a group that <!-- historical -->
  already had three sites could be copied to five without breaching. It gated the
  crossing and then ignored every site after it.

`head_occurrences > base_occurrences` catches both: any diff that **adds a site**
to a group standing at three or more. A group that stays at three, or shrinks,
does not breach.

- Clone-group identity across base and head is matched on the **normalized token
  sequence**, not line numbers. Line ranges shift on any edit.
- **Relocation is not duplication — but only when the site count did not grow.**
  A group is relocated when `head_occurrences == base_occurrences` **and** every
  head site pairs 1:1 with a base site (moved or unmoved). It is then reported as
  relocated and does not breach. Staged migrations that temporarily hold two
  copies are the common case and must not block.

  **The pairing condition is load-bearing.** Group identity is already matched on
  the normalized token sequence, so "same content as a base-side group" is true
  of *every* matched group — it discriminates nothing on its own. Without the
  equal-count requirement, a diff that adds a third site *while also* moving one
  existing site to a renamed file satisfies the carve-out as written and can be
  argued as "just relocated," swallowing the growth rule this gate exists to
  enforce. Any increase in site count is evaluated under the gate regardless of
  how many sites moved.
- A change that adds a **third** site to an existing 2-site clone breaches — that
  is the rule of three being crossed by this diff, and it is the intended catch.
- A change that touches one site of an existing clone group without adding a site
  does not breach. Editing duplicated code is not the same as duplicating code.
- Pre-existing clone groups entirely in untouched files are irrelevant and never
  block.
- If the tool version or threshold configuration changed in the same diff, the
  result is `INCONCLUSIVE` for that run — a threshold change silently rewrites
  every count.

**Loosening a declared threshold is not a fix.** Raising `--min-tokens` or
`--min-lines` to clear a finding is scope narrowing and is a `REQUIRED` finding
— `INT-2` in the gate registry, exactly as widening a coverage exclusion is.
(Note the direction: a *higher* min-tokens value detects *less*.)

**Deliberate perturbation to change clone type is gaming.** Because Type-3 is
reported and never gated, inserting a no-op statement, reordering independent
lines, or renaming to break a normalized-token match converts a gated Type-1/2
group into an ungated Type-3 one while leaving the duplication in place. Where a
diff's only effect on a clone group is to move it across the Type-2/Type-3
boundary without changing behavior, that is a `REQUIRED` finding under the
gate registry as `INT-6`, a sibling of the `INT-2` rule governing threshold raising. This is
integrity finding `INT-6` and is never capped by gate status.

## Severity

| Finding | Severity | Disposition |
|---|---|---|
| Clone group crossing to >= 3 sites above threshold, in changed scope | `Medium` | `REQUIRED` |
| New 2-site clone above threshold | `Low` | `RECOMMENDED` — with the premature-extraction caveat stated |
| Threshold raised or exclusion broadened — in a change where it affects an observed finding, or at any time without recorded approval | `High` | `REQUIRED` — `INT-2`, never capped |
| Perturbation moving a group from Type-2 to Type-3 with no behavior change | `High` | `REQUIRED` — `INT-6`, never capped |
| Scan scoped to changed files rather than the full tree | — | `INCONCLUSIVE`; declaration defect |
| Type-3 match arising naturally | — | reported only, never a finding |
| Pre-existing clone group, untouched | — | advisory note only |
| Relocated clone group | — | advisory note only |
| Zero clones without a passing conformance fixture | — | `INCONCLUSIVE`, never `PASS` |

**Dispositions in this table apply at `validated` status.** This gate's current
status is in
`<AI_DEV_SHOP_ROOT>/harness-engineering/quality/gate-validation-status.md`; while
it is `unvalidated`, every `REQUIRED` above is capped at `RECOMMENDED`. Canonical
integrity findings (`INT-1`…`INT-9`) are never capped.

Note the top row is **`Medium`/`REQUIRED`**, not `High`. Duplication is a
maintainability cost, not a correctness defect, and it is the one gate here whose
mechanically-correct answer is sometimes "leave it duplicated." As with every
mechanical finding, the severity may not be downgraded by a reviewing agent — but
a **justification is upheld more readily here than elsewhere**, and "these three
sites will diverge" is a legitimate one when the reviewer can say how.

**A zero clone count earns no credit.** It establishes that this detector found
nothing.

## Custody

Identical to `code-structure-quality.md`. Code Inspection executes the command on
every reviewed change and its run is authoritative. Programmer may run it as an
advisory preview and must never restate results as free text in a handoff.

## Brownfield

First run records nothing and blocks nothing — the merge base supplies the
comparison. A repo with 300 existing clone groups blocks on group 301 only if the
change introduces it in a file it touched.

## Interaction with the complexity gates — read this before acting on a finding

`code-structure-quality.md` gates cognitive complexity and nesting. This sensor
gates duplication. **They pull in opposite directions**, and an agent optimizing
both without judgment will oscillate:

- Extracting a shared helper to clear a duplication finding can raise the helper's
  cognitive complexity past the gate, because it now handles every caller's case.
- Splitting a function to clear a complexity finding can create near-identical
  helpers that trip the duplication gate.

When the two conflict, the resolution is **not** to satisfy both. It is to record
a justification against one of them and say which cost was chosen and why. A
change that satisfies both by producing a parameterized helper whose parameters
are caller identities has satisfied neither — that is the specific outcome this
section exists to prevent. Code Inspection adjudicates; it does not require a clean
sweep of both gates.

## Action-on-Fail

| Finding | Severity | Action |
|---|---|---|
| Clone group grown past 3 sites, no upheld justification | Required | Code Inspection reports at fixed severity; **blocks only at `validated` gate status** (see the registry); otherwise routes to Programmer or Refactor as `RECOMMENDED` |
| Threshold raised or exclusion broadened without approval | Required | `INT-2`; blocks regardless of gate status; flags to the human |
| Type-2 → Type-3 perturbation with no behavior change | Required | `INT-6`; blocks regardless of gate status |
| New 2-site clone above threshold | Advisory | Recommended finding, with the premature-extraction caveat |
| Slot declared but command emits only an aggregate ratio | Required (workflow) | `INCONCLUSIVE`; fix the declaration |
| Slot undeclared | Advisory | Note absence in the CR report; gates are not enforced |

## Known Limitations

- **Type-4 (semantic) duplication is invisible.** Two functions that do the same
  thing by different means are the most expensive kind of duplication and no tool
  listed here finds them.
- **Token thresholds are arbitrary.** 50 tokens / 5 lines is a common default,
  not a calibrated one. Tuning it changes results substantially and there is no
  evidence base here for a better value.
- **Cross-language clones are not detected** by the token-based tools; a
  TypeScript validator duplicated into a Python service is invisible.
- **The rule-of-three default will miss real duplication.** A 2-site clone of 200
  lines is usually a genuine problem, and this sensor will only recommend it.
  That is a deliberate false-negative trade against the false-positive cost.
- **Unvalidated.** Thresholds, tier assignments, and dispositions are provisional
  until the eval runs.

## Related

- `<AI_DEV_SHOP_ROOT>/framework/contracts/computational-controls.md` — the `duplication` slot
- `code-structure-quality.md` — the complexity gates this sensor is in tension with
- `<AI_DEV_SHOP_ROOT>/harness-engineering/quality/gate-validation-status.md` — `INT-2` (threshold/exclusion loosening) and `INT-6` (classification-boundary perturbation)
- `<AI_DEV_SHOP_ROOT>/skills/refactor-patterns/SKILL.md` — what not to refactor
