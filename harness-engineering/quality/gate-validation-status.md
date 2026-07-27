# Gate Validation Status

Single source of truth for **which mechanical gates may block and which may not**.

A gate is a detector plus a threshold. This file records, per gate, whether that
pair has earned blocking authority, and defines the closed set of integrity
findings that block regardless.

**No sensor may grant itself blocking authority.** A sensor doc describes what a
gate *would* do once validated; this file decides whether it is there yet. A
sensor that declares its own exemption from this file is defective — see
Canonical Integrity Findings.

## Why this exists

Every mechanical gate in this harness was designed before any eval ran. Their
thresholds are inherited or invented, every one of them. Each sensor states
this honestly in its own Known Limitations, and then several went on to declare
`REQUIRED` dispositions anyway.

That is the contradiction this file resolves: **an unvalidated threshold does not
get blocking authority just because the document describing it is
well-specified.**

## Status values

Named `unvalidated` / `validated` / `inactive` — **deliberately not
`advisory`/`blocking`.** Those two words already mean something else in
`<AI_DEV_SHOP_ROOT>/framework/contracts/architecture-fitness.md`, where a **host**
declares an individual boundary rule's `Severity: blocking | advisory`. That is a
per-rule authoring choice; this is a harness-wide validation state. Two axes, and
reusing one vocabulary for both made `dependency-structure.md` read as though a
host-declared `blocking` rule currently blocks, when the sensor's own state
overrides it.

| Status | Maximum disposition | Meaning |
|---|---|---|
| `unvalidated` | `RECOMMENDED` | Detector runs, findings are reported at full severity, **nothing blocks**. Default for every new gate. |
| `validated` | `REQUIRED` | Passed the promotion criterion. May block. |
| `inactive` | — | No detector available on this stack, or slot undeclared. Report absence; **never report as clean**. |

**The two axes compose, and the stricter wins.** A host-declared `blocking`
boundary rule violated in changed scope is `REQUIRED` *at gate status
`validated`*; while the gate is `unvalidated` it is still capped at
`RECOMMENDED`. A host-declared `advisory` rule is `RECOMMENDED` at any gate
status. Neither axis alone determines the outcome.

**The cap is on disposition, not severity.** A `High`-severity `unvalidated`
finding keeps its `High` and is still worth fixing; it just does not stop the
pipeline. A reviewing agent may not route an `unvalidated` finding as `REQUIRED`,
and may not describe it as blocking.

## Current status registry

| Gate | Sensor | Status | Why |
|---|---|---|---|
| Cognitive complexity, new or worsened | `code-structure-quality.md` | `unvalidated` | bands are inherited and provisional; no eval has run |
| Max nesting depth, new or worsened | `code-structure-quality.md` | `unvalidated`, and `inactive` wherever no nesting adapter is declared | see the sensor's capability contract |
| New dependency cycle in a `blocking`-severity scope | `dependency-structure.md` | `unvalidated` | no conformance evidence retained |
| New violation of a `blocking`-severity boundary rule | `dependency-structure.md` | `unvalidated` | same |
| New Tier A unsafe type operation | `type-safety.md` | `unvalidated` | tier assignment is a design judgment, unmeasured |
| Clone group growth | `duplication.md` | `unvalidated` | thresholds arbitrary; highest known false-positive risk in the set |
| Changed-code branch coverage | `changed-code-coverage.md` | `unvalidated` | floor is a starting value, not calibrated |
| Per-file zero-coverage rule | `changed-code-coverage.md` | `unvalidated` | same gate family, listed separately because it fires independently of the aggregate. **Threshold lives in the sensor; this registry names gates and their status, never their numbers** |
| Mutation score regression > 10% vs baseline | `mutation-quality.md` | **`validated` by legacy, not by eval** | pre-existing hard blocker. See Legacy Gates. |
| Suite coverage below 98/90/80 | `skills/test-design/SKILL.md` | **`validated` by legacy, not by eval** | pre-existing hard blocker. See Legacy Gates. |

**Cyclomatic complexity and function size never appear here.** They are reported
and never gated by design, at any status.

### Legacy gates

The last two rows block today and were never validated against a labeled set
either. They are listed so this registry is **complete** — an earlier draft
excluded them, which made the claim "every gate is unvalidated" false and left a
reviewer following this file disagreeing with TestRunner.

They are **not** demoted here. Demoting a pre-existing hard blocker is a scope
decision that has not been made, and silently changing what TestRunner enforces
from a file it does not read would be worse than the inconsistency. Recorded as
an open item below.

## Canonical Integrity Findings

These block **regardless of gate status**, because they are not threshold
judgments — they are findings about the measurement itself, and their correctness
does not depend on any unvalidated band.

**This list is closed.** A sensor may not invent a local exemption. If a sensor
needs a new integrity finding, it is added here first and the sensor references
the ID. Without this rule any sensor could escape the cap by labeling a
threshold-adjacent judgment "integrity."

| ID | Finding |
|---|---|
| `INT-1` | Weakening compiler or lint strictness without recorded approval |
| `INT-2` | Loosening or narrowing **any** declared threshold, scope, or exclusion — **either** in a change where it affects an observed finding, **or** at any time without recorded human approval. Covers duplication `--min-tokens`/`--min-lines`, the cognitive or nesting bands embedded in a `code_metrics` command, the `diff_coverage` floor or minimum-branch count, and any coverage exclusion |
| `INT-3` | Downgrading a declared `architecture-fitness` rule's `Severity` from `blocking` to `advisory` without recorded approval |
| `INT-4` | Adding a suppression comment or directive over an existing violation and reporting it as a fix |
| `INT-5` | Deleting, renaming, or skipping a test so its source file leaves a measured scope |
| `INT-6` | Deliberate no-op perturbation to move code across a detector's classification boundary — e.g. inserting a dead statement to convert a gated Type-1/2 clone into an ungated Type-3 |
| `INT-7` | Reporting a metric value with no authoritative run behind it, **or reporting a value under a field that measures something else** — e.g. a line-coverage ratio placed in a branch-coverage field. A mislabelled value from a real run is still a misrepresented measurement |
| `INT-8` | Reporting an unverified or detector-inactive zero as `PASS` rather than `INCONCLUSIVE` |
| `INT-9` | A changed test **executes** behaviour it does not **verify** — either by weakening or removing assertions that previously checked it, or by covering newly-changed code with a test that asserts nothing about the outcome. Fires where it affects an observed coverage or mutation result, or at any time without recorded approval of the assertion change. The finding must name the specific behaviour now unverified |

`INT-9` exists because `INT-5` protects only against a test being *removed* from
scope. Gutting the assertions inside a test that stays put defeats coverage and
mutation evidence simultaneously while every count holds steady, and it was
reachable under no other ID. It is the assertion half of the rule
`coverage-integrity-policy.md` states as "delete, weaken, rewrite, or replace
tests or assertions."

**It deliberately covers assertion-free-from-birth tests, not just gutted ones.**
An earlier draft keyed on behaviour "previously verified," which left the
cheapest version of the attack open: write a *new* test that calls the new code,
asserts nothing, and banks the coverage. Nothing was weakened, nothing was
deleted, the run is real — so `INT-5`, `INT-7`, and the old `INT-9` were all
silent, and the coverage-integrity policy's own prohibition on tests that only
execute lines was capped like any ordinary finding. Keying on the *gap between
executed and verified* covers both shapes.

**On the judgment risk.** "Weakening" is not fully mechanical, and this is the
one member of the closed set that leans on reviewer judgment — a real cost,
accepted deliberately. Two guards keep it from swallowing legitimate work:
replacing an over-specified assertion with a narrower one that still checks the
same behaviour is **not** `INT-9` (de-brittling is encouraged by this toolkit's
own test-design doctrine), and the two-prong structure means an approved
assertion change outside an affected result does not fire. The finding must name
the behaviour now unverified; if it cannot, there is no finding.

`INT-2` is deliberately written to cover **every** gate rather than enumerating
tools. An earlier draft protected only duplication and type-safety thresholds,
leaving cognitive/nesting bands, boundary severities, and the coverage floor
tamperable the moment their gates are promoted.

**`INT-2` is two-pronged on purpose.** An intent-only trigger ("loosened to clear
a finding") depends on motive the measured party narrates, and it admits a
two-commit game: loosen the threshold in a clean diff where no finding exists,
land the offending code later, and neither change ever "cleared a finding." An
approval-only trigger would flag legitimate calibration work. Requiring **either**
condition closes both: unapproved loosening is a finding whenever it happens, and
approval is no defence when the loosening lands in the same change as the finding
it removes. Recording the approval is what separates governance work from gaming,
and it must precede the change, not accompany it.

`INT-1`, `INT-2` (coverage portion), `INT-4`, and `INT-5` overlap with
`<AI_DEV_SHOP_ROOT>/harness-engineering/quality/coverage-integrity-policy.md`,
which is **coverage-scoped**. The non-coverage rules here are stated in this file
because that policy does not contain them — citing it as their source, as an
earlier draft did, sent a reader to a document where the rule does not appear.

## Promotion — the ablation canary

Promoting a gate from `unvalidated` to `validated` requires passing the
**ablation canary**.

The canary answers one question: **does this detector actually detect?** A gate
that has never been shown to fire cannot be distinguished from a gate that
cannot fire, and the failure is silent — a detector whose entry point misses the
changed code exits successfully and emits an empty finding list that reads
exactly like clean code. "Zero findings" is evidence only when the detector is
known to have been live.

### The four controls

Every control must pass, against the detector the host has actually declared,
at the version it will run.

| # | Control | Requirement |
|---|---|---|
| 1 | **Injection** | Plant each defect the gate claims to catch. The gate must fire and name it. Where a sensor already specifies conformance fixtures, those are the injection set — do not invent a parallel one. |
| 2 | **Negative** | Run against code that is clean *and* against the idioms this toolkit itself mandates. The gate must stay quiet. This measures the false-positive rate; the exhaustive-`switch` case is the known trap. |
| 3 | **Ablation** | Cripple the detector — narrow its entry point so it cannot reach the planted defect — and re-run. The result **must differ** from the healthy run. If it does not, the findings never depended on the detector traversing the code, and no zero result from this gate means anything. |
| 4 | **Sensitivity** | The threshold must decide something. The planted defect must be a finding on the strict side of the threshold and not on the permissive side. A gate that fires identically at every threshold is reporting the detector's presence, not the measurement. |

Control 3 is the canary proper and the reason for the name. Controls 1, 2 and 4
can all pass against a detector that is quietly scoped to the wrong tree.

### What a promotion must record

A promotion commit contains **both** the status change and the canary artifact.
The registry is a writable file in a shared workspace; a status flipped without
its evidence in the same commit is a claim, not a validation.

The artifact records: the gate, the sensor, the detector command and its pinned
version, every control with its expectation and observed output, the verdict,
and the explicit human approval. Re-run the canary on any detector or ruleset
change — a passing artifact describes one detector at one version and expires
when either moves.

### Scope of a PASS

A passing canary means the gate **can fire and can stay quiet**. It does not
establish that the gate's threshold is well-chosen, that its disposition is
right, or that its scope matches the risk. Those remain judgment, and the canary
does not launder them into evidence.

### Pilot

`harness-engineering/canary/` runs this specification end to end for the
dependency-cycle gate, executing the conformance fixtures already specified in
`dependency-structure.md`. It exists to prove the loop is cheap and real, and it
is mutation-tested: five deliberately broken detectors each fail the control that
should catch them.

**It does not promote anything.** Its subject is a pilot stand-in detector, not a
host's declared `dependency_graph` command, so the dependency-cycle gate remains
`unvalidated` in the registry above. Promoting it requires running these same
four controls against a real declared detector on a real project.

**Consequence: no gate in the registry is promoted yet.** The criterion now
exists; nothing has met it.

## How a sensor references this

A sensor's severity table states the disposition the gate would carry at
`validated` status, then defers:

> Dispositions in this table apply at `validated` status. This gate's current
> status is in
> `<AI_DEV_SHOP_ROOT>/harness-engineering/quality/gate-validation-status.md`;
> while it is `unvalidated`, every `REQUIRED` above is capped at `RECOMMENDED`.
> Canonical integrity findings (`INT-1`…`INT-9`) are never capped.

**Action-on-Fail tables must carry the same qualifier.** A table that says "Code
Review blocks" without it contradicts the sensor's own severity section.

Do not duplicate the status value into the sensor doc — two copies drift, and the
copy an agent happens to read would decide whether a pipeline blocks.

## What this means today, stated plainly

**Nothing added by the code-quality metrics program currently blocks.** Every one
of its gates is `unvalidated`. A change can introduce a dependency cycle, unsafe
type operations, duplication, deep nesting, and untested branches, and every
finding lands as `RECOMMENDED`.

What still blocks: the `INT-*` findings above, and the two legacy gates. So the
harness currently enforces **"do not misrepresent the measurement"** and the two
pre-existing test gates — not **"do not write the bad code."** That is the
intended consequence of shipping unvalidated detectors, and it is written here
plainly because it is the single most important fact about the harness's current
state.

## Open Dependencies

- **The ablation canary is unspecified.** Blocks all promotion. Highest-priority
  open item.
- **No eval has run** against any gate in the registry.
- **The two legacy gates block without validation** and are not demoted. Scope
  decision outstanding.
- **`mutation-quality.md` keeps a writable self-ratcheting baseline**, which
  contradicts the no-writable-baseline decision every other gate follows.
- **The anti-fragmentation hole is open** — complexity gates push toward tiny
  single-caller helpers. Documented in `code-structure-quality.md`; no detector
  ships.

## Related

- `<AI_DEV_SHOP_ROOT>/harness-engineering/quality/coverage-integrity-policy.md` — coverage-scoped integrity rules
- `<AI_DEV_SHOP_ROOT>/skills/function-quality-assessment/references/finding-rubric.md` — dispositions and fixed severities
- `<AI_DEV_SHOP_ROOT>/framework/contracts/computational-controls.md` — the slots these gates run in
- `<AI_DEV_SHOP_ROOT>/framework/contracts/architecture-fitness.md` — per-rule `blocking`/`advisory` severity, the other axis
- `<AI_DEV_SHOP_ROOT>/harness-engineering/sensors/README.md` — the sensor catalog
