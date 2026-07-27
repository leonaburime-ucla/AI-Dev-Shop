#!/usr/bin/env python3
"""Run the ablation canary for the dependency-cycle gate.

The canary answers one question: **does this detector actually detect?** A gate
that has never been shown to fire cannot be told apart from a gate that cannot
fire, and the failure is silent — a detector whose entry point misses the changed
code exits 0 and emits an empty finding list that reads exactly like clean code.

Controls, per `harness-engineering/quality/gate-validation-status.md` § Promotion:

  1. INJECTION      plant the defect; the gate must fire, naming it
  2. NEGATIVE       clean code and toolkit idioms must stay quiet; rate recorded
  3. ABLATION       cripple the detector; the healthy run finds what the crippled
                    one misses, and the traversal shrinks
  4. SENSITIVITY    the threshold must be load-bearing, not decorative
  5. UNSEEN         a fixture generated at run time, nested deeper than any
                    committed one, must also be caught

Controls 1 and 2 execute the conformance fixtures the sensor doc already
specifies rather than inventing a parallel set.

Control 5 exists because of an adversarial review of the first version. The
original ablation control asserted only that output changed when the scope
argument changed, which is far weaker than "the detector read the code". Two
detectors defeated it: one that opened no files and answered from a hardcoded
table, and one that parsed properly but capped file discovery at two path
segments — literally "an entry point quietly scoped to the wrong tree", the
failure this canary is named for. A run-time-generated, deeply nested fixture
cannot be answered from a table, and a shallow walker cannot reach it.

Usage:
    python3 harness-engineering/canary/run_canary.py             # run, write artifact
    python3 harness-engineering/canary/run_canary.py --check     # verify, write nothing
    python3 harness-engineering/canary/run_canary.py --seed 7    # vary the unseen fixture
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference_detector import detect  # noqa: E402


HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"
ARTIFACT = HERE / "results" / "dependency-cycle-canary.json"

GATE = "New dependency cycle in a `blocking`-severity scope"
SENSOR = "harness-engineering/sensors/dependency-structure.md"

# A real promotion records the host's command and its pinned version here. The
# pilot's subject is this repository's stand-in, so its "version" is the commit
# that last changed it — recorded so the artifact has the shape a host must copy.
DETECTOR = {
    "command": "harness-engineering/canary/reference_detector.py",
    "version": "pilot stand-in; not a host `dependency_graph` command",
    "pinned": False,
}

DIRECTION_RULES = [
    {
        "name": "domain-does-not-depend-on-infra",
        "from_prefix": "domain",
        "to_prefix": "infra",
    }
]


def result(control, fixture, expectation, observed, passed, note=None):
    entry = {
        "control": control,
        "fixture": fixture,
        "expectation": expectation,
        "observed": observed,
        "passed": passed,
    }
    if note:
        entry["note"] = note
    return entry


def control_injection() -> list[dict]:
    """Fixtures that must produce a finding, from the sensor's fixture table."""
    out = []

    f1 = detect(FIXTURES / "f1_direct_cycle")
    two = [c for c in f1["cycles"] if len(c) == 2]
    out.append(
        result(
            "injection",
            "f1_direct_cycle",
            "cycle of length 2, both modules named",
            f1["cycles"],
            bool(two) and set(two[0]) == {"a", "b"},
        )
    )

    f2 = detect(FIXTURES / "f2_indirect_cycle")
    three = [c for c in f2["cycles"] if len(c) == 3]
    out.append(
        result(
            "injection",
            "f2_indirect_cycle",
            "3-module cycle reported, closing through a module the entry point does not import directly",
            f2["cycles"],
            bool(three) and set(three[0]) == {"a", "b", "c"},
        )
    )

    f3 = detect(FIXTURES / "f3_boundary_violation", rules=DIRECTION_RULES)
    named = [
        v for v in f3["direction_violations"]
        if v["rule"] == "domain-does-not-depend-on-infra"
    ]
    out.append(
        result(
            "injection",
            "f3_boundary_violation",
            "reported against the declared rule by name",
            f3["direction_violations"],
            bool(named),
        )
    )

    f6 = detect(FIXTURES / "f6_relative_imports")
    rel = [c for c in f6["cycles"] if len(c) == 2]
    out.append(
        result(
            "injection",
            "f6_relative_imports",
            "cycle written with relative imports is found — intra-package is where cycles live",
            f6["cycles"],
            bool(rel),
        )
    )
    return out


def control_negative() -> list[dict]:
    """Clean code and toolkit-mandated idioms must stay quiet.

    The false-positive rate is the measurement the spec asks for, so it is
    computed and recorded rather than collapsed into a boolean.
    """
    out = []
    quiet = 0
    fixtures = [
        ("f4_acyclic_fanout", "acyclic module importing five others is NOT reported"),
        (
            "f5_reexport_hub",
            "a package re-exporting its own submodules is NOT reported — a mandated idiom, "
            "and the shape naive detectors flag",
        ),
    ]

    for name, expectation in fixtures:
        found = detect(FIXTURES / name, rules=DIRECTION_RULES)
        clean = not found["cycles"] and not found["direction_violations"]
        quiet += 1 if clean else 0
        out.append(
            result(
                "negative",
                name,
                expectation,
                {
                    "cycles": found["cycles"],
                    "direction_violations": found["direction_violations"],
                    "modules_graphed": len(found["modules_graphed"]),
                },
                clean,
            )
        )

    rate = (len(fixtures) - quiet) / len(fixtures)
    out.append(
        result(
            "negative",
            "false-positive rate",
            "measured across the negative-control set; must be 0.0",
            {"negative_controls": len(fixtures), "fired_on": len(fixtures) - quiet, "rate": rate},
            rate == 0.0,
        )
    )
    return out


def control_ablation() -> list[dict]:
    """Cripple the detector and require the healthy run to see what it misses.

    Comparing the two outputs is not enough on its own — that only shows the
    output depends on the scope argument, which a detector that never reads a file
    can satisfy. The healthy run must positively find the planted cycle, the
    ablated run must miss it, and the traversal must visibly shrink.
    """
    root = FIXTURES / "f1_direct_cycle"
    healthy = detect(root)
    ablated = detect(root, scope="a.py")

    healthy_found = any(set(c) == {"a", "b"} for c in healthy["cycles"])
    ablated_missed = not ablated["cycles"]
    shrank = len(ablated["modules_graphed"]) < len(healthy["modules_graphed"])

    return [
        result(
            "ablation",
            "f1_direct_cycle",
            "healthy run finds the planted cycle, under-scoped run misses it, traversal shrinks",
            {
                "healthy_cycles": healthy["cycles"],
                "healthy_modules": healthy["modules_graphed"],
                "ablated_cycles": ablated["cycles"],
                "ablated_modules": ablated["modules_graphed"],
                "healthy_found": healthy_found,
                "ablated_missed": ablated_missed,
                "traversal_shrank": shrank,
            },
            healthy_found and ablated_missed and shrank,
            note=(
                "The ablated run reports zero cycles on a fixture that has one. That is the "
                "silent failure this control exists to expose: a zero finding is evidence only "
                "when the detector is known to have been live."
            ),
        )
    ]


def control_sensitivity() -> list[dict]:
    """The threshold must decide something, or the number is decorative."""
    root = FIXTURES / "f2_indirect_cycle"
    tolerated = detect(root, max_cycle_length=3)
    flagged = detect(root, max_cycle_length=2)
    return [
        result(
            "sensitivity",
            "f2_indirect_cycle",
            "the 3-cycle is a finding at max_cycle_length=2 and not at 3",
            {
                "max_cycle_length=3": tolerated["cycles"],
                "max_cycle_length=2": flagged["cycles"],
            },
            not tolerated["cycles"] and bool(flagged["cycles"]),
        )
    ]


def control_unseen(seed: int) -> list[dict]:
    """A fixture built at run time, nested deeper than any committed one.

    Defeats the two detectors that beat the first version of this canary: a
    hardcoded answer table has never seen these module names, and a walker that
    caps discovery at two path segments cannot reach a cycle planted at depth 3.
    """
    tmp = Path(tempfile.mkdtemp(prefix="canary-unseen-"))
    try:
        tag = f"g{seed:04d}"
        deep = tmp / "svc" / tag / "core"
        deep.mkdir(parents=True)
        for part in (tmp / "svc", tmp / "svc" / tag, deep):
            (part / "__init__.py").write_text("", encoding="utf-8")

        left, right = f"alpha_{tag}", f"beta_{tag}"
        prefix = f"svc.{tag}.core"
        (deep / f"{left}.py").write_text(
            f"from {prefix} import {right}\n", encoding="utf-8"
        )
        (deep / f"{right}.py").write_text(
            f"from {prefix} import {left}\n", encoding="utf-8"
        )

        found = detect(tmp)
        target = {f"{prefix}.{left}", f"{prefix}.{right}"}
        hit = any(set(c) == target for c in found["cycles"])

        return [
            result(
                "unseen",
                f"generated depth-3 package (seed {seed})",
                "a cycle in a package the detector has never seen, three directories deep, is found",
                {
                    "planted": sorted(target),
                    "cycles": found["cycles"],
                    "modules_graphed": found["modules_graphed"],
                },
                hit,
                note=(
                    "A detector answering from a lookup table cannot know these names, and one "
                    "that caps file discovery near the root cannot reach this depth. Vary --seed "
                    "for a promotion run."
                ),
            )
        ]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run(seed: int) -> dict:
    results = (
        control_injection()
        + control_negative()
        + control_ablation()
        + control_sensitivity()
        + control_unseen(seed)
    )
    by_control: dict[str, dict] = {}
    for r in results:
        bucket = by_control.setdefault(r["control"], {"passed": 0, "failed": 0})
        bucket["passed" if r["passed"] else "failed"] += 1

    return {
        "gate": GATE,
        "sensor": SENSOR,
        "detector": DETECTOR,
        "seed": seed,
        "verdict": "PASS" if all(r["passed"] for r in results) else "FAIL",
        "summary": by_control,
        "controls": results,
        "human_approval": None,
        "caveats": [
            "The subject is the pilot stand-in detector, not a host's declared "
            "`dependency_graph` command. This run demonstrates the canary loop; it validates "
            "no host's detector, and `human_approval` is null because nothing is being promoted.",
            "Fixture sources are Python so the pilot runs with nothing installed. The controls "
            "are language-neutral; the fixture language is incidental.",
            "A PASS means the gate can fire and can stay quiet. It is not evidence that the "
            "gate's threshold, disposition or scope is correct.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify without writing")
    parser.add_argument("--seed", type=int, default=1, help="vary the unseen fixture")
    args = parser.parse_args()

    report = run(args.seed)

    print(f"Ablation canary — {report['gate']}")
    print(f"  detector: {report['detector']['command']}\n")
    for r in report["controls"]:
        print(f"  [{'PASS' if r['passed'] else 'FAIL'}] {r['control']:12s} {r['fixture']}")
    print(f"\n  verdict: {report['verdict']}")

    if args.check:
        # Never rewrite the evidence while verifying it: a run that regenerates the
        # artifact can never catch it stale, which defeats committing the two together.
        if report["verdict"] != "PASS":
            return 1
        if ARTIFACT.exists():
            committed = json.loads(ARTIFACT.read_text(encoding="utf-8"))
            if committed.get("verdict") != "PASS":
                print(f"  FAIL: committed artifact records {committed.get('verdict')!r}")
                return 1
        return 0

    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"  artifact: {ARTIFACT}")
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
