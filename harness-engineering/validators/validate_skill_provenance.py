#!/usr/bin/env python3
"""Verify that skills-lock.json actually locks the vendored skills it names.

Before this existed, nothing in the repo read `computedHash`. The file recorded
provenance for third-party skill drops and no check ever confirmed a single
entry — so "provenance locked" was documentation, not a property.

It was also wrong. Two entries (`supabase`, `supabase-postgres-best-practices`)
carried hashes that matched no file in the repository at all: not the SKILL.md
they named, not any of the other 83,000 files, and not the same bytes under any
other common digest. They had been wrong since the commit that introduced them
(`a1721d2`), and neither SKILL.md had changed since, so this was never drift —
the values were simply never hashes of the content they claimed to pin.

The lock format is hand-maintained; the vendor READMEs tell a human to "update
the hash if it changed". This makes that instruction checkable.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
LOCK_PATH = ROOT / "skills" / "skills-lock.json"

# The lock lives under skills/. A copy at the repo root is a stale shadow: it has
# been seen holding pre-reorganisation paths, and `skills/impeccable/scripts/pin.mjs`
# treats a `skills-lock.json` as a project-root marker, so a second one is a file
# that can be read instead of the real one.
SHADOW_PATHS = [ROOT / "skills-lock.json"]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    violations: list[str] = []

    if not LOCK_PATH.exists():
        print(f"VIOLATION: Missing {LOCK_PATH.relative_to(ROOT)}")
        return 1

    for shadow in SHADOW_PATHS:
        if shadow.exists():
            violations.append(
                f"VIOLATION: Shadow lock file at {shadow.relative_to(ROOT)}\n"
                f"FIX: Delete it. The only lock file is skills/skills-lock.json; a second copy "
                f"drifts from it and can be picked up in its place."
            )

    try:
        lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"VIOLATION: skills/skills-lock.json is not valid JSON: {exc}")
        return 1

    entries = lock.get("skills", {})
    if not entries:
        violations.append(
            "VIOLATION: skills/skills-lock.json records no skills.\n"
            "FIX: Restore the entries, or delete the file rather than keeping an empty lock."
        )

    for name, entry in sorted(entries.items()):
        skill_path = entry.get("skillPath")
        if not skill_path:
            violations.append(
                f"VIOLATION: Lock entry {name!r} has no skillPath.\n"
                f"FIX: Every entry must name the file it pins."
            )
            continue

        target = ROOT / skill_path
        if not target.is_file():
            violations.append(
                f"VIOLATION: Lock entry {name!r} points at a missing file: {skill_path}\n"
                f"FIX: Restore the file, correct skillPath, or drop the entry if the skill was removed."
            )
            continue

        recorded = entry.get("computedHash")
        actual = digest(target)
        if not recorded:
            violations.append(
                f"VIOLATION: Lock entry {name!r} has no computedHash.\n"
                f"FIX: Set it to the sha256 of {skill_path}: {actual}"
            )
        elif recorded != actual:
            violations.append(
                f"VIOLATION: {skill_path} does not match its locked hash.\n"
                f"  recorded: {recorded}\n"
                f"  actual:   {actual}\n"
                f"FIX: If the change was intended, update computedHash for {name!r} to the actual value "
                f"and note the re-import. If it was not, the vendored skill was edited in place — "
                f"restore it from upstream."
            )

    if violations:
        print("\n\n".join(violations))
        return 1

    print(f"PASS: skill provenance verified ({len(entries)} locked skill(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
