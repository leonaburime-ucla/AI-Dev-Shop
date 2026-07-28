# Ablation Canary — dependency-cycle pilot

> **Not run by `run-all.sh`, deliberately.** Its subject is the stand-in detector
> below, not a host's declared `dependency_graph` command, so a PASS on every
> commit implied a validation that had not happened. Run it by hand when working
> on the canary itself. Read § What it does NOT catch before trusting a PASS.

The specification lives in
`<AI_DEV_SHOP_ROOT>/harness-engineering/quality/gate-validation-status.md`
§ Promotion. This directory is the pilot that runs it end to end for one gate, so
the criterion is something executable rather than something described.

```bash
python3 harness-engineering/canary/run_canary.py           # run and write the artifact
python3 harness-engineering/canary/run_canary.py --check   # non-zero if any control fails
python3 harness-engineering/canary/run_canary.py --seed 99 # vary the generated fixture
```

## Why one gate and not twelve

A specification that has never been run is the placeholder this program spent a
release avoiding — it would let a gate be promoted against a standard nobody had
tested. Piloting on one gate first turns the criterion into something with a
known cost and a known failure mode before it is applied to eleven more.

Dependency cycles were chosen because a cycle either exists or it does not: no
threshold-calibration argument, no ambiguity about what the defect is, and the
smallest possible fixture. Cognitive complexity would have been the worst first
choice for exactly the reasons that make this one easy.

## What it runs

Controls 1 and 2 execute the conformance fixtures that
`harness-engineering/sensors/dependency-structure.md` § Conformance Fixtures
already specifies, rather than a parallel set invented here. Those fixtures had
been specified and never executed; this runs them.

| Fixture | Control | Expectation |
|---|---|---|
| `f1_direct_cycle` | injection | cycle of length 2, both modules named |
| `f2_indirect_cycle` | injection | 3-module cycle reported though it closes through an untouched file |
| `f3_boundary_violation` | injection | reported against the declared rule by name |
| `f4_acyclic_fanout` | negative | acyclic module importing five others is **not** reported |
| `f1_direct_cycle` | ablation | an under-scoped detector must produce a different result than a healthy one |
| `f2_indirect_cycle` | sensitivity | the 3-cycle is a finding on the strict side of the threshold and not on the permissive side |

## The detector is a stand-in

`reference_detector.py` is a real detector — it parses source, builds an import
graph, and finds cycles — but it is **not** a host's declared `dependency_graph`
command. It exists so the canary can run with nothing installed, because a
validation loop that cannot run on the machine in front of you is the problem
this program is trying to solve.

Consequence: **this pilot promotes nothing.** The dependency-cycle gate stays
`unvalidated`. Promotion needs these same five controls run against a real
declared detector, pinned by version, on a real project.

## What it catches

Broken detectors that fail, each on the control that should catch it:

| Broken detector | Control that failed |
|---|---|
| finds no cycles at all | injection |
| flags fan-out as a cycle | negative |
| caps file discovery two directories deep | **unseen** |
| ignores the cycle-length threshold | sensitivity |
| loses the direction rules | injection (`f3`) |

## What it does NOT catch — measured, not assumed

An adversarial review wrote six broken detectors that pass **every** control.
This is recorded here because a canary trusted beyond its reach is worse than no
canary at all.

| Passes anyway | Why the controls miss it |
|---|---|
| Opens no source file; guesses "deepest package with two modules → 2-cycle" | every fixture, including the generated one, has that shape |
| Resolves imports by basename, so any two `utils.py` look linked | no fixture has a repeated leaf name |
| Direction rules prefix-match with no path boundary | no fixture has a `domain_utils`-style near-miss |
| Misses cycles longer than 3 | the longest planted cycle is 3 |
| Reads only the first two lines of each file | every fixture puts its import on line 1 |
| Caps discovery at four path segments | the generated fixture is fixed at depth 3 |

Two structural weaknesses cause most of that. **The generated fixture varies its
names, not its shape** — so a detector can pattern-match the shape without
reading anything. And `run-all.sh` invokes `--check` with no `--seed`, so the
default of `1` makes even the names identical on every run; a three-name lookup
table passes.

**Read a PASS as "this detector is not broken in one of the five ways the
controls model."** It is not evidence that the detector reads your code.

## It is mutation-tested

The detector under test is mutation-tested separately: `find_cycles` and
`strongly_connected` were differential-tested against an independent Kosaraju
implementation and a brute-force cycle enumerator over 17 hand cases and 4,000
random graphs, with no mismatches.

## Fixture language

The fixtures are Python because the pilot must run without installing anything.
The controls are language-neutral; the fixture language is incidental and is not
a claim about which stacks this gate supports.
