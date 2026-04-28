#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECT_KNOWLEDGE_TEMPLATE = ROOT / "project-knowledge-template"
SCAN_TARGETS = [
    ROOT / "AGENTS.md",
    ROOT / "CLAUDE.md",
    ROOT / "GEMINI.md",
    ROOT / "README.md",
    ROOT / ".claude/commands",
    ROOT / "agents",
    ROOT / "skills",
    ROOT / "framework",
    ROOT / "project-knowledge-template/README.md",
    ROOT / "project-knowledge-template/governance",
    ROOT / "project-knowledge-template/memory",
    ROOT / "project-knowledge-template/meta",
    ROOT / "harness-engineering",
]

AI_DEV_SHOP_ROOT_RE = re.compile(r"<AI_DEV_SHOP_ROOT>/([A-Za-z0-9_./-]+)")
ADS_PROJECT_KNOWLEDGE_ROOT_RE = re.compile(r"<ADS_PROJECT_KNOWLEDGE_ROOT>/([A-Za-z0-9_./-]+)")
BACKTICK_PATH_RE = re.compile(
    r"`((?:AGENTS|CLAUDE|GEMINI|README|todo)\.md|(?:\.claude/commands|agents|skills|framework|project-knowledge-template|harness-engineering)/[A-Za-z0-9_./-]+(?:\.[A-Za-z0-9_-]+)?)`"
)
MARKDOWN_LINK_RE = re.compile(
    r"\]\(((?:AGENTS|CLAUDE|GEMINI|README|todo)\.md|(?:\.claude/commands|agents|skills|framework|project-knowledge-template|harness-engineering)/[^)#\s]+)"
)


@dataclass(frozen=True)
class Violation:
    file_path: Path
    line_number: int
    reference: str


def should_skip(path_text: str) -> bool:
    if path_text.endswith("-"):
        return True
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


def check_repo_reference(path_text: str) -> bool:
    if should_skip(path_text):
        return True
    if path_text.startswith("specs/"):
        return True
    if path_text.startswith("project-knowledge-template/reports/"):
        base_name = Path(path_text).name
        stem = Path(path_text).stem
        if not path_text.endswith(".md"):
            return True
        if any(ch.isupper() for ch in stem) and "-" in stem:
            return True
    return (ROOT / path_text).exists()


def check_workspace_reference(path_text: str) -> bool:
    if path_text.startswith(".local-artifacts/"):
        return True
    return check_repo_reference(str(Path("project-knowledge-template") / path_text))


def find_violations() -> list[Violation]:
    violations: list[Violation] = []
    seen: set[tuple[Path, int, str]] = set()

    for file_path in repo_files():
        for line_number, line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), start=1):
            repo_candidates: set[str] = set()
            workspace_candidates: set[str] = set()
            for match in AI_DEV_SHOP_ROOT_RE.finditer(line):
                repo_candidates.add(match.group(1))
            for match in ADS_PROJECT_KNOWLEDGE_ROOT_RE.finditer(line):
                workspace_candidates.add(match.group(1))
            for match in BACKTICK_PATH_RE.finditer(line):
                repo_candidates.add(match.group(1))
            for match in MARKDOWN_LINK_RE.finditer(line):
                repo_candidates.add(match.group(1))

            for candidate in sorted(repo_candidates):
                if check_repo_reference(candidate):
                    continue
                key = (file_path, line_number, candidate)
                if key in seen:
                    continue
                seen.add(key)
                violations.append(Violation(file_path, line_number, candidate))

            for candidate in sorted(workspace_candidates):
                reference = f"<ADS_PROJECT_KNOWLEDGE_ROOT>/{candidate}"
                if check_workspace_reference(candidate):
                    continue
                key = (file_path, line_number, reference)
                if key in seen:
                    continue
                seen.add(key)
                violations.append(Violation(file_path, line_number, reference))

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
