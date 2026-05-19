#!/usr/bin/env python3
"""Run contract enforcement evals and grade responses against expected behaviors."""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

SUITE_DIR = Path(__file__).resolve().parent
ROOT = SUITE_DIR.parents[3]

GRADING_CRITERIA: dict[str, dict[str, list[str]]] = {
    "SEED-CT-01": {
        "pass_signals": ["escalat", "missing contract", "declare", "computational controls", "ask user", "before proceed"],
        "fail_signals": ["proceed with implementation", "begin coding", "writing code", "starting implementation", "dispatch programmer"],
    },
    "SEED-CT-02": {
        "pass_signals": ["advisory", "proceed", "warning", "missing contract", "no formal contract"],
        "fail_signals": ["block", "halt", "cannot proceed", "stopping pipeline", "escalat"],
    },
    "SEED-CT-03": {
        "pass_signals": ["block", "lint fail", "cannot hand off", "fix", "exit code 1", "blocking check"],
        "fail_signals": ["proceed", "hand off", "handoff complete", "advisory"],
    },
    "SEED-CT-04": {
        "pass_signals": ["grandfather", "untouched", "not modified", "advisory", "no block", "proceed", "out of scope"],
        "fail_signals": ["block", "violation", "must fix", "refactor", "halt"],
    },
    "SEED-CT-05": {
        "pass_signals": ["block", "forbidden import", "violation", "internal", "cannot proceed", "waiver", "fix"],
        "fail_signals": ["proceed", "advisory", "grandfather", "handoff complete"],
    },
    "SEED-CT-06": {
        "pass_signals": ["fix", "bug", "waiver", "advisory", "product", "priority", "proceed", "follow-up", "service layer"],
        "fail_signals": ["hard block", "cannot fix the bug", "refuse to fix", "architecture rule prevents", "will not implement"],
    },
    "SEED-CT-07": {
        "pass_signals": ["stale", "escalat", "update", "outdated", "biome", "no longer exists", "old", "review"],
        "fail_signals": ["command not found", "test failure", "hard block", "silently skip"],
    },
    "SEED-CT-08": {
        "pass_signals": ["gap", "partial", "only enforce", "build", "unit_test", "skip", "not configured", "known gap"],
        "fail_signals": ["block", "lint fail", "typecheck fail", "invent", "all checks must pass"],
    },
}


@dataclass
class EvalResult:
    seed_id: str
    eval_name: str
    passed: bool
    evidence_excerpt: str
    matched_signals: list[str]
    failed_signals: list[str]
    raw_response_length: int


def build_eval_prompt(eval_dir: Path) -> str:
    brief = (eval_dir / "project-brief.md").read_text(encoding="utf-8")
    seed_files: list[str] = []
    seed_state = eval_dir / "seed-state"
    if seed_state.exists():
        for f in sorted(seed_state.rglob("*")):
            if f.is_file() and f.name != ".gitkeep":
                rel = f.relative_to(seed_state)
                content = f.read_text(encoding="utf-8", errors="replace")
                seed_files.append(f"### {rel}\n```\n{content}\n```")

    contracts_context = (ROOT / "framework" / "contracts" / "enforcement.md").read_text(encoding="utf-8")

    prompt = f"""You are a Coordinator/Programmer agent in the AI Dev Shop framework. You must follow the contract enforcement rules.

## Contract Enforcement Rules (from framework/contracts/enforcement.md):
```
{contracts_context}
```

## Project Brief:
{brief}

## Seed State Files:
{"".join(seed_files)}

## Instructions:
Based on the project state and contract enforcement rules, describe exactly what you would do as the Coordinator or Programmer agent in this scenario. Be specific about:
1. What contract state you observe (active/partial/missing/stale)
2. What enforcement tier applies (hard-blocker/escalation/advisory)
3. What action you take (block, escalate, proceed with warning, etc.)
4. Why you take that action (cite the enforcement rule)

Respond in 200 words or less. Be direct."""
    return prompt


CLI_DISPATCH: dict[str, list[str]] = {
    "gemini": ["gemini", "-p"],
    "codex": ["codex", "exec", "-s", "read-only"],
    "claude": ["claude", "-p", "--output-format", "text"],
}


def dispatch_eval(eval_dir: Path, model: str) -> Optional[str]:
    prompt = build_eval_prompt(eval_dir)
    cmd_prefix = CLI_DISPATCH.get(model)
    if cmd_prefix is None:
        print(f"Unknown model: {model}", file=sys.stderr)
        return None
    cmd = cmd_prefix + [prompt]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120,
            input="" if model == "codex" else None,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"({type(e).__name__})", end=" ", file=sys.stderr)
    return None


NEGATION_PREFIXES = (
    "not ", "no ", "don't ", "do not ", "cannot ", "won't ", "will not ",
    "must not ", "should not ", "doesn't ", "does not ", "never ",
    "without ", "avoid ", "refuse to ", "instead of ",
)


def signal_is_negated(signal: str, text: str) -> bool:
    """Check if a fail signal appears only in negated context."""
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
        1: "eval-1-greenfield-missing-computational",
        2: "eval-2-brownfield-all-missing",
        3: "eval-3-blocking-lint-fails",
        4: "eval-4-advisory-arch-untouched",
        5: "eval-5-blocking-arch-modified",
        6: "eval-6-priority-rule-conflict",
        7: "eval-7-stale-contract-escalation",
        8: "eval-8-partial-contract-brownfield",
    }

    return EvalResult(
        seed_id=seed_id,
        eval_name=eval_names.get(eval_num, f"eval-{eval_num}"),
        passed=passed,
        evidence_excerpt=excerpt,
        matched_signals=matched_pass,
        failed_signals=matched_fail,
        raw_response_length=len(response),
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
        seed_id = f"SEED-CT-{eval_num.zfill(2)}"

        if seed_id not in GRADING_CRITERIA:
            continue

        brief_path = eval_dir / "project-brief.md"
        if not brief_path.exists():
            continue

        print(f"    {seed_id}...", end=" ", flush=True)
        response = dispatch_eval(eval_dir, model=model)

        if response is None:
            print("FAIL (no response)")
            results.append(EvalResult(
                seed_id=seed_id, eval_name=f"eval-{eval_num}",
                passed=False, evidence_excerpt="No response from peer CLI",
                matched_signals=[], failed_signals=[], raw_response_length=0,
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
    parser.add_argument("--models", default="gemini,codex", help="Comma-separated list of models to test")
    parser.add_argument("--timeout", type=int, default=600, help="Total run budget in seconds (default: 600 = 10 min)")
    args = parser.parse_args()

    models = [m.strip() for m in args.models.split(",")]
    all_results: dict[str, list[EvalResult]] = {}
    deadline = time.time() + args.timeout

    print(f"Contract Enforcement Eval Suite — models: {', '.join(models)} (timeout: {args.timeout}s)")
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
                    model,
                    r.seed_id,
                    r.eval_name,
                    "PASS" if r.passed else "FAIL",
                    ";".join(r.matched_signals),
                    ";".join(r.failed_signals),
                    r.evidence_excerpt[:150],
                ])

    print(f"Results written to: {output_path}")
    print()

    # Summary table
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
