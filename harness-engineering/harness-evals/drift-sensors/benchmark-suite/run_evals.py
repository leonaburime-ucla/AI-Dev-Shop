#!/usr/bin/env python3
"""Run drift sensor evals and grade responses against expected behaviors."""
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

SUITE_DIR = Path(__file__).resolve().parent
ROOT = SUITE_DIR.parents[3]

CLI_DISPATCH: dict[str, list[str]] = {
    "gemini": ["gemini", "-p"],
    "codex": ["codex", "exec", "-s", "read-only"],
    "claude": ["claude", "-p", "--output-format", "text"],
}

GRADING_CRITERIA: dict[str, dict[str, list[str]]] = {
    "SEED-DS-01": {
        "pass_signals": ["blocker", "escalat", "immediately", "security", "critical", "cve"],
        "fail_signals": ["advisory", "batch", "maintenance report only", "wait for next"],
    },
    "SEED-DS-02": {
        "pass_signals": ["advisory", "batch", "maintenance", "no escalat", "routine", "minor"],
        "fail_signals": ["blocker", "escalat", "security agent", "block pipeline", "critical"],
    },
    "SEED-DS-03": {
        "pass_signals": ["escalat", "refactor", "threshold", "tech-debt", "35%", "above baseline"],
        "fail_signals": ["blocker", "advisory only", "ignore", "no action"],
    },
    "SEED-DS-04": {
        "pass_signals": ["advisory", "note", "handoff", "small", "2%", "no escalat"],
        "fail_signals": ["escalat", "blocker", "block", "tdd agent", "must add tests"],
    },
    "SEED-DS-05": {
        "pass_signals": ["escalat", "critical-path", "auth", "login", "8%", "add test", "flag"],
        "fail_signals": ["advisory only", "no action", "acceptable", "within threshold"],
    },
    "SEED-DS-06": {
        "pass_signals": ["advisory", "warn", "programmer", "within", "threshold", "handoff"],
        "fail_signals": ["classify as escalation", "blocker", "route to refactor", "threshold breach"],
    },
}

NEGATION_PREFIXES = (
    "not ", "no ", "don't ", "do not ", "cannot ", "won't ", "will not ",
    "must not ", "should not ", "doesn't ", "does not ", "never ",
    "without ", "avoid ", "instead of ",
)


def signal_is_negated(signal: str, text: str) -> bool:
    idx = 0
    while True:
        pos = text.find(signal, idx)
        if pos == -1:
            return True
        context_start = max(0, pos - 40)
        preceding = text[context_start:pos].lower()
        if not any(preceding.endswith(neg) or neg in preceding[-20:] for neg in NEGATION_PREFIXES):
            return False
        idx = pos + 1
    return True


def build_eval_prompt(eval_dir: Path) -> str:
    brief = (eval_dir / "project-brief.md").read_text(encoding="utf-8")
    sensors_readme = (ROOT / "harness-engineering" / "sensors" / "README.md").read_text(encoding="utf-8")

    return f"""You are the Observer agent in the AI Dev Shop framework. You read drift sensor artifacts and classify/route findings.

## Sensor Catalog (your reference):
```
{sensors_readme}
```

## Current Sensor Artifact to Process:
{brief}

## Instructions:
Based on the sensor definitions and routing protocol, describe exactly what you do:
1. What severity you assign (blocker/escalation/advisory)
2. What action you take (escalate immediately, route to agent, batch into report, note in handoff)
3. Which agent you route to (if any)
4. Why (cite the sensor definition)

Respond in 150 words or less. Be direct."""


@dataclass
class EvalResult:
    seed_id: str
    eval_name: str
    passed: bool
    evidence_excerpt: str
    matched_signals: list[str]
    failed_signals: list[str]


def dispatch_eval(eval_dir: Path, model: str) -> Optional[str]:
    prompt = build_eval_prompt(eval_dir)
    cmd_prefix = CLI_DISPATCH.get(model)
    if cmd_prefix is None:
        return None
    cmd = cmd_prefix + [prompt]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120,
            input="" if model == "codex" else None,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def grade_response(seed_id: str, response: str) -> EvalResult:
    criteria = GRADING_CRITERIA[seed_id]
    response_lower = response.lower()

    matched_pass = [s for s in criteria["pass_signals"] if s.lower() in response_lower]
    matched_fail = [
        s for s in criteria["fail_signals"]
        if s.lower() in response_lower and not signal_is_negated(s.lower(), response_lower)
    ]

    pass_score = len(matched_pass) / max(len(criteria["pass_signals"]), 1)
    fail_score = len(matched_fail) / max(len(criteria["fail_signals"]), 1)
    passed = pass_score >= 0.3 and fail_score < 0.5

    excerpt = response[:200].replace("\n", " ").replace("\t", " ")
    eval_num = int(seed_id.split("-")[-1])
    eval_names = {
        1: "eval-1-critical-vuln-escalation",
        2: "eval-2-routine-outdated-advisory",
        3: "eval-3-dead-code-threshold-breach",
        4: "eval-4-small-coverage-drop-advisory",
        5: "eval-5-large-coverage-drop-escalation",
        6: "eval-6-new-dead-code-pr-advisory",
    }

    return EvalResult(
        seed_id=seed_id,
        eval_name=eval_names.get(eval_num, f"eval-{eval_num}"),
        passed=passed,
        evidence_excerpt=excerpt,
        matched_signals=matched_pass,
        failed_signals=matched_fail,
    )


def run_suite(model: str, deadline: float) -> list[EvalResult]:
    results: list[EvalResult] = []
    eval_dirs = sorted(SUITE_DIR.glob("eval-*/"))

    print(f"  [{model}] Running {len(eval_dirs)} evals...")

    for eval_dir in eval_dirs:
        if time.time() > deadline:
            print(f"    TIMEOUT — run budget exceeded, skipping remaining evals")
            break

        eval_num = eval_dir.name.split("-")[1]
        seed_id = f"SEED-DS-{eval_num.zfill(2)}"

        if seed_id not in GRADING_CRITERIA:
            continue
        if not (eval_dir / "project-brief.md").exists():
            continue

        print(f"    {seed_id}...", end=" ", flush=True)
        response = dispatch_eval(eval_dir, model=model)

        if response is None:
            print("FAIL (no response)")
            results.append(EvalResult(
                seed_id=seed_id, eval_name=f"eval-{eval_num}",
                passed=False, evidence_excerpt="No response",
                matched_signals=[], failed_signals=[],
            ))
            continue

        result = grade_response(seed_id, response)
        status = "PASS" if result.passed else "FAIL"
        print(f"{status} (pass={len(result.matched_signals)}, fail={len(result.failed_signals)})")
        results.append(result)
        time.sleep(1)

    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", default="gemini,codex")
    parser.add_argument("--timeout", type=int, default=600, help="Total run budget in seconds (default: 600 = 10 min)")
    args = parser.parse_args()

    models = [m.strip() for m in args.models.split(",")]
    all_results: dict[str, list[EvalResult]] = {}
    deadline = time.time() + args.timeout

    print(f"Drift Sensor Eval Suite — models: {', '.join(models)} (timeout: {args.timeout}s)")
    print()

    for model in models:
        if time.time() > deadline:
            print(f"  [{model}] SKIPPED — total run budget exceeded")
            continue
        all_results[model] = run_suite(model, deadline)
        passed = sum(1 for r in all_results[model] if r.passed)
        total = len(all_results[model])
        print(f"  [{model}] Results: {passed}/{total} passed")
        print()

    output_path = SUITE_DIR / "run-results.tsv"
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["model", "seed_id", "eval_name", "result", "pass_signals_matched", "fail_signals_matched", "evidence_excerpt"])
        for model, results in all_results.items():
            for r in results:
                writer.writerow([
                    model, r.seed_id, r.eval_name,
                    "PASS" if r.passed else "FAIL",
                    ";".join(r.matched_signals),
                    ";".join(r.failed_signals),
                    r.evidence_excerpt[:150],
                ])

    print(f"Results written to: {output_path}")
    print()
    print("Summary:")
    print(f"{'Model':<10} {'Passed':<8} {'Failed':<8} {'Total':<8}")
    print("-" * 34)
    any_fail = False
    for model, results in all_results.items():
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        print(f"{model:<10} {passed:<8} {failed:<8} {len(results):<8}")
        if failed > 0:
            any_fail = True

    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())
