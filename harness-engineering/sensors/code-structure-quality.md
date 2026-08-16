# Sensor: Code Structure Quality

Measures per-function structural complexity and size on changed code and converts
breaches into findings with fixed severities. Backs the gates declared in
`<AI_DEV_SHOP_ROOT>/skills/testable-design-patterns/SKILL.md`.

Four metrics, two roles: **cognitive complexity** and **nesting depth** are gated;
**cyclomatic complexity** and **function size** are mandatory to report and never
gated. Both non-gated metrics exist because they change how a reviewer reads a
gated result, not because they are verdicts.

**The gated metric is cognitive complexity, not cyclomatic.** See "Why not
cyclomatic" below — this is not a preference, it is a conflict with a pattern
this toolkit mandates.

## Sensor Definition

- **Class**: `computational`
- **Timing**: PR (every reviewed change) + scheduled (distribution trends)
- **PR owner**: **Code Inspection** — it already executes `lint`, `typecheck`, and
  `static_analysis` per the execution table in
  `<AI_DEV_SHOP_ROOT>/framework/contracts/computational-controls.md`, and
  `code_metrics` is static analysis. No new role is introduced.
- **Scheduled owner**: Observer (trends only, never changes a PR outcome)
- **Artifact**: `<ADS_MEMORY_ROOT>/.local-artifacts/sensors/code-structure-<feature-id>-<timestamp>.json`

## Custody — who may produce the number

**The measured party never authors the measurement.**

| Actor | May do | May not do |
|---|---|---|
| Programmer | run the command locally as an **advisory preview**; fix what it reports | restate metric values as free text in a handoff; treat preview output as evidence |
| Code Inspection | run the command itself; that run is **authoritative** | accept a Programmer-reported number in place of its own run |
| Observer | read accepted artifacts for trends | change a PR outcome retroactively |

Code Inspection runs `code_metrics` on **every** reviewed change. It is not sampled.

A sampled or artifact-based scheme was considered and rejected: any audit trigger
computed from bytes the measured agent authored is predictable by that agent, and
a content hash proves an artifact matches the source files, not that the numbers
came from the tool. For a check that costs seconds, unconditional recomputation
by the consumer is both cheaper and deterministic. A handoff asserting metric
values with no Code Inspection run behind it is a Required workflow finding.

**Honest limit, stated rather than obscured:** this closes fabrication by the
*measured* agent. It does not close fabrication by the *reviewing* agent. No
repository-only mechanism can — every agent shares the workspace and there is no
key custody. Closing that requires a trust boundary outside the agent-controlled
workspace (a required CI check with retained logs, or host-issued attestation)
and is out of scope for this sensor.

## Tools

The toolkit installs nothing. The host declares a command in the `code_metrics`
slot; agents invoke it via shell and parse stdout.

Because cyclomatic is mandatory to report and cognitive is the gate, most hosts
need **two commands or one tool that emits both**. Declare a `command` and an
optional `secondary_command`; the sensor merges their per-function output on
`file path + symbol name`.

**ESLint does not emit a symbol name**, so that merge key cannot be read directly
from the primary JS/TS command — its JSON carries file, line, column, rule id and
message, and `max-depth` reports at the offending nested block rather than at the
enclosing function. Mapping a diagnostic to its function requires an adapter over
an AST or over `lizard`'s per-function line spans. That adapter is host work and
is unspecified here; a host that skips it cannot populate the artifact's
per-function records, and anonymous and nested functions are where it will break
first.

### Cross-language layer — satisfies the mandatory CC requirement

| Tool | Coverage | Granularity | Emits |
|---|---|---|---|
| **`lizard`** (recommended default) | ~20 languages incl. C/C++, Java, C#, JS/TS, Python, Go, Rust, Ruby, PHP, Swift, Kotlin, Scala, Objective-C, Lua | **per-function** | cyclomatic (CCN), NLOC, parameter count, token count. **No cognitive complexity.** |
| **SonarQube / SonarCloud** | 30+ languages | per-function | **both** cyclomatic and cognitive, one consistent algorithm. Requires a server, scanner, and token. |
| **`scc`** | 200+ languages | **file-level only** | a branch-keyword approximation, **not true McCabe**. Usable for scheduled trends; **not** valid for the per-function layer. |

For the mandatory CC layer, prefer a cross-language per-function tool that runs
locally and needs no server — that is the cheapest thing to declare, and nothing
gates on CC. Such tools usually parse heuristically rather than building full
ASTs, so treat their values as internally consistent rather than authoritative.
Whatever is declared, record it and its version with the result.

### Per-language layer — the host declares, the fixture decides

**This section deliberately names no tools, flags, thresholds or defaults.**

An earlier version carried a per-stack table for JS/TS, Python, Go, Rust and
Java. Five separate defects came out of it and every one was found by reading a
tool's upstream source, never by anything in this repository:

<!-- historical:start -->
| Claim that was wrong | Reality |
|---|---|
| `flake8-max-nesting` is the Python nesting adapter | the package does not exist on PyPI (404) |
| clippy's `excessive-nesting-threshold` defaults to 5 | it defaults to **0** — the lint is off until configured |
| pylint `--max-nested-blocks` measures max block depth | it counts `if`/`for`/`while`/`try` only and is **blind to `with`** |
| `revive -enable-rule max-control-nesting` | `revive` has no `-enable-rule` flag; rules come from its config file |
| the JS/TS command supplies the artifact's merge key | ESLint emits no symbol name at all |
<!-- historical:end -->

The pattern is not five mistakes. It is one: **this repository cannot execute
any of these tools, so every claim it makes about them is unverifiable here and
decays silently.** Naming a tool creates an obligation to track its flags,
defaults and comparison operators across versions — an obligation nothing here
can discharge.

So the contract is a **capability**, not a tool:

> Declare a command that emits, per changed function, a **numeric value** for the
> metric, together with the **threshold it was configured at** and that
> threshold's **comparison operator**. Prove it with the conformance fixtures
> below. If it cannot, that metric's gate is `inactive` — reported as absent,
> never as clean.

What a host must establish at declaration time, for each metric it wants gated:

| Requirement | Why |
|---|---|
| Emits a value, not just a violation | `REVIEW` vs `BREACH` cannot be separated without one, and the delta rule needs a base value |
| Reports below the review band's lower edge | a tool configured at the gate says nothing about the review band |
| Records its threshold **and operator** | what silence proves depends on both; `>= N` and `> N` differ by one |
| Attributes to an enclosing function | file-and-line alone cannot populate a per-function record |
| Passes the conformance fixtures | the only evidence that survives a version bump |

A tool failing any row makes that metric `inactive` on that stack. That is a
supported, honest outcome — unlike a named tool that silently stops matching.

`lizard` remains named in the cross-language layer above for one reason: it
supplies `cyclomatic` and `size_nloc`, both of which are **reported and never
gated**, so a drift in its behaviour cannot produce a wrong gate outcome.

**On SonarQube/SonarCloud:** it is the only tool that produces cognitive
complexity consistently across languages, and it satisfies both layers with one
declaration. For a JS/TS-only host, prefer `eslint-plugin-sonarjs` — same
algorithm, installs as a devDependency, no server. For a polyglot host already
running SonarQube, declaring it is the simplest correct answer. Either way the
conformance fixtures below still apply.

**Verify tool claims at declaration time, not from this table.** Tool language
support and output formats change. The conformance fixtures are the mechanism
that settles what a given tool actually does on this host — run them rather than
trusting the coverage claims above.

## Why Not Cyclomatic Complexity

`<AI_DEV_SHOP_ROOT>/skills/testable-design-patterns/SKILL.md` **mandates**
exhaustive `switch` over discriminated unions with a `never` default. A
14-variant exhaustive switch scores cyclomatic ≈ 15 and cognitive ≈ 1 — Sonar
charges a `switch` once precisely so flat dispatch is not punished.

Gating on cyclomatic complexity would therefore hard-fail a pattern this toolkit
requires, and every compliant escape is worse than the breach: splitting the
switch destroys single-point exhaustiveness, and converting it to a handler map
turns readable control flow into indirection. Cyclomatic complexity is never on
its own a Required finding.

**But CC is mandatory to report.** Every changed function in the artifact must
carry a `cyclomatic` value. It is never gated, and it never blocks — it is
context a reviewer uses to interpret a cognitive-complexity result, and the input
to any later research sensor.

The reason CC is mandatory while cognitive is the gate is a tooling asymmetry
worth stating plainly:

- **Cyclomatic complexity generalizes.** It is a property of the control-flow
  graph — count decision points, add one — so genuinely cross-language tools
  produce it consistently.
- **Cognitive complexity does not.** It is a Sonar-defined algorithm. Outside
  Sonar itself, each language has a separate reimplementation that drifts in edge
  cases.

So the metric this sensor *gates* on is the one with the more fragile tooling
story, and the metric it merely *reports* is the one available everywhere. That
is a deliberate trade — CC false-fires on the exhaustive-switch idiom this
toolkit mandates, and cognitive does not — but it means a host whose stack has no
cognitive analyzer still produces useful CC context while the gate itself
degrades to advisory.

**A declared command that cannot emit per-function cyclomatic values is a
declaration defect**, reported as a Required workflow finding against the
contract (not against the code under review). Do not silently omit the field, and
never report a CC value the tool did not actually produce.

## Function Size — reported, never gated

Every changed function carries a `size_nloc` value (non-comment lines of code).
`lizard` already emits it alongside cyclomatic complexity, so the collection cost
is zero — it is the same parse.

**Size is never a gate, and never on its own a Required finding.** It was cut
from an earlier draft of this sensor for a real reason: it false-fires on
declarative code, where a 200-line config object, route table, or validation
schema is one long function with no branching and nothing wrong with it. Gating
on it would reproduce exactly the failure mode the cyclomatic gate had — hard-fail
a shape the codebase legitimately uses.

Reporting it is safe and useful for three things a reviewer cannot get elsewhere:

- **Disambiguating a cognitive-complexity result.** Cognitive 14 in 20 lines is
  dense logic; cognitive 14 in 300 lines is a function doing too many things. The
  gate value is the same; the correct response is not.
- **Detecting fragmentation.** The known anti-fragmentation hole below is partly
  visible in size data — a cluster of new sub-10-line single-caller helpers is
  the signature. Size does not resolve the hole, but without it a reviewer cannot
  even see the pattern.
- **Scheduled distribution trends.** Observer tracks the size distribution over
  time; a rising tail is a signal worth a human look, not a block.

A `size_nloc` value that is large and unaccompanied by any other finding is
**not** a finding. Do not synthesize one from it.

## Artifact Record

One record per changed function. `cyclomatic` and `size_nloc` are mandatory; a
record missing either is a declaration defect, not a clean result.

```json
{
  "run": {
    "base_ref": "<merge-base sha>",
    "head_ref": "<head sha>",
    "commands": ["<resolved command>", "<resolved secondary command or null>"],
    "tools": [{"name": "lizard", "version": "..."}],
    "conformance": "PASS | FAIL | NOT_RUN",
    "executed_by": "code-inspection",
    "scope": ["<changed files>"],
    "exclusions": [{"path": "...", "rule": "...", "approval": "..."}]
  },
  "functions": [
    {
      "id": "src/policy.ts#evaluatePolicy",
      "status": "new | touched",
      "cyclomatic": 12,
      "cyclomatic_base": 12,
      "cognitive": 12,
      "cognitive_base": 12,
      "nesting": 3,
      "nesting_base": 3,
      "size_nloc": 34,
      "size_nloc_base": 31,
      "gate_cognitive": "PASS | REVIEW | BREACH | INCONCLUSIVE | INACTIVE",
      "gate_nesting": "PASS | REVIEW | BREACH | INCONCLUSIVE | INACTIVE",
      "value_source_cognitive": "measured | below_reporting_threshold | not_applicable",
      "value_source_nesting": "measured | below_reporting_threshold | not_applicable",
      "reporting_threshold_cognitive": 10,
      "reporting_threshold_nesting": 3,
      "justification": null
    }
  ]
}
```

**There is one gate field per gated metric, deliberately.** An earlier draft used
a single scalar `gate`, which could not represent the common case: on a Java host,
`cognitive` is measured and clean while `nesting` has no detector at all.
One field forces those into a single verdict, and the only available answer
collapses to either a false `PASS` or a permanent `INCONCLUSIVE` — the exact
outcomes this sensor forbids. A function may be `PASS` on cognitive and `INACTIVE`
on nesting simultaneously; that is two facts and it takes two fields.

`*_base` is `null` for new functions. Per metric:

- **`INACTIVE`** — no analyzer declared for that metric on this stack. Permanent
  host property, never `PASS`, never re-raised per PR.
- **`INCONCLUSIVE`** — an analyzer *was* declared and produced no value, failed,
  or did not pass its fixture. A defect to fix.
- **`value_source: below_reporting_threshold`** — the tool ran correctly and this
  function is under the configured reporting threshold, so no value exists. Gates
  `PASS` (provably under the review band) but the numeric field stays `null`; do
  not report an unmeasured value as measured.

`size_nloc` and `cyclomatic` never influence either gate field in any direction.
`conformance: FAIL` or `NOT_RUN` caps **both** gate fields at `REVIEW`; a tool
that has not passed the fixtures cannot block.

## Conformance Fixtures (required before a tool may block)

An analyzer may only produce blocking findings after passing these fixtures with
**exact expected outputs** recorded. A tool that fails any fixture is
**advisory-only** and cannot be promoted via an exception list.

| Fixture | Expectation |
|---|---|
| 14-variant exhaustive `switch` over a discriminated union with `never` default | cognitive well under the gate; **must not** breach |
| Stack of 5 top-level guard clauses with early returns | cognitive well under the gate; must not breach |
| Genuinely 5-level nested conditional | nesting breach reported |
| 5-level nest of **3 `with` + 2 `if`** (≤3 counted blocks) | nesting breach reported — **pylint fails this**, making the `with` blindness mechanically visible instead of a silent wrong-PASS. The counts matter: 4 `if` + 1 `with` gives pylint 4 counted blocks, which trips `--max-nested-blocks=3` and lets it pass the fixture while still blind |
| Deeply nested conditional with compound boolean conditions | cognitive breach reported |

Re-run fixtures on any analyzer, algorithm, or adapter version change, and
recompute base and head with the same version. Never compare an old-tool number
to a new-tool number.

## Gate Logic

Comparison base is the VCS merge base selected by Coordinator. **There is no
stored baseline file** — a writable baseline is enforcement authority an agent
can poison; comparing to the merge base removes the attack surface instead of
policing it.

```text
BREACH = head_value > gate
         AND (function_is_new OR head_value > base_value)
```

| Metric | Review band | Gate |
|---|---|---|
| Cognitive complexity | 11-15 | 16+ |
| Max nesting depth | 4 | 5+ |

Worked examples:

- base 20 → head 20: **no block**, record legacy-above-band advisory
- base 20 → head 18: **no block**, and **no positive credit**
- base 20 → head 21: **REQUIRED**
- new function at 16: **REQUIRED**
- base 14 → head 16: **REQUIRED**

Function identity across base and head is matched by `file path + enclosing
scope + symbol name`. Body content is **not** used for matching — a refactor
changes the body by definition, and fingerprint matching would misclassify the
exact improvement this gate is meant to encourage. Genuine renames use Git rename
information. An unresolvable match is `INCONCLUSIVE`, never "new function."

If the repository has no reachable merge base (shallow clone, common in
brownfield CI), the result is `INCONCLUSIVE` and advisory — never "treat all
functions as new."

## Severity — fixed, not negotiable

| Finding | Severity | Disposition |
|---|---|---|
| Cognitive complexity > 15, new or worsened | `High` | `REQUIRED` unless a justification is upheld |
| Nesting depth > 4, new or worsened | `High` | `REQUIRED` unless a justification is upheld |
| Review-band value (cognitive 11-15, nesting 4) | — | review prompt only, never blocks |
| Legacy above band, unworsened | — | advisory note |
| Large `size_nloc`, no gated breach | — | **not a finding**; context for reading other results |
| High `cyclomatic`, no gated breach | — | **not a finding**; context for reading other results |
| `cognitive` or `nesting` is `null`, no analyzer declared for the stack | — | `inactive` for that metric, never `PASS` |
| Analyzer declared but produced no value, or its fixture failed | — | `INCONCLUSIVE` for that metric, never `PASS` |

**Dispositions in this table apply at `validated` status.** These gates' current
status is in
`<AI_DEV_SHOP_ROOT>/harness-engineering/quality/gate-validation-status.md`; while
they are `unvalidated`, every `REQUIRED` above is capped at `RECOMMENDED`.
Canonical integrity findings (`INT-1`…`INT-9`) are never capped — including `INT-2`,
raising the cognitive or nesting band embedded in a declared `code_metrics`
command to clear a finding.

A reviewing agent **may not downgrade** a mechanically-sourced severity. It may
uphold a justification to clear the finding, per the Justification Hatch in
`testable-design-patterns`, where exhaustive union dispatch is the canonical
accepted case. The justification is written by the author and adjudicated by the
non-authoring reviewer; it is never self-approved. Without this rule the findings
regime has a one-word bypass.

**A clean metric earns no credit.** It establishes only that this detector found
no breach. It removes a ceiling; it never adds quality.

## Brownfield Adoption

- No whole-repository scan is required or wanted.
- Untouched violations are irrelevant and never block.
- Touched functions are measured at base and head; existing above-band functions
  block only on worsening.
- New functions face the absolute gate immediately — new code has no legacy excuse.
- Improving a legacy function without clearing the band is allowed and expected.
- Undeclared slot → sensor inactive, gates degrade to advisory review prompts.
  The review report must say so rather than implying enforcement.
- Generated, vendored, declarative-UI, template, migration, and fixture paths may
  be declared scope classes; exclusions remain visible in the artifact. Adding or
  broadening an exclusion is `INT-2` in
  `<AI_DEV_SHOP_ROOT>/harness-engineering/quality/gate-validation-status.md` — a
  finding when it lands in a change where it affects an observed result, or at
  any time without recorded human approval. (The coverage-integrity policy is
  coverage-scoped and does not govern metric scan exclusions; cite the ID.)

## Action-on-Fail

| Finding | Severity | Action |
|---|---|---|
| Gate breach, new or worsened, no upheld justification | Required | Code Inspection reports at fixed severity; **blocks only at `validated` gate status** (see the registry); otherwise routes to Programmer or Refactor as `RECOMMENDED` |
| Threshold in the declared command raised to clear a breach | Required | `INT-2`; blocks regardless of gate status |
| Gate breach with upheld justification | — | Recorded as adjudicated; no block |
| Review-band value on changed code | Advisory | Review prompt in the CR report |
| Slot declared but command fails or output unparseable | Required (workflow) | `INCONCLUSIVE`; fix the declaration before relying on the gate |
| Slot undeclared | Advisory | Note absence in the CR report; gates are not enforced |

## Known Limitations

- **Not validated.** The cognitive 11-15/16+ and nesting 4/5+ bands are inherited
  provisional review bands, not ADS-calibrated thresholds. Treat breaches as
  review triggers pending eval evidence. Their validation state is recorded in
  `<AI_DEV_SHOP_ROOT>/harness-engineering/quality/gate-validation-status.md`.
- **No anti-fragmentation detector ships with this sensor.** Complexity gates
  push agents toward splitting functions into many small single-caller helpers,
  which lowers every per-function metric while raising indirection. Candidate
  detectors were designed and rejected as uncalibrated. Until one is validated,
  fragmentation is a **human/reviewer judgment call**, and reviewers should treat
  a sudden rise in tiny single-caller helpers as suspicious rather than as
  improvement. The `size_nloc` field makes the pattern *visible* — a batch of new
  sub-10-line functions in one changed file is its signature — but visibility is
  not detection, and nothing here converts that shape into a finding.
- **Cognitive-complexity tooling is not universal, and the gate depends on it.**
  Cognitive complexity is a Sonar-defined algorithm with per-language
  reimplementations that drift; cyclomatic is a control-flow-graph property that
  generalizes cleanly. So the gated metric has the weaker tooling story and the
  reported one has the stronger. Hosts without a cognitive analyzer fall back to
  advisory gating while still reporting cyclomatic. **Do not silently substitute
  cyclomatic as a blocking gate** — that reintroduces the exhaustive-switch
  conflict this sensor exists to avoid.
- **This sensor is function-local only.** It does **not** detect dependency
  cycles, layer violations, fan-out concentration, or public-API growth — those
  are module-graph properties. Cycles and boundary violations are covered by
  `dependency-structure.md` via the `dependency_graph` slot; **fan-out
  concentration and public-API growth remain uncovered** by any sensor in this
  toolkit. Do not describe this sensor as providing architectural analysis.
  A **diagnostic** for coupling shape — afferent/efferent coupling, instability,
  abstractness, distance from the main sequence — exists at
  `<AI_DEV_SHOP_ROOT>/skills/codebase-analysis/references/component-coupling-metrics.md`.
  It is part of a skill, not a sensor: it produces no findings, no disposition is
  derived from it, and it does not make fan-out concentration a covered metric.

## Related

- `<AI_DEV_SHOP_ROOT>/skills/testable-design-patterns/SKILL.md` — the gates and the Justification Hatch
- `<AI_DEV_SHOP_ROOT>/skills/function-quality-assessment/references/finding-rubric.md` — dispositions and fixed severities
- `<AI_DEV_SHOP_ROOT>/framework/contracts/computational-controls.md` — the `code_metrics` slot
- `mutation-quality.md` — the custody precedent this sensor deliberately diverges from (mutation is protected because it is expensive; this check is cheap, so it is recomputed instead)
