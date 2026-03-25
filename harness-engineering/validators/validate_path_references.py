#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCAN_TARGETS = [
    ROOT / "AGENTS.md",
    ROOT / "CLAUDE.md",
    ROOT / "GEMINI.md",
    ROOT / "README.md",
    ROOT / ".claude/commands",
    ROOT / "agents",
    ROOT / "skills",
    ROOT / "project-knowledge/governance",
    ROOT / "project-knowledge/operations",
    ROOT / "project-knowledge/quality",
    ROOT / "project-knowledge/routing",
    ROOT / "templates",
    ROOT / "workflows",
    ROOT / "harness-engineering",
]

AI_DEV_SHOP_ROOT_RE = re.compile(r"<AI_DEV_SHOP_ROOT>/([A-Za-z0-9_./-]+)")
BACKTICK_PATH_RE = re.compile(
    r"`((?:AGENTS|CLAUDE|GEMINI|README|todo)\.md|(?:agents|skills|project-knowledge|workflows|templates|slash-commands|reports|harness-engineering)/[A-Za-z0-9_./-]+(?:\.[A-Za-z0-9_-]+)?)`"
)
MARKDOWN_LINK_RE = re.compile(
    r"\]\(((?:AGENTS|CLAUDE|GEMINI|README|todo)\.md|(?:agents|skills|project-knowledge|workflows|templates|slash-commands|reports|harness-engineering)/[^)#\s]+)"
)


@dataclass(frozen=True)
class Violation:
    file_path: Path
    line_number: int
    reference: str


def should_skip(path_text: str) -> bool:
    return any(token in path_text for token in ("<", ">", "*", "...", "$", "{", "}"))


def repo_files() -> list[Path]:
    files: list[Path] = []
    for target in SCAN_TARGETS:
        if target.is_file():
            files.append(target)
            continue
        for path in target.rglob("*.md"):
            if path.name == "ORIGINAL.md":
                continue
            if "archive" in path.parts:
                continue
            files.append(path)
    return sorted(files)


def check_reference(path_text: str) -> bool:
    if should_skip(path_text):
        return True
    if path_text.startswith("specs/"):
        return True
    if path_text.startswith("framework/reports/"):
        base_name = Path(path_text).name
        stem = Path(path_text).stem
        if not path_text.endswith(".md"):
            return True
        if any(ch.isupper() for ch in stem) and "-" in stem:
            return True
    return (ROOT / path_text).exists()


def find_violations() -> list[Violation]:
    violations: list[Violation] = []
    seen: set[tuple[Path, int, str]] = set()

    for file_path in repo_files():
        for line_number, line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), start=1):
            candidates: set[str] = set()
            for match in AI_DEV_SHOP_ROOT_RE.finditer(line):
                candidates.add(match.group(1))
            for match in BACKTICK_PATH_RE.finditer(line):
                candidates.add(match.group(1))
            for match in MARKDOWN_LINK_RE.finditer(line):
                candidates.add(match.group(1))

            for candidate in sorted(candidates):
                if check_reference(candidate):
                    continue
                key = (file_path, line_number, candidate)
                if key in seen:
                    continue
                seen.add(key)
                violations.append(Violation(file_path, line_number, candidate))

    return violations


def main() -> int:
    violations = find_violations()

    if not violations:
        print("PASS: repo-local markdown path references resolved cleanly.")
        return 0

    for violation in violations:
        rel_path = violation.file_path.relative_to(ROOT)
        print(
            f"VIOLATION: missing repo path reference in {rel_path}:{violation.line_number} -> {violation.reference}"
        )
        print("FIX: update the reference to a real path or add the missing file/directory.")

    print(f"FAIL: {len(violations)} missing repo path reference(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
