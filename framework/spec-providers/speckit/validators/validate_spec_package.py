#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ALWAYS_REQUIRED = [
    "feature.spec.md",
    "traceability.spec.md",
    "spec-manifest.md",
    "spec-dod.md",
]

OPTIONAL = [
    "api.spec.md",
    "state.spec.md",
    "orchestrator.spec.md",
    "ui.spec.md",
    "errors.spec.md",
    "behavior.spec.md",
]

ALL_LOGICAL_FILES = ALWAYS_REQUIRED[:1] + OPTIONAL + ALWAYS_REQUIRED[1:]

PLACEHOLDER_MARKERS = [
    "SPEC-<NNN>",
    "FEAT-<NNN>-<short-feature-name>",
    "<feature-name>",
    "<short-feature-name>",
    "<semver",
    "<ISO-8601",
    "<one-line purpose>",
    "<one sentence>",
    "<notes>",
    "<precondition>",
    "<action>",
    "<observable outcome>",
    "<actual filename>",
    "<actual feature spec>",
    "<path or symbol>",
]


def find_by_suffix(root: Path, suffix: str) -> list[Path]:
    return sorted(
        p
        for p in root.glob("*.md")
        if p.is_file() and p.name.endswith(suffix)
    )


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_table_value(text: str, key: str) -> str | None:
    pattern = re.compile(rf"^\|\s*{re.escape(key)}\s*\|\s*(.*?)\s*\|$", re.MULTILINE)
    match = pattern.search(text)
    return match.group(1).strip() if match else None


def find_manifest_row_status(manifest_text: str, logical_name: str) -> str | None:
    pattern = re.compile(
        rf"^\|\s*`{re.escape(logical_name)}`\s*\|\s*([A-Z]+)\s*\|",
        re.MULTILINE,
    )
    match = pattern.search(manifest_text)
    return match.group(1).strip() if match else None


def parse_dod_statuses(text: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for line in text.splitlines():
        if not re.match(r"^\|\s*[A-H]-\d+\s*\|", line):
            continue
        parts = [part.strip() for part in line.split("|")[1:-1]]
        if len(parts) < 3:
            continue
        rows.append((parts[0], parts[2]))
    return rows


def collect_feature_ids(feature_text: str, pattern: str) -> list[str]:
    return re.findall(pattern, feature_text, flags=re.MULTILINE)


def validate(spec_root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not spec_root.exists():
        return [f"Spec folder does not exist: {spec_root}"], warnings
    if not spec_root.is_dir():
        return [f"Spec path is not a directory: {spec_root}"], warnings

    discovered: dict[str, list[Path]] = {
        logical: find_by_suffix(spec_root, logical) for logical in ALL_LOGICAL_FILES
    }

    for logical in ALWAYS_REQUIRED:
        matches = discovered[logical]
        if not matches:
            errors.append(f"Missing required file matching '*{logical}'")
        elif len(matches) > 1:
            errors.append(
                f"Expected exactly one file matching '*{logical}', found {len(matches)}: "
                + ", ".join(str(p.name) for p in matches)
            )

    for logical in OPTIONAL:
        matches = discovered[logical]
        if len(matches) > 1:
            errors.append(
                f"Expected at most one file matching '*{logical}', found {len(matches)}: "
                + ", ".join(str(p.name) for p in matches)
            )

    manifest_matches = discovered["spec-manifest.md"]
    if manifest_matches:
        manifest_text = read_text(manifest_matches[0])
        for logical in ALL_LOGICAL_FILES:
            status = find_manifest_row_status(manifest_text, logical)
            if status is None:
                errors.append(f"spec-manifest.md is missing applicability row for `{logical}`")
                continue
            actual_exists = bool(discovered[logical])
            if logical in ALWAYS_REQUIRED:
                if status != "PRESENT":
                    errors.append(f"`{logical}` must be marked PRESENT in spec-manifest.md")
                if not actual_exists:
                    errors.append(f"`{logical}` is marked in manifest but file is missing on disk")
            else:
                if actual_exists and status != "PRESENT":
                    errors.append(f"`{logical}` exists on disk but is not marked PRESENT in spec-manifest.md")
                if not actual_exists and status != "OMITTED":
                    errors.append(f"`{logical}` is absent on disk and must be marked OMITTED in spec-manifest.md")
    else:
        manifest_text = ""

    for md_file in sorted(spec_root.glob("*.md")):
        text = read_text(md_file)
        if "[NEEDS CLARIFICATION:" in text:
            errors.append(f"Unresolved clarification marker in {md_file.name}")
        for marker in PLACEHOLDER_MARKERS:
            if marker in text:
                errors.append(f"Template placeholder `{marker}` still present in {md_file.name}")

    feature_matches = discovered["feature.spec.md"]
    if feature_matches:
        feature_text = read_text(feature_matches[0])
        status = extract_table_value(feature_text, "status")
        if status != "APPROVED":
            errors.append(f"{feature_matches[0].name}: status must be APPROVED, found {status or 'missing'}")

        spec_id = extract_table_value(feature_text, "spec_id")
        if not spec_id or not re.fullmatch(r"SPEC-\d{3,}", spec_id):
            errors.append(f"{feature_matches[0].name}: invalid or missing spec_id")

        version = extract_table_value(feature_text, "version")
        if not version or not re.fullmatch(r"\d+\.\d+\.\d+", version):
            errors.append(f"{feature_matches[0].name}: invalid or missing semver version")

        feature_name = extract_table_value(feature_text, "feature_name")
        if not feature_name or not re.fullmatch(r"FEAT-\d{3}-[a-z0-9-]+", feature_name):
            errors.append(f"{feature_matches[0].name}: invalid or missing feature_name")

        content_hash = extract_table_value(feature_text, "content_hash")
        if not content_hash or not re.fullmatch(r"sha256:[0-9a-f]{64}", content_hash):
            errors.append(f"{feature_matches[0].name}: invalid or missing content_hash")

        owner = extract_table_value(feature_text, "owner")
        if not owner or owner in {"TBD", "<human name or team>"}:
            errors.append(f"{feature_matches[0].name}: owner must be set to a named human or team")

        req_ids = collect_feature_ids(feature_text, r"^- (REQ-\d+):",)
        ac_ids = collect_feature_ids(feature_text, r"^- (AC-\d+)\s+\(REQ-\d+\)")
        inv_ids = collect_feature_ids(feature_text, r"^- (INV-\d+):")
        ec_ids = collect_feature_ids(feature_text, r"^- (EC-\d+):")

        traceability_matches = discovered["traceability.spec.md"]
        if traceability_matches:
            traceability_text = read_text(traceability_matches[0])
            for req_id in req_ids:
                if req_id not in traceability_text:
                    errors.append(f"{traceability_matches[0].name}: missing {req_id} from traceability matrix")
            for ac_id in ac_ids:
                if ac_id not in traceability_text:
                    errors.append(f"{traceability_matches[0].name}: missing {ac_id} from traceability matrix")
            for inv_id in inv_ids:
                if inv_id not in traceability_text:
                    errors.append(f"{traceability_matches[0].name}: missing {inv_id} from invariant traceability")
            for ec_id in ec_ids:
                if ec_id not in traceability_text:
                    errors.append(f"{traceability_matches[0].name}: missing {ec_id} from edge-case traceability")

    dod_matches = discovered["spec-dod.md"]
    if dod_matches:
        dod_text = read_text(dod_matches[0])
        dod_rows = parse_dod_statuses(dod_text)
        if not dod_rows:
            errors.append(f"{dod_matches[0].name}: no checklist rows found")
        for item_id, status in dod_rows:
            if status not in {"PASS", "NA"}:
                errors.append(f"{dod_matches[0].name}: {item_id} must be PASS or NA, found {status or 'blank'}")
        if "Overall DoD Result:** PASS" not in dod_text and "Overall DoD Result: PASS" not in dod_text:
            errors.append(f"{dod_matches[0].name}: overall result must be PASS")

    extra_md = [
        p.name
        for p in sorted(spec_root.glob("*.md"))
        if not any(p.name.endswith(logical) for logical in ALL_LOGICAL_FILES)
    ]
    if extra_md:
        warnings.append(
            "Additional markdown files found in spec package root: " + ", ".join(extra_md)
        )

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a strict Speckit compatibility spec package."
    )
    parser.add_argument("spec_dir", help="Path to the spec package directory")
    args = parser.parse_args()

    spec_root = Path(args.spec_dir).expanduser().resolve()
    errors, warnings = validate(spec_root)

    print("Speckit Spec Package Validator")
    print("------------------------------")
    print(f"Spec root: {spec_root}")

    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")

    if errors:
        print("VIOLATION:")
        for error in errors:
            print(f"  - {error}")
        print("FIX:")
        print("  Repair the spec package, rerun this validator, and do not hand off to `/plan` until it exits cleanly.")
        return 1

    print("PASS: strict Speckit package passed mechanical validation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
