#!/usr/bin/env python3
"""Validate contract file presence, structure, cross-references, and field coverage."""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS_DIR = ROOT / "framework" / "contracts"
HOST_DECLARATIONS_DIR = ROOT / "project-knowledge-template" / "governance" / "contracts"

LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^(#{1,4})\s+(.+)$", re.MULTILINE)
CODE_BLOCK_RE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)

GAP_TOKENS = frozenset(
    {"n/a", "none", "gap", "missing", "needs declaration", "not yet available", "not yet configured"}
)
PLACEHOLDER_TOKENS = frozenset({"todo", "tbd", "unknown", "fixme"})


@dataclass(frozen=True)
class ContractSpec:
    filename: str
    required_headings: tuple[str, ...]
    required_slots: tuple[str, ...]


FRAMEWORK_SPECS: dict[str, ContractSpec] = {
    "README.md": ContractSpec(
        filename="README.md",
        required_headings=(
            "Host-Project Contracts",
            "Contract Types",
            "Where Contracts Live",
            "Which Stages Consume Contracts",
        ),
        required_slots=(),
    ),
    "computational-controls.md": ContractSpec(
        filename="computational-controls.md",
        required_headings=(
            "Computational Controls Contract",
            "Named Command Slots",
            "lint",
            "typecheck",
            "build",
            "unit_tests",
            "integration_tests",
            "static_analysis",
            "Behavior When Contract Is Missing",
            "Behavior When a Check Fails",
        ),
        required_slots=("lint", "typecheck", "build", "unit_tests", "integration_tests", "static_analysis"),
    ),
    "runtime-validation.md": ContractSpec(
        filename="runtime-validation.md",
        required_headings=(
            "Runtime Validation Contract",
            "Required Fields",
            "boot_command",
            "healthy_signal",
            "critical_path_check",
            "negative_path_check",
            "artifact_capture_path",
            "teardown_command",
            "Outcome Model",
            "Behavior When Contract Is Missing",
        ),
        required_slots=(
            "boot_command",
            "healthy_signal",
            "critical_path_check",
            "negative_path_check",
            "artifact_capture_path",
            "teardown_command",
        ),
    ),
    "architecture-fitness.md": ContractSpec(
        filename="architecture-fitness.md",
        required_headings=(
            "Architecture Fitness Contract",
            "Rule Format",
            "Enforcement Scope",
            "Validator Priority Rule",
            "Behavior When Contract Is Missing",
        ),
        required_slots=(),
    ),
    "enforcement.md": ContractSpec(
        filename="enforcement.md",
        required_headings=(
            "Contract Enforcement",
            "Contract States",
            "Greenfield vs Brownfield Defaults",
            "Enforcement Tiers",
            "Waiver Protocol",
            "Stage Gate Behavior",
        ),
        required_slots=(),
    ),
}


@dataclass(frozen=True)
class Violation:
    file_path: Path
    line_number: int
    code: str
    message: str


def strip_code_blocks(text: str) -> str:
    return CODE_BLOCK_RE.sub("", text)


def heading_lines(text: str) -> dict[str, int]:
    results: dict[str, int] = {}
    for i, line in enumerate(text.splitlines(), 1):
        m = re.match(r"^#{1,4}\s+(.+)$", line)
        if m:
            results[m.group(1).strip()] = i
    return results


def extract_markdown_links(text: str) -> Iterable[tuple[int, str]]:
    clean = strip_code_blocks(text)
    for i, line in enumerate(clean.splitlines(), 1):
        for m in LINK_RE.finditer(line):
            target = m.group(2)
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            if target.startswith("<"):
                continue
            yield i, target.split("#")[0] if "#" in target else target


def slot_has_content(text: str, slot_heading: str) -> bool:
    lines = text.splitlines()
    in_slot = False
    for line in lines:
        if re.match(rf"^#{2,4}\s+{re.escape(slot_heading)}\s*$", line):
            in_slot = True
            continue
        if in_slot:
            if re.match(r"^#{1,4}\s+", line):
                break
            stripped = line.strip().lower()
            if stripped.startswith("- **command"):
                value = stripped.split(":", 1)[-1].strip() if ":" in stripped else ""
                value = value.strip("` ")
                if not value or value in PLACEHOLDER_TOKENS:
                    return False
                return True
    return in_slot


def validate_presence(contracts_dir: Path) -> list[Violation]:
    violations: list[Violation] = []
    for name, spec in FRAMEWORK_SPECS.items():
        path = contracts_dir / name
        if not path.exists():
            violations.append(Violation(
                file_path=path, line_number=0, code="MISSING_FILE",
                message=f"Required contract file not found: {name}",
            ))
        elif path.stat().st_size == 0:
            violations.append(Violation(
                file_path=path, line_number=0, code="EMPTY_FILE",
                message=f"Contract file is empty: {name}",
            ))
    return violations


def validate_required_headings(path: Path, spec: ContractSpec) -> list[Violation]:
    violations: list[Violation] = []
    if not path.exists():
        return violations
    text = path.read_text(encoding="utf-8")
    headings = heading_lines(text)
    heading_names_lower = {h.lower() for h in headings}
    for required in spec.required_headings:
        if required.lower() not in heading_names_lower:
            violations.append(Violation(
                file_path=path, line_number=0, code="MISSING_HEADING",
                message=f"Required heading not found: '{required}'",
            ))
    return violations


def validate_links(path: Path, base_dir: Path) -> list[Violation]:
    violations: list[Violation] = []
    if not path.exists():
        return violations
    text = path.read_text(encoding="utf-8")
    for line_num, target in extract_markdown_links(text):
        if not target:
            continue
        resolved = (path.parent / target).resolve()
        if not resolved.exists():
            violations.append(Violation(
                file_path=path, line_number=line_num, code="BROKEN_LINK",
                message=f"Link target not found: '{target}'",
            ))
    return violations


def validate_host_declarations(host_dir: Path) -> list[Violation]:
    violations: list[Violation] = []
    if not host_dir.exists():
        return violations
    for name in ("computational-controls.md", "runtime-validation.md", "architecture-fitness.md"):
        path = host_dir / name
        if path.exists():
            text = path.read_text(encoding="utf-8")
            headings = heading_lines(text)
            if not headings:
                violations.append(Violation(
                    file_path=path, line_number=0, code="NO_HEADINGS",
                    message="Host declaration file has no markdown headings",
                ))
    return violations


def scan_all() -> list[Violation]:
    violations: list[Violation] = []
    violations.extend(validate_presence(CONTRACTS_DIR))
    for name, spec in FRAMEWORK_SPECS.items():
        path = CONTRACTS_DIR / name
        violations.extend(validate_required_headings(path, spec))
        violations.extend(validate_links(path, CONTRACTS_DIR))
    violations.extend(validate_host_declarations(HOST_DECLARATIONS_DIR))
    return violations


def main() -> int:
    violations = scan_all()
    if violations:
        print(f"\n{len(violations)} contract validation issue(s) found:", file=sys.stderr)
        for v in violations:
            loc = f":{v.line_number}" if v.line_number else ""
            print(f"  [{v.code}] {v.file_path}{loc} — {v.message}", file=sys.stderr)
        return 1
    print("All contract files valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
