#!/usr/bin/env python3
"""Score a seeded eval suite and emit aggregate metrics.

Reads seed-catalog.tsv and run-results.tsv, computes per-seed, per-dimension,
per-bug-nature, per-structure, and per-difficulty breakdowns, false-positive
rate, severity accuracy, cross-dimension stability, and emits a computed status
label.

Usage:
    python3 harness-engineering/quality/scripts/score_eval_suite.py <suite-dir>
    python3 harness-engineering/quality/scripts/score_eval_suite.py <suite-dir> \
        --baseline-results <previous-run-results.tsv>
    python3 harness-engineering/quality/scripts/score_eval_suite.py <suite-dir> \
        --output <report-path.md>
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

SCORE_MAP = {"CAUGHT": 1.0, "PARTIAL": 0.5, "MISSED": 0.0, "FALSE_POSITIVE": 0.0}

STABILITY_THRESHOLD = 0.3  # drop > this flags a stability regression

# Minimum negative-control ratio for benchmark suites.
NEGATIVE_CONTROL_RATIO = 0.15

# Per-dimension seed density floors.
PILOT_DIMENSION_FLOOR = 5
BENCHMARK_DIMENSION_FLOOR = 8


# ---------------------------------------------------------------------------
# TSV loading (shared with validate_eval_suite.py)
# ---------------------------------------------------------------------------

def load_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = []
        for raw in reader:
            row = {k: (v or "").strip() for k, v in raw.items()}
            if any(row.values()):
                rows.append(row)
        return rows


# ---------------------------------------------------------------------------
# Core scoring
# ---------------------------------------------------------------------------

def compute_per_seed_catch_rate(
    results: list[dict[str, str]],
) -> dict[str, dict[str, object]]:
    """Return {seed_id: {runs, caught, partial, missed, fp, catch_rate, scores}}."""
    by_seed: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for row in results:
        by_seed[row["seed_id"]].append(row)

    out: dict[str, dict[str, object]] = {}
    for seed_id, rows in sorted(by_seed.items()):
        scores = [SCORE_MAP.get(r["result"], 0.0) for r in rows]
        counts = Counter(r["result"] for r in rows)
        sev_correct = sum(1 for r in rows if r["severity_correct"] == "yes")
        sev_applicable = sum(1 for r in rows if r["severity_correct"] in ("yes", "no"))
        out[seed_id] = {
            "runs": len(rows),
            "caught": counts.get("CAUGHT", 0),
            "partial": counts.get("PARTIAL", 0),
            "missed": counts.get("MISSED", 0),
            "false_positive": counts.get("FALSE_POSITIVE", 0),
            "catch_rate": sum(scores) / len(scores) if scores else 0.0,
            "severity_accuracy": (sev_correct / sev_applicable) if sev_applicable else None,
            "scores": scores,
        }
    return out


def build_seed_index(catalog: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["seed_id"]: row for row in catalog}


def group_catch_rates(
    seed_rates: dict[str, dict[str, object]],
    seed_index: dict[str, dict[str, str]],
    group_key: str,
) -> dict[str, dict[str, float]]:
    """Group catch rates by a seed-catalog column (agent_dimension, bug_nature, etc.)."""
    groups: defaultdict[str, list[float]] = defaultdict(list)
    for seed_id, stats in seed_rates.items():
        meta = seed_index.get(seed_id)
        if not meta:
            continue
        groups[meta.get(group_key, "unknown")].append(stats["catch_rate"])

    out = {}
    for key, rates in sorted(groups.items()):
        out[key] = {
            "mean_catch_rate": sum(rates) / len(rates) if rates else 0.0,
            "seed_count": len(rates),
        }
    return out


def compute_false_positive_rate(
    seed_rates: dict[str, dict[str, object]],
    seed_index: dict[str, dict[str, str]],
) -> dict[str, object]:
    """FP rate from negative controls: how often the agent flagged a non-bug."""
    nc_seeds = [
        sid for sid, meta in seed_index.items()
        if meta.get("control_type") == "negative_control"
    ]
    if not nc_seeds:
        return {"negative_controls": 0, "fp_rate": None, "detail": "no negative controls in suite"}

    total_runs = 0
    total_fps = 0
    for sid in nc_seeds:
        stats = seed_rates.get(sid)
        if not stats:
            continue
        # For negative controls, MISSED means the agent correctly did NOT flag it.
        # FALSE_POSITIVE or CAUGHT means the agent incorrectly flagged the non-bug.
        total_runs += stats["runs"]
        total_fps += stats["caught"] + stats["false_positive"]

    fp_rate = total_fps / total_runs if total_runs else 0.0
    return {
        "negative_controls": len(nc_seeds),
        "total_nc_runs": total_runs,
        "false_positives": total_fps,
        "fp_rate": fp_rate,
    }


def compute_severity_accuracy(
    seed_rates: dict[str, dict[str, object]],
    seed_index: dict[str, dict[str, str]],
) -> dict[str, object]:
    """Severity accuracy across all standard + positive/regression seeds."""
    correct = 0
    applicable = 0
    for sid, stats in seed_rates.items():
        meta = seed_index.get(sid, {})
        if meta.get("control_type") == "negative_control":
            continue
        sa = stats.get("severity_accuracy")
        if sa is not None:
            # Weight by number of applicable runs
            runs = stats["runs"]
            caught_or_partial = stats["caught"] + stats["partial"]
            if caught_or_partial > 0:
                correct += round(sa * caught_or_partial)
                applicable += caught_or_partial

    return {
        "severity_accuracy": correct / applicable if applicable else None,
        "applicable_findings": applicable,
    }


# ---------------------------------------------------------------------------
# Cross-dimension stability (attention-budget metric)
# ---------------------------------------------------------------------------

def compute_stability_deltas(
    current_rates: dict[str, dict[str, object]],
    baseline_rates: dict[str, dict[str, object]],
    seed_index: dict[str, dict[str, str]],
    changed_dimensions: set[str] | None = None,
) -> list[dict[str, object]]:
    """Compare current vs baseline catch rates, flag regressions."""
    regressions = []
    for seed_id in sorted(set(current_rates) & set(baseline_rates)):
        baseline_cr = baseline_rates[seed_id]["catch_rate"]
        current_cr = current_rates[seed_id]["catch_rate"]
        delta = current_cr - baseline_cr

        if delta < -STABILITY_THRESHOLD:
            meta = seed_index.get(seed_id, {})
            dimension = meta.get("agent_dimension", "unknown")
            is_cross_dimension = (
                changed_dimensions is not None
                and dimension not in changed_dimensions
            )
            regressions.append({
                "seed_id": seed_id,
                "dimension": dimension,
                "baseline_catch_rate": baseline_cr,
                "current_catch_rate": current_cr,
                "delta": delta,
                "is_attention_budget_regression": is_cross_dimension,
            })
    return regressions


# ---------------------------------------------------------------------------
# Status label computation
# ---------------------------------------------------------------------------

def compute_status_label(
    catalog: list[dict[str, str]],
    seed_index: dict[str, dict[str, str]],
    results: list[dict[str, str]],
    matrix_path: Path,
    controls_path: Path,
    has_advanced_structures: bool,
    run_count: int,
) -> tuple[str, list[str]]:
    """Compute exploratory/pilot/benchmark/stable_benchmark and reasons."""
    reasons = []
    total_standard = sum(
        1 for s in catalog if s.get("control_type", "standard") == "standard"
    )
    total_seeds = len(catalog)

    has_matrix = matrix_path.exists()
    has_controls = controls_path.exists()

    control_types = {s.get("control_type") for s in catalog}
    has_positive = "positive_control" in control_types
    has_negative = "negative_control" in control_types
    has_regression = "regression" in control_types
    has_all_controls = has_positive and has_negative and has_regression

    difficulties = {s.get("difficulty") for s in catalog}
    has_all_tiers = {"Easy", "Medium", "Hard"}.issubset(difficulties)

    # Count benchmark_full runs
    benchmark_runs = set()
    for row in results:
        benchmark_runs.add(row.get("run_id", ""))
    distinct_runs = len(benchmark_runs)

    # Check negative control ratio
    nc_count = sum(1 for s in catalog if s.get("control_type") == "negative_control")
    nc_ratio_ok = nc_count >= math.ceil(total_standard * NEGATIVE_CONTROL_RATIO) if total_standard > 0 else False

    # Check per-dimension density
    dim_counts: Counter[str] = Counter()
    for s in catalog:
        if s.get("control_type", "standard") != "negative_control":
            dim_counts[s.get("agent_dimension", "unknown")] += 1

    all_dims_above_benchmark = all(c >= BENCHMARK_DIMENSION_FLOOR for c in dim_counts.values()) if dim_counts else False
    all_dims_above_pilot = all(c >= PILOT_DIMENSION_FLOOR for c in dim_counts.values()) if dim_counts else False

    # Determine label
    if not has_matrix or not has_controls:
        label = "exploratory"
        if not has_matrix:
            reasons.append("no coverage-matrix.tsv")
        if not has_controls:
            reasons.append("no controls.md")
    elif total_seeds < 30 or not has_advanced_structures:
        label = "pilot"
        if total_seeds < 30:
            reasons.append(f"only {total_seeds} seeds (need 30+ for pilot minimum)")
        if not has_advanced_structures:
            reasons.append("no advanced seed structures (combined/layered/distributed/camouflaged/interference)")
    elif (
        total_seeds >= 36
        and has_all_controls
        and has_all_tiers
        and has_advanced_structures
        and run_count >= 3
    ):
        if total_seeds >= 54 and nc_ratio_ok and all_dims_above_benchmark:
            label = "stable benchmark"
            reasons.append("54+ seeds, all controls, all tiers, 3+ runs, NC ratio met, dimension density met")
        else:
            label = "benchmark"
            reasons.append("36+ seeds, all controls, all tiers, 3+ runs")
            if not nc_ratio_ok:
                reasons.append(f"negative-control ratio below 15% ({nc_count} NCs for {total_standard} standard seeds)")
            if not all_dims_above_benchmark:
                thin_dims = [d for d, c in dim_counts.items() if c < BENCHMARK_DIMENSION_FLOOR]
                reasons.append(f"thin dimensions (< {BENCHMARK_DIMENSION_FLOOR} seeds): {', '.join(thin_dims)}")
    else:
        label = "pilot"
        if not has_all_controls:
            missing_controls = []
            if not has_positive:
                missing_controls.append("positive_control")
            if not has_negative:
                missing_controls.append("negative_control")
            if not has_regression:
                missing_controls.append("regression")
            reasons.append(f"missing control types: {', '.join(missing_controls)}")
        if not has_all_tiers:
            reasons.append(f"missing difficulty tiers: {', '.join({'Easy', 'Medium', 'Hard'} - difficulties)}")
        if run_count < 3:
            reasons.append(f"only {run_count} runs (need 3+ for benchmark)")

    return label, reasons


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def format_pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100:.1f}%"


def generate_report(
    suite_dir: Path,
    catalog: list[dict[str, str]],
    results: list[dict[str, str]],
    seed_rates: dict[str, dict[str, object]],
    seed_index: dict[str, dict[str, str]],
    stability_regressions: list[dict[str, object]] | None,
    status_label: str,
    status_reasons: list[str],
) -> str:
    lines = []
    lines.append(f"# Eval Suite Score Report — {suite_dir.name}")
    lines.append("")
    lines.append(f"**Suite:** `{suite_dir}`")
    lines.append(f"**Status Label:** `{status_label}`")
    for reason in status_reasons:
        lines.append(f"  - {reason}")
    lines.append("")

    # Overall score
    all_rates = [s["catch_rate"] for s in seed_rates.values()
                 if seed_index.get(s_id := "", {}).get("control_type") != "negative_control"
                 # We need seed_id, iterate differently
                 ]
    # Recompute properly
    standard_rates = []
    for sid, stats in seed_rates.items():
        meta = seed_index.get(sid, {})
        if meta.get("control_type") != "negative_control":
            standard_rates.append(stats["catch_rate"])

    mean_score = sum(standard_rates) / len(standard_rates) if standard_rates else 0.0
    lines.append(f"**Mean Catch Rate (non-NC seeds):** {format_pct(mean_score)}")

    # Run count
    run_ids = {r["run_id"] for r in results}
    lines.append(f"**Distinct Runs Scored:** {len(run_ids)}")
    lines.append(f"**Total Seeds in Catalog:** {len(catalog)}")
    lines.append("")

    # FP rate
    fp = compute_false_positive_rate(seed_rates, seed_index)
    lines.append("## False Positive Rate")
    lines.append("")
    lines.append(f"- Negative controls: {fp['negative_controls']}")
    if fp["fp_rate"] is not None:
        lines.append(f"- FP rate: {format_pct(fp['fp_rate'])} ({fp['false_positives']} FPs across {fp['total_nc_runs']} NC runs)")
    else:
        lines.append(f"- FP rate: N/A ({fp.get('detail', '')})")
    lines.append("")

    # Severity accuracy
    sev = compute_severity_accuracy(seed_rates, seed_index)
    lines.append("## Severity Accuracy")
    lines.append("")
    lines.append(f"- Accuracy: {format_pct(sev['severity_accuracy'])} ({sev['applicable_findings']} applicable findings)")
    lines.append("")

    # Per-seed detail
    lines.append("## Per-Seed Catch Rates")
    lines.append("")
    lines.append("| Seed | Dimension | Bug Nature | Structure | Difficulty | Control | Catch Rate | Runs |")
    lines.append("|------|-----------|-----------|-----------|------------|---------|------------|------|")
    for sid in sorted(seed_rates.keys()):
        stats = seed_rates[sid]
        meta = seed_index.get(sid, {})
        lines.append(
            f"| {sid} "
            f"| {meta.get('agent_dimension', '?')} "
            f"| {meta.get('bug_nature', '?')} "
            f"| {meta.get('seed_structure', '?')} "
            f"| {meta.get('difficulty', '?')} "
            f"| {meta.get('control_type', '?')} "
            f"| {format_pct(stats['catch_rate'])} "
            f"| {stats['runs']} |"
        )
    lines.append("")

    # Breakdowns
    for group_key, title in [
        ("agent_dimension", "Per-Dimension Breakdown"),
        ("bug_nature", "Per-Bug-Nature Breakdown"),
        ("seed_structure", "Per-Structure Breakdown"),
        ("difficulty", "Per-Difficulty Breakdown"),
    ]:
        grouped = group_catch_rates(seed_rates, seed_index, group_key)
        lines.append(f"## {title}")
        lines.append("")
        lines.append(f"| {group_key} | Seeds | Mean Catch Rate |")
        lines.append("|---|---|---|")
        for key, data in grouped.items():
            lines.append(f"| {key} | {data['seed_count']} | {format_pct(data['mean_catch_rate'])} |")
        lines.append("")

    # Dimension density
    lines.append("## Dimension Density")
    lines.append("")
    dim_counts: Counter[str] = Counter()
    for s in catalog:
        if s.get("control_type", "standard") != "negative_control":
            dim_counts[s.get("agent_dimension", "unknown")] += 1
    lines.append("| Dimension | Seed Count | Meets Pilot (5) | Meets Benchmark (8) |")
    lines.append("|-----------|-----------|-----------------|-------------------|")
    for dim, count in sorted(dim_counts.items()):
        pilot_ok = "yes" if count >= PILOT_DIMENSION_FLOOR else "**NO**"
        bench_ok = "yes" if count >= BENCHMARK_DIMENSION_FLOOR else "**NO**"
        lines.append(f"| {dim} | {count} | {pilot_ok} | {bench_ok} |")
    lines.append("")

    # Negative-control calibration
    nc_count = sum(1 for s in catalog if s.get("control_type") == "negative_control")
    std_count = sum(1 for s in catalog if s.get("control_type", "standard") == "standard")
    required_nc = math.ceil(std_count * NEGATIVE_CONTROL_RATIO) if std_count > 0 else 0
    lines.append("## Negative-Control Calibration")
    lines.append("")
    lines.append(f"- Standard seeds: {std_count}")
    lines.append(f"- Negative controls: {nc_count}")
    lines.append(f"- Required (15%): {required_nc}")
    lines.append(f"- Meets ratio: {'yes' if nc_count >= required_nc else '**NO**'}")
    lines.append("")

    # Stability regressions
    lines.append("## Cross-Dimension Stability")
    lines.append("")
    if stability_regressions is None:
        lines.append("*No baseline provided — stability comparison skipped.*")
        lines.append("Pass `--baseline-results` to enable attention-budget regression detection.")
    elif not stability_regressions:
        lines.append("No stability regressions detected (all seeds within 0.3 of baseline).")
    else:
        attn_budget = [r for r in stability_regressions if r["is_attention_budget_regression"]]
        lines.append(f"**Stability regressions:** {len(stability_regressions)}")
        lines.append(f"**Attention-budget regressions:** {len(attn_budget)}")
        lines.append("")
        lines.append("| Seed | Dimension | Baseline | Current | Delta | Attention-Budget? |")
        lines.append("|------|-----------|----------|---------|-------|-------------------|")
        for reg in stability_regressions:
            lines.append(
                f"| {reg['seed_id']} "
                f"| {reg['dimension']} "
                f"| {format_pct(reg['baseline_catch_rate'])} "
                f"| {format_pct(reg['current_catch_rate'])} "
                f"| {reg['delta']:+.2f} "
                f"| {'**YES**' if reg['is_attention_budget_regression'] else 'no'} |"
            )
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Score a seeded eval suite.")
    parser.add_argument("suite_dir", help="Path to the eval suite root")
    parser.add_argument(
        "--baseline-results",
        help="Path to a previous run-results.tsv for stability comparison",
    )
    parser.add_argument(
        "--changed-dimensions",
        help="Comma-separated list of dimensions that were changed (for attention-budget flagging)",
    )
    parser.add_argument(
        "--output",
        help="Write report to this file instead of stdout",
    )
    args = parser.parse_args()

    suite_dir = Path(args.suite_dir).resolve()
    seed_path = suite_dir / "seed-catalog.tsv"
    results_path = suite_dir / "run-results.tsv"
    matrix_path = suite_dir / "coverage-matrix.tsv"
    controls_path = suite_dir / "controls.md"

    # Load data
    if not seed_path.exists():
        print(f"ERROR: {seed_path} not found", file=sys.stderr)
        return 1
    if not results_path.exists():
        print(f"ERROR: {results_path} not found", file=sys.stderr)
        return 1

    catalog = load_tsv(seed_path)
    results = load_tsv(results_path)
    seed_index = build_seed_index(catalog)

    # Core scoring
    seed_rates = compute_per_seed_catch_rate(results)

    # Stability comparison
    stability_regressions = None
    if args.baseline_results:
        baseline_path = Path(args.baseline_results).resolve()
        if not baseline_path.exists():
            print(f"ERROR: baseline {baseline_path} not found", file=sys.stderr)
            return 1
        baseline_results = load_tsv(baseline_path)
        baseline_rates = compute_per_seed_catch_rate(baseline_results)
        changed_dims = None
        if args.changed_dimensions:
            changed_dims = {d.strip() for d in args.changed_dimensions.split(",")}
        stability_regressions = compute_stability_deltas(
            seed_rates, baseline_rates, seed_index, changed_dims,
        )

    # Status label
    structures = {s.get("seed_structure") for s in catalog}
    has_advanced = bool(
        structures & {"combined", "layered", "distributed", "camouflaged", "interference"}
    )
    run_ids = {r["run_id"] for r in results}
    status_label, status_reasons = compute_status_label(
        catalog, seed_index, results, matrix_path, controls_path,
        has_advanced, len(run_ids),
    )

    # Report
    report = generate_report(
        suite_dir, catalog, results, seed_rates, seed_index,
        stability_regressions, status_label, status_reasons,
    )

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")
        print(f"Report written to {out_path}")
    else:
        print(report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
