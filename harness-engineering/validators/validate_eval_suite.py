#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

BUG_NATURES = {
    "contradiction",
    "omission",
    "boundary_error",
    "semantic_mismatch",
    "severity_misclassification",
    "cosmetic_fix",
    "type_contract_error",
    "missing_test",
    "anti_pattern",
    "hidden_dependency",
    "dead_code",
    "state_leak",
    "invariant_violation",
}

SEED_STRUCTURES = {
    "single",
    "combined",
    "layered",
    "distributed",
    "camouflaged",
    "interference",
}

DIFFICULTIES = {"Easy", "Medium", "Hard"}
REQUIREMENTS = {"required", "optional", "pruned"}
CONTROL_TYPES = {"standard", "positive_control", "negative_control", "regression"}
SEVERITIES = {"Critical", "Required", "Recommended"}
FALSE_POSITIVE_RISKS = {"None", "Low", "Medium", "High"}
RESULTS = {"CAUGHT", "PARTIAL", "MISSED", "FALSE_POSITIVE"}
SEVERITY_CORRECT = {"yes", "no", "na"}
RUN_SCOPES = {"benchmark_full", "targeted_regression"}
SUITE_KINDS = {"benchmark", "targeted_regression"}
EXECUTION_MODES = {"repo_persona_subagent", "repo_persona_host", "external_peer_cli"}

# Negative-control calibration: benchmark suites need NCs >= 15% of standard seeds.
NEGATIVE_CONTROL_RATIO = 0.15

# Per-dimension seed density floors.
PILOT_DIMENSION_FLOOR = 5
BENCHMARK_DIMENSION_FLOOR = 8

MATRIX_COLUMNS = {
    "cell_id",
    "agent",
    "agent_dimension",
    "bug_nature",
    "seed_structure",
    "difficulty",
    "requirement",
    "rationale",
    "seed_ids",
}

SEED_COLUMNS = {
    "seed_id",
    "eval_name",
    "agent",
    "agent_dimension",
    "skill_source",
    "agent_guard",
    "bug_nature",
    "seed_structure",
    "difficulty",
    "control_type",
    "expected_severity",
    "false_positive_risk",
    "evidence_path",
    "detail_ref",
    "matrix_cell_id",
}

RUN_COLUMNS = {
    "run_id",
    "seed_id",
    "result",
    "severity_correct",
    "reviewer_notes",
}

RUN_MANIFEST_COLUMNS = {
    "run_id",
    "agent",
    "execution_mode",
    "persona_source",
    "llm_family",
    "model_id",
    "model_label",
    "cli_name",
    "cli_version",
    "selection_source",
    "run_scope",
    "target_seed_ids",
    "workdir",
    "prompt_path",
    "output_path",
    "executed_at",
}


def load_tsv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError(f"{path} has no header row")
        rows = []
        for raw in reader:
            row = {key: (value or "").strip() for key, value in raw.items()}
            if not any(row.values()):
                continue
            rows.append(row)
        return rows, list(reader.fieldnames)


def violation(message: str, fix: str) -> str:
    return f"VIOLATION: {message}\nFIX: {fix}"


def require_columns(found: list[str], expected: set[str], path: Path) -> list[str]:
    missing = sorted(expected.difference(found))
    if not missing:
        return []
    return [
        violation(
            f"{path} is missing required columns: {', '.join(missing)}",
            f"Add the missing TSV columns to {path}.",
        )
    ]


def validate_matrix(rows: list[dict[str, str]], path: Path) -> tuple[dict[str, dict[str, str]], list[str]]:
    errors: list[str] = []
    cells: dict[str, dict[str, str]] = {}

    for index, row in enumerate(rows, start=2):
        cell_id = row["cell_id"]
        if not cell_id:
            errors.append(
                violation(
                    f"{path}:{index} has an empty cell_id",
                    "Give every coverage row a stable cell_id.",
                )
            )
            continue
        if cell_id in cells:
            errors.append(
                violation(
                    f"{path}:{index} duplicates cell_id '{cell_id}'",
                    "Use unique cell_id values in coverage-matrix.tsv.",
                )
            )
            continue
        if row["bug_nature"] not in BUG_NATURES:
            errors.append(
                violation(
                    f"{path}:{index} uses unknown bug_nature '{row['bug_nature']}'",
                    "Use a bug_nature from eval-coverage-model.md.",
                )
            )
        if row["seed_structure"] not in SEED_STRUCTURES:
            errors.append(
                violation(
                    f"{path}:{index} uses unknown seed_structure '{row['seed_structure']}'",
                    "Use a seed_structure from eval-coverage-model.md.",
                )
            )
        if row["difficulty"] not in DIFFICULTIES:
            errors.append(
                violation(
                    f"{path}:{index} uses unknown difficulty '{row['difficulty']}'",
                    "Use Easy, Medium, or Hard.",
                )
            )
        if row["requirement"] not in REQUIREMENTS:
            errors.append(
                violation(
                    f"{path}:{index} uses unknown requirement '{row['requirement']}'",
                    "Use required, optional, or pruned.",
                )
            )
        if row["requirement"] in {"required", "pruned"} and not row["rationale"]:
            errors.append(
                violation(
                    f"{path}:{index} leaves rationale empty for '{row['requirement']}' cell '{cell_id}'",
                    "Document why the cell is required or why it was pruned.",
                )
            )
        cells[cell_id] = row

    return cells, errors


def validate_seed_catalog(
    rows: list[dict[str, str]],
    path: Path,
    cells: dict[str, dict[str, str]],
    suite_kind: str,
) -> tuple[set[str], list[str]]:
    errors: list[str] = []
    seed_ids: set[str] = set()
    by_cell: defaultdict[str, list[str]] = defaultdict(list)
    control_counts: Counter[str] = Counter()
    difficulties: set[str] = set()
    structures: set[str] = set()

    for index, row in enumerate(rows, start=2):
        seed_id = row["seed_id"]
        if not seed_id:
            errors.append(
                violation(
                    f"{path}:{index} has an empty seed_id",
                    "Give every seed a stable seed_id.",
                )
            )
            continue
        if seed_id in seed_ids:
            errors.append(
                violation(
                    f"{path}:{index} duplicates seed_id '{seed_id}'",
                    "Use unique seed_id values in seed-catalog.tsv.",
                )
            )
            continue
        seed_ids.add(seed_id)

        if row["bug_nature"] not in BUG_NATURES:
            errors.append(
                violation(
                    f"{path}:{index} uses unknown bug_nature '{row['bug_nature']}'",
                    "Use a bug_nature from eval-coverage-model.md.",
                )
            )
        if row["seed_structure"] not in SEED_STRUCTURES:
            errors.append(
                violation(
                    f"{path}:{index} uses unknown seed_structure '{row['seed_structure']}'",
                    "Use a seed_structure from eval-coverage-model.md.",
                )
            )
        if row["difficulty"] not in DIFFICULTIES:
            errors.append(
                violation(
                    f"{path}:{index} uses unknown difficulty '{row['difficulty']}'",
                    "Use Easy, Medium, or Hard.",
                )
            )
        if row["control_type"] not in CONTROL_TYPES:
            errors.append(
                violation(
                    f"{path}:{index} uses unknown control_type '{row['control_type']}'",
                    "Use standard, positive_control, negative_control, or regression.",
                )
            )
        if row["expected_severity"] not in SEVERITIES:
            errors.append(
                violation(
                    f"{path}:{index} uses unknown expected_severity '{row['expected_severity']}'",
                    "Use Critical, Required, or Recommended.",
                )
            )
        if row["false_positive_risk"] not in FALSE_POSITIVE_RISKS:
            errors.append(
                violation(
                    f"{path}:{index} uses unknown false_positive_risk '{row['false_positive_risk']}'",
                    "Use None, Low, Medium, or High.",
                )
            )
        matrix_cell_id = row["matrix_cell_id"]
        if matrix_cell_id not in cells:
            errors.append(
                violation(
                    f"{path}:{index} references unknown matrix_cell_id '{matrix_cell_id}'",
                    "Point every seed to a real coverage-matrix.tsv cell.",
                )
            )
        else:
            cell = cells[matrix_cell_id]
            requirement = cell["requirement"]
            if requirement == "pruned":
                errors.append(
                    violation(
                        f"{path}:{index} assigns seed '{seed_id}' to pruned cell '{matrix_cell_id}'",
                        "Move the seed to a required or optional cell, or un-prune the target cell with rationale.",
                    )
                )
            for column in ("agent", "agent_dimension", "bug_nature", "seed_structure", "difficulty"):
                if row[column] != cell[column]:
                    errors.append(
                        violation(
                            f"{path}:{index} does not match coverage cell '{matrix_cell_id}' for column '{column}'",
                            f"Make seed '{seed_id}' agree with the matrix cell or move it to the correct coverage row.",
                        )
                    )
            by_cell[matrix_cell_id].append(seed_id)

        if not row["detail_ref"]:
            errors.append(
                violation(
                    f"{path}:{index} leaves detail_ref empty for '{seed_id}'",
                    "Point each seed at a detailed entry in seed-ledger.md.",
                )
            )
        if not row["evidence_path"]:
            errors.append(
                violation(
                    f"{path}:{index} leaves evidence_path empty for '{seed_id}'",
                    "Record the primary artifact or file:line for each seed.",
                )
            )

        control_counts[row["control_type"]] += 1
        difficulties.add(row["difficulty"])
        structures.add(row["seed_structure"])

    for cell_id, cell in cells.items():
        if cell["requirement"] == "required" and not by_cell.get(cell_id):
            errors.append(
                violation(
                    f"Required coverage cell '{cell_id}' has no seeds assigned in {path}",
                    "Add at least one seed to every required coverage cell.",
                )
            )

    if suite_kind == "benchmark":
        for required_control in ("positive_control", "negative_control", "regression"):
            if control_counts[required_control] == 0:
                errors.append(
                    violation(
                        f"{path} does not contain any '{required_control}' seeds",
                        "Add the missing control type to the suite.",
                    )
                )
    else:
        if control_counts["regression"] == 0:
            errors.append(
                violation(
                    f"{path} does not contain any 'regression' seeds",
                    "Targeted regression packs must contain at least one regression seed.",
                )
            )

    if suite_kind == "benchmark":
        if difficulties != DIFFICULTIES:
            missing = ", ".join(sorted(DIFFICULTIES.difference(difficulties)))
            errors.append(
                violation(
                    f"{path} does not cover all difficulty tiers; missing: {missing}",
                    "Ensure seed-catalog.tsv contains Easy, Medium, and Hard seeds.",
                )
            )

        if structures == {"single"} or not any(
            structure in structures
            for structure in {"combined", "layered", "distributed", "camouflaged", "interference"}
        ):
            errors.append(
                violation(
                    f"{path} only covers trivial seed structures",
                    "Add at least one non-single structure such as combined, layered, distributed, camouflaged, or interference.",
                )
            )

        # Negative-control calibration: NCs >= 15% of standard seeds.
        standard_count = control_counts["standard"]
        nc_count = control_counts["negative_control"]
        required_nc = math.ceil(standard_count * NEGATIVE_CONTROL_RATIO) if standard_count > 0 else 1
        if nc_count < required_nc:
            errors.append(
                violation(
                    f"{path} has {nc_count} negative control(s) but needs at least {required_nc} "
                    f"(15% of {standard_count} standard seeds)",
                    "Add more negative controls to meaningfully measure false-positive tendency.",
                )
            )

        # Per-dimension seed density.
        dim_counts: Counter[str] = Counter()
        for row2 in rows:
            if row2.get("control_type", "standard") != "negative_control":
                dim_counts[row2.get("agent_dimension", "unknown")] += 1
        thin_dims = [d for d, c in dim_counts.items() if c < BENCHMARK_DIMENSION_FLOOR]
        if thin_dims:
            errors.append(
                violation(
                    f"{path} has dimensions below the benchmark density floor "
                    f"({BENCHMARK_DIMENSION_FLOOR} seeds): {', '.join(sorted(thin_dims))}",
                    "Add seeds to thin dimensions or document in coverage-matrix.tsv rationale why fewer suffice.",
                )
            )

    return seed_ids, errors


def parse_target_seed_ids(value: str, seed_ids: set[str]) -> tuple[set[str], list[str]]:
    if value == "all":
        return set(seed_ids), []
    targets = {item.strip() for item in value.split(",") if item.strip()}
    if not targets:
        return set(), [
            violation(
                "run-manifest.tsv contains an empty target_seed_ids field",
                "Use 'all' or a comma-separated list of seed IDs.",
            )
        ]
    unknown = sorted(targets.difference(seed_ids))
    if unknown:
        return set(), [
            violation(
                f"run-manifest.tsv references unknown seed IDs: {', '.join(unknown)}",
                "Use only seed IDs declared in seed-catalog.tsv.",
            )
        ]
    return targets, []


def validate_run_manifest(
    rows: list[dict[str, str]],
    path: Path,
    seed_ids: set[str],
    require_runs: bool,
    suite_kind: str,
) -> tuple[dict[str, set[str]], dict[str, str], list[str]]:
    errors: list[str] = []
    run_targets: dict[str, set[str]] = {}
    run_scopes: dict[str, str] = {}

    if not rows:
        if require_runs:
            errors.append(
                violation(
                    f"{path} is missing or empty but run results are required",
                    "Persist run-manifest.tsv alongside run-results.tsv.",
                )
            )
        return run_targets, run_scopes, errors

    for index, row in enumerate(rows, start=2):
        run_id = row["run_id"]
        if not run_id:
            errors.append(
                violation(
                    f"{path}:{index} has an empty run_id",
                    "Give every manifest row a stable run_id.",
                )
            )
            continue
        if run_id in run_targets:
            errors.append(
                violation(
                    f"{path}:{index} duplicates run_id '{run_id}'",
                    "Use unique run_id values in run-manifest.tsv.",
                )
            )
            continue

        for column in (
            "agent",
            "execution_mode",
            "persona_source",
            "llm_family",
            "model_id",
            "model_label",
            "cli_name",
            "cli_version",
            "selection_source",
            "workdir",
            "prompt_path",
            "output_path",
            "executed_at",
        ):
            if not row[column]:
                errors.append(
                    violation(
                        f"{path}:{index} leaves '{column}' empty for run '{run_id}'",
                        f"Populate '{column}' in run-manifest.tsv for run '{run_id}'.",
                    )
                )

        execution_mode = row["execution_mode"]
        persona_source = row["persona_source"]
        if execution_mode not in EXECUTION_MODES:
            errors.append(
                violation(
                    f"{path}:{index} uses unknown execution_mode '{execution_mode}'",
                    "Use repo_persona_subagent, repo_persona_host, or external_peer_cli.",
                )
            )
        else:
            if execution_mode == "external_peer_cli":
                if persona_source != "none":
                    errors.append(
                        violation(
                            f"{path}:{index} marks run '{run_id}' as external_peer_cli but persona_source is '{persona_source}'",
                            "Use persona_source 'none' for external_peer_cli runs.",
                        )
                    )
            else:
                if persona_source == "none":
                    errors.append(
                        violation(
                            f"{path}:{index} marks run '{run_id}' as {execution_mode} but persona_source is 'none'",
                            "Record the repo persona bootstrap path, such as agents/<agent>/skills.md.",
                        )
                    )

        run_scope = row["run_scope"]
        if run_scope not in RUN_SCOPES:
            errors.append(
                violation(
                    f"{path}:{index} uses unknown run_scope '{run_scope}'",
                    "Use benchmark_full or targeted_regression.",
                )
            )
            continue

        targets, target_errors = parse_target_seed_ids(row["target_seed_ids"], seed_ids)
        errors.extend(target_errors)
        if target_errors:
            continue

        if run_scope == "benchmark_full" and targets != seed_ids:
            errors.append(
                violation(
                    f"{path}:{index} marks run '{run_id}' as benchmark_full but target_seed_ids is not 'all'",
                    "Benchmark full runs must target every seed in the suite.",
                )
            )
        if run_scope == "targeted_regression" and targets == seed_ids and suite_kind == "targeted_regression":
            errors.append(
                violation(
                    f"{path}:{index} marks run '{run_id}' as targeted_regression but targets every seed in the suite",
                    "Targeted regression runs should list only the unresolved seed subset. Use benchmark_full for all-seed runs.",
                )
            )

        run_targets[run_id] = targets
        run_scopes[run_id] = run_scope

    if suite_kind == "benchmark" and require_runs and "benchmark_full" not in set(run_scopes.values()):
        errors.append(
            violation(
                f"{path} does not contain any benchmark_full runs",
                "Benchmark suite validation requires at least one full-suite run in run-manifest.tsv.",
            )
        )

    return run_targets, run_scopes, errors


def validate_run_results(
    rows: list[dict[str, str]],
    path: Path,
    seed_ids: set[str],
    min_runs: int,
    require_runs: bool,
    suite_kind: str,
    run_targets: dict[str, set[str]],
    run_scopes: dict[str, str],
) -> list[str]:
    errors: list[str] = []

    if not rows:
        if require_runs:
            errors.append(
                violation(
                    f"{path} is missing or empty but run results are required",
                    "Persist run-results.tsv with one row per seed per run.",
                )
            )
        return errors

    runs_by_seed: defaultdict[str, set[str]] = defaultdict(set)
    benchmark_runs_by_seed: defaultdict[str, set[str]] = defaultdict(set)
    seeds_by_run: defaultdict[str, set[str]] = defaultdict(set)

    for index, row in enumerate(rows, start=2):
        run_id = row["run_id"]
        seed_id = row["seed_id"]
        result = row["result"]
        severity_correct = row["severity_correct"]

        if not run_id:
            errors.append(
                violation(
                    f"{path}:{index} has an empty run_id",
                    "Give every scored pass a run_id.",
                )
            )
            continue
        if run_id not in run_targets:
            errors.append(
                violation(
                    f"{path}:{index} references unknown run_id '{run_id}'",
                    "Declare every scored run in run-manifest.tsv before using it in run-results.tsv.",
                )
            )
            continue
        if seed_id not in seed_ids:
            errors.append(
                violation(
                    f"{path}:{index} references unknown seed_id '{seed_id}'",
                    "Score only seeds declared in seed-catalog.tsv.",
                )
            )
            continue
        if result not in RESULTS:
            errors.append(
                violation(
                    f"{path}:{index} uses unknown result '{result}'",
                    "Use CAUGHT, PARTIAL, MISSED, or FALSE_POSITIVE.",
                )
            )
        if severity_correct not in SEVERITY_CORRECT:
            errors.append(
                violation(
                    f"{path}:{index} uses unknown severity_correct value '{severity_correct}'",
                    "Use yes, no, or na.",
                )
            )

        runs_by_seed[seed_id].add(run_id)
        if run_scopes.get(run_id) == "benchmark_full":
            benchmark_runs_by_seed[seed_id].add(run_id)
        seeds_by_run[run_id].add(seed_id)

    if suite_kind == "benchmark":
        counted_runs = benchmark_runs_by_seed
        target_union = set(seed_ids)
        run_count_fix = f"Persist at least {min_runs} benchmark_full runs per seed before treating the suite as benchmark-grade."
    else:
        counted_runs = runs_by_seed
        target_union: set[str] = set()
        for run_id, targets in run_targets.items():
            if run_scopes.get(run_id) == "targeted_regression":
                target_union.update(targets)
        run_count_fix = f"Persist at least {min_runs} targeted_regression runs per targeted seed."

    for seed_id in sorted(target_union):
        run_count = len(counted_runs[seed_id])
        if run_count < min_runs:
            errors.append(
                violation(
                    f"Seed '{seed_id}' only appears in {run_count} qualifying run(s) in {path}",
                    run_count_fix,
                )
            )

    for run_id, scored_seed_ids in sorted(seeds_by_run.items()):
        target_seed_ids = run_targets.get(run_id, set())
        missing = target_seed_ids.difference(scored_seed_ids)
        extras = scored_seed_ids.difference(target_seed_ids)
        if missing:
            errors.append(
                violation(
                    f"Run '{run_id}' does not score every targeted seed; missing: {', '.join(sorted(missing))}",
                    "Record one run-results.tsv row per targeted seed for every declared run.",
                )
            )
        if extras:
            errors.append(
                violation(
                    f"Run '{run_id}' scored non-target seeds: {', '.join(sorted(extras))}",
                    "For targeted regression runs, score only the seeds listed in run-manifest.tsv.",
                )
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a seeded eval suite.")
    parser.add_argument("suite_dir", help="Path to the eval suite root")
    parser.add_argument("--min-runs", type=int, default=0, help="Minimum distinct runs required per seed")
    parser.add_argument(
        "--suite-kind",
        choices=sorted(SUITE_KINDS),
        default="benchmark",
        help="Validation mode: full benchmark suite or targeted regression pack",
    )
    parser.add_argument(
        "--require-run-results",
        action="store_true",
        help="Fail when run-results.tsv is missing or empty",
    )
    args = parser.parse_args()

    suite_dir = Path(args.suite_dir).resolve()
    coverage_path = suite_dir / "coverage-matrix.tsv"
    seed_path = suite_dir / "seed-catalog.tsv"
    ledger_path = suite_dir / "seed-ledger.md"
    controls_path = suite_dir / "controls.md"
    manifest_path = suite_dir / "run-manifest.tsv"
    runs_path = suite_dir / "run-results.tsv"

    errors: list[str] = []

    for required_path in (coverage_path, seed_path, ledger_path, controls_path):
        if not required_path.exists():
            errors.append(
                violation(
                    f"Required suite artifact is missing: {required_path}",
                    "Create the missing suite artifact before using this eval as benchmark infrastructure.",
                )
            )

    if errors:
        print("\n\n".join(errors))
        return 1

    try:
        matrix_rows, matrix_fields = load_tsv(coverage_path)
        seed_rows, seed_fields = load_tsv(seed_path)
        manifest_rows, manifest_fields = load_tsv(manifest_path) if manifest_path.exists() else ([], [])
        run_rows, run_fields = load_tsv(runs_path) if runs_path.exists() else ([], [])
    except ValueError as exc:
        print(
            violation(
                str(exc),
                "Fix the TSV header row and rerun the validator.",
            )
        )
        return 1

    errors.extend(require_columns(matrix_fields, MATRIX_COLUMNS, coverage_path))
    errors.extend(require_columns(seed_fields, SEED_COLUMNS, seed_path))
    if manifest_rows or args.require_run_results:
        errors.extend(require_columns(manifest_fields, RUN_MANIFEST_COLUMNS, manifest_path))
    if run_rows or args.require_run_results:
        errors.extend(require_columns(run_fields, RUN_COLUMNS, runs_path))

    cells, matrix_errors = validate_matrix(matrix_rows, coverage_path)
    errors.extend(matrix_errors)
    seed_ids, seed_errors = validate_seed_catalog(seed_rows, seed_path, cells, args.suite_kind)
    errors.extend(seed_errors)
    run_targets, run_scopes, manifest_errors = validate_run_manifest(
        manifest_rows,
        manifest_path,
        seed_ids,
        args.require_run_results,
        args.suite_kind,
    )
    errors.extend(manifest_errors)
    errors.extend(
        validate_run_results(
            run_rows,
            runs_path,
            seed_ids,
            args.min_runs,
            args.require_run_results,
            args.suite_kind,
            run_targets,
            run_scopes,
        )
    )

    if errors:
        print("\n\n".join(errors))
        return 1

    # Compute and emit status label.
    total_seeds = len(seed_rows)
    total_standard = sum(1 for r in seed_rows if r.get("control_type", "standard") == "standard")
    control_types_found = {r.get("control_type") for r in seed_rows}
    has_positive = "positive_control" in control_types_found
    has_negative = "negative_control" in control_types_found
    has_regression = "regression" in control_types_found
    has_all_controls = has_positive and has_negative and has_regression
    difficulties_found = {r.get("difficulty") for r in seed_rows}
    has_all_tiers = {"Easy", "Medium", "Hard"}.issubset(difficulties_found)
    structures_found = {r.get("seed_structure") for r in seed_rows}
    has_advanced = bool(
        structures_found & {"combined", "layered", "distributed", "camouflaged", "interference"}
    )
    nc_count = sum(1 for r in seed_rows if r.get("control_type") == "negative_control")
    required_nc = math.ceil(total_standard * NEGATIVE_CONTROL_RATIO) if total_standard > 0 else 0
    nc_ratio_ok = nc_count >= required_nc

    dim_counts: Counter = Counter()
    for r in seed_rows:
        if r.get("control_type", "standard") != "negative_control":
            dim_counts[r.get("agent_dimension", "unknown")] += 1
    all_dims_bench = all(c >= BENCHMARK_DIMENSION_FLOOR for c in dim_counts.values()) if dim_counts else False

    distinct_runs = len({r["run_id"] for r in run_rows}) if run_rows else 0

    if not coverage_path.exists() or not controls_path.exists():
        label = "exploratory"
    elif total_seeds < 30 or not has_advanced:
        label = "pilot"
    elif (
        total_seeds >= 36
        and has_all_controls
        and has_all_tiers
        and has_advanced
        and distinct_runs >= 3
    ):
        if total_seeds >= 54 and nc_ratio_ok and all_dims_bench:
            label = "stable benchmark"
        else:
            label = "benchmark"
    else:
        label = "pilot"

    print(f"OK: eval suite metadata is valid for {suite_dir}")
    print(f"STATUS LABEL: {label}")

    notes = []
    if label == "benchmark" and not nc_ratio_ok:
        notes.append(f"  - negative-control ratio below 15% ({nc_count} NCs / {total_standard} standard seeds, need {required_nc})")
    if label == "benchmark":
        thin = [d for d, c in dim_counts.items() if c < BENCHMARK_DIMENSION_FLOOR]
        if thin:
            notes.append(f"  - thin dimensions (< {BENCHMARK_DIMENSION_FLOOR} seeds): {', '.join(sorted(thin))}")
    if label == "pilot":
        if total_seeds < 30:
            notes.append(f"  - only {total_seeds} seeds (need 30+ for pilot)")
        if not has_all_controls:
            missing_ct = []
            if not has_positive:
                missing_ct.append("positive_control")
            if not has_negative:
                missing_ct.append("negative_control")
            if not has_regression:
                missing_ct.append("regression")
            notes.append(f"  - missing control types: {', '.join(missing_ct)}")
        if distinct_runs < 3:
            notes.append(f"  - only {distinct_runs} runs (need 3+ for benchmark)")
    if notes:
        print("NOTES:")
        for note in notes:
            print(note)

    return 0


if __name__ == "__main__":
    sys.exit(main())
