# Ablation Canary — dependency-cycle pilot

The specification lives in
`<AI_DEV_SHOP_ROOT>/harness-engineering/quality/gate-validation-status.md`
§ Promotion. This directory is the pilot that runs it end to end for one gate, so
the criterion is something executable rather than something described.

```bash
python3 harness-engineering/canary/run_canary.py           # run and write the artifact
python3 harness-engineering/canary/run_canary.py --check   # non-zero if any control fails
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
`unvalidated`. Promotion needs these same four controls run against a real
declared detector, pinned by version, on a real project.

## It is mutation-tested

A canary that only ever passes is worth nothing. Five deliberately broken
detectors were each caught by the control that should catch them:

| Broken detector | Control that failed |
|---|---|
| finds no cycles at all | injection |
| flags fan-out as a cycle | negative |
| ignores its scope argument | **ablation** |
| ignores the cycle-length threshold | sensitivity |
| loses the direction rules | injection (`f3`) |

The third is the one that matters. A detector that ignores its scope produces
identical output however it is pointed, so its zero findings carry no
information — and only the ablation control notices.

## Fixture language

The fixtures are Python because the pilot must run without installing anything.
The controls are language-neutral; the fixture language is incidental and is not
a claim about which stacks this gate supports.
