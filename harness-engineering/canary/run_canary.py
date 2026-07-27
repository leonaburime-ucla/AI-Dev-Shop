#!/usr/bin/env python3
"""Run the ablation canary for the dependency-cycle gate.

The canary answers one question: **does this detector actually detect?** A gate
that has never been shown to fire is indistinguishable from a gate that cannot,
and the failure is silent — an under-scoped graph command exits 0 and emits an
empty finding list that reads exactly like a clean repository.

Four controls, per the specification in
`harness-engineering/quality/gate-validation-status.md` § Promotion:

  1. INJECTION      plant the defect; the gate must fire, naming it
  2. NEGATIVE       run on clean code; the gate must stay quiet
  3. ABLATION       disable the detector; the result must change
  4. SENSITIVITY    the threshold must be load-bearing, not decorative

Controls 1 and 2 execute the conformance fixtures the sensor doc already
specifies (`dependency-structure.md` § Conformance Fixtures) rather than
inventing new ones — the point is to exercise the contract that exists.

Control 3 is the canary proper and the reason for the name. It re-runs a fixture
with a deliberately under-scoped entry point, which is the real-world
misconfiguration the sensor doc calls out. If the ablated run and the healthy run
produce the same output, the reported findings did not depend on the detector
having actually traversed the code, and a zero result proves nothing.

Usage:
    python3 harness-engineering/canary/run_canary.py            # run, print, write artifact
    python3 harness-engineering/canary/run_canary.py --check    # exit 1 if any control fails
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference_detector import detect  # noqa: E402


HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"
ARTIFACT = HERE / "results" / "dependency-cycle-canary.json"

GATE = "New dependency cycle in a `blocking`-severity scope"
SENSOR = "harness-engineering/sensors/dependency-structure.md"

DIRECTION_RULES = [
    {
        "name": "domain-does-not-depend-on-infra",
        "from_prefix": "domain",
        "to_prefix": "infra",
    }
]


def control_injection() -> list[dict]:
    """Fixtures that must produce a finding, from the sensor's fixture table."""
    results = []

    f1 = detect(FIXTURES / "f1_direct_cycle")
    two_cycles = [c for c in f1["cycles"] if len(c) == 2]
    results.append(
        {
            "control": "injection",
            "fixture": "f1_direct_cycle",
            "expectation": "cycle of length 2, both modules named",
            "observed": f1["cycles"],
            "passed": bool(two_cycles) and set(two_cycles[0]) == {"a", "b"},
        }
    )

    f2 = detect(FIXTURES / "f2_indirect_cycle")
    three_cycles = [c for c in f2["cycles"] if len(c) == 3]
    results.append(
        {
            "control": "injection",
            "fixture": "f2_indirect_cycle",
            "expectation": "3-module cycle reported though it closes through an untouched file",
            "observed": f2["cycles"],
            "passed": bool(three_cycles) and set(three_cycles[0]) == {"a", "b", "c"},
        }
    )

    f3 = detect(FIXTURES / "f3_boundary_violation", rules=DIRECTION_RULES)
    named = [
        v
        for v in f3["direction_violations"]
        if v["rule"] == "domain-does-not-depend-on-infra"
    ]
    results.append(
        {
            "control": "injection",
            "fixture": "f3_boundary_violation",
            "expectation": "reported against the declared rule by name",
            "observed": f3["direction_violations"],
            "passed": bool(named),
        }
    )
    return results


def control_negative() -> list[dict]:
    """Clean code must stay quiet, or the gate is noise."""
    f4 = detect(FIXTURES / "f4_acyclic_fanout", rules=DIRECTION_RULES)
    clean = not f4["cycles"] and not f4["direction_violations"]
    return [
        {
            "control": "negative",
            "fixture": "f4_acyclic_fanout",
            "expectation": "acyclic module importing five others is NOT reported",
            "observed": {
                "cycles": f4["cycles"],
                "direction_violations": f4["direction_violations"],
                "modules_graphed": len(f4["modules_graphed"]),
            },
            "passed": clean,
        }
    ]


def control_ablation() -> list[dict]:
    """The canary proper: cripple the detector and require the result to change.

    Narrowing the scope to `a.py` models an entry point that never reaches `b.py`.
    The detector then reports zero cycles on a fixture that certainly has one. If
    that is indistinguishable from the healthy run, no zero result from this gate
    can be trusted.
    """
    healthy = detect(FIXTURES / "f1_direct_cycle")
    ablated = detect(FIXTURES / "f1_direct_cycle", scope="a.py")

    changed = healthy["cycles"] != ablated["cycles"]
    return [
        {
            "control": "ablation",
            "fixture": "f1_direct_cycle",
            "expectation": "under-scoped detector produces a different result than a healthy one",
            "observed": {
                "healthy_cycles": healthy["cycles"],
                "healthy_modules": len(healthy["modules_graphed"]),
                "ablated_cycles": ablated["cycles"],
                "ablated_modules": len(ablated["modules_graphed"]),
            },
            "passed": changed,
            "note": (
                "The ablated run reports zero cycles on a fixture that has one. That is "
                "the silent failure this control exists to expose: a zero finding is only "
                "evidence when the detector is known to have been live."
            ),
        }
    ]


def control_sensitivity() -> list[dict]:
    """The threshold must decide something, or the number is decorative."""
    root = FIXTURES / "f2_indirect_cycle"
    at_limit = detect(root, max_cycle_length=3)  # 3-cycle tolerated
    below_limit = detect(root, max_cycle_length=2)  # 3-cycle is a finding

    return [
        {
            "control": "sensitivity",
            "fixture": "f2_indirect_cycle",
            "expectation": "the 3-cycle is a finding at max_cycle_length=2 and not at 3",
            "observed": {
                "max_cycle_length=3": at_limit["cycles"],
                "max_cycle_length=2": below_limit["cycles"],
            },
            "passed": not at_limit["cycles"] and bool(below_limit["cycles"]),
        }
    ]


def run() -> dict:
    results = (
        control_injection()
        + control_negative()
        + control_ablation()
        + control_sensitivity()
    )
    passed = all(r["passed"] for r in results)
    by_control = {}
    for r in results:
        bucket = by_control.setdefault(r["control"], {"passed": 0, "failed": 0})
        bucket["passed" if r["passed"] else "failed"] += 1

    return {
        "gate": GATE,
        "sensor": SENSOR,
        "detector": "harness-engineering/canary/reference_detector.py (pilot stand-in)",
        "verdict": "PASS" if passed else "FAIL",
        "summary": by_control,
        "controls": results,
        "caveats": [
            "The subject is the pilot reference detector, not a host's declared "
            "`dependency_graph` command. This run demonstrates the canary loop; it does "
            "not validate any host's detector.",
            "Fixture sources are Python because the pilot must run with nothing installed. "
            "The controls are language-neutral; the fixture language is incidental.",
            "A PASS here is evidence the gate can fire and can stay quiet. It is not "
            "evidence that the gate's disposition or scope is correct.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true", help="exit non-zero if any control fails"
    )
    args = parser.parse_args()

    report = run()
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(f"Ablation canary — {report['gate']}")
    print(f"  detector: {report['detector']}\n")
    for r in report["controls"]:
        mark = "PASS" if r["passed"] else "FAIL"
        print(f"  [{mark}] {r['control']:12s} {r['fixture']}")
        print(f"         expected: {r['expectation']}")
    print(f"\n  verdict: {report['verdict']}")
    print(f"  artifact: {ARTIFACT.relative_to(Path.cwd()) if ARTIFACT.is_relative_to(Path.cwd()) else ARTIFACT}")

    if args.check and report["verdict"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
