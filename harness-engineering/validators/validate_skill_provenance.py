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
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
LOCK_PATH = ROOT / "skills" / "skills-lock.json"

# The lock lives under skills/. Any other copy is a stale shadow — one was found
# at the repo root holding 13 dead pre-reorganisation paths.
#
# An earlier comment here claimed `skills/impeccable/scripts/pin.mjs` would pick a
# root copy up by accident. That was wrong: `findProjectRoot` only tests existence
# and checks `.git` in the same condition, so at the repo root it changes nothing.
# The reason to forbid a second lock is simpler — two files disagree, and a reader
# or tool cannot tell which is current.
SHADOW_NAME = "skills-lock.json"
CANONICAL_LOCK = Path("skills") / SHADOW_NAME

# Vendored trees are registered here. A tree registered but absent from the lock is
# unpinned, and deleting an entry is the cheapest way to make this validator green —
# so the two are cross-checked rather than trusting the lock to list itself.
REGISTRY_EXCEPTIONS = ROOT / "framework" / "routing" / "skills-registry-exceptions.md"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    violations: list[str] = []

    if not LOCK_PATH.exists():
        print(f"VIOLATION: Missing {LOCK_PATH.relative_to(ROOT)}")
        return 1

    for shadow in sorted(ROOT.rglob(SHADOW_NAME)):
        rel = shadow.relative_to(ROOT)
        if rel == CANONICAL_LOCK:
            continue
        if any(part in {".git", "node_modules"} for part in rel.parts):
            continue
        violations.append(
            f"VIOLATION: Shadow lock file at {rel}\n"
            f"FIX: Delete it. The only lock file is {CANONICAL_LOCK.as_posix()}; a second copy "
            f"drifts from it and a reader cannot tell which is current."
        )

    try:
        lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"VIOLATION: skills/skills-lock.json is not valid JSON: {exc}")
        return 1

    if not isinstance(lock, dict):
        print("VIOLATION: skills/skills-lock.json is not a JSON object.\nFIX: Restore the "
              "`{\"version\": ..., \"skills\": {...}}` shape.")
        return 1

    entries = lock.get("skills", {})
    if not isinstance(entries, dict):
        print("VIOLATION: skills/skills-lock.json `skills` is not an object.\nFIX: Each key is "
              "a skill name mapping to an object with `skillPath` and `computedHash`.")
        return 1

    for name, entry in sorted(entries.items()):
        if not isinstance(entry, dict):
            violations.append(
                f"VIOLATION: Lock entry {name!r} is not an object ({type(entry).__name__}).\n"
                f"FIX: Give it `skillPath` and `computedHash` fields."
            )

    # A vendored tree registered as an exception but absent from the lock is
    # unpinned. Without this, deleting an entry is the cheapest way to pass.
    if REGISTRY_EXCEPTIONS.is_file():
        # Anchor to the registered path at the head of each list item. Matching every
        # backticked path in the file also caught cross-references inside other
        # entries' descriptions, which are not registrations. And only vendored trees
        # need a lock — a locally-authored skill has no upstream to drift from.
        registered = set()
        for line in REGISTRY_EXCEPTIONS.read_text(encoding="utf-8").splitlines():
            head = re.match(r"-\s+`(skills/[A-Za-z0-9._-]+)/[^`]*`", line)
            if head and re.search(r"vendor drop|vendored|skills import", line, re.IGNORECASE):
                registered.add(head.group(1))
        locked_trees = {
            "/".join(str(e.get("skillPath", "")).split("/")[:2])
            for e in entries.values()
            if isinstance(e, dict)
        }
        for tree in sorted(registered - locked_trees):
            if (ROOT / tree).is_dir():
                violations.append(
                    f"VIOLATION: {tree} is registered as a vendor import but has no lock entry.\n"
                    f"FIX: Add it to {CANONICAL_LOCK.as_posix()}, or drop its entry from "
                    f"{REGISTRY_EXCEPTIONS.relative_to(ROOT)} if it is no longer vendored. "
                    f"An unlocked vendored tree can be edited in place with nothing noticing."
                )

    if not entries:
        violations.append(
            "VIOLATION: skills/skills-lock.json records no skills.\n"
            "FIX: Restore the entries, or delete the file rather than keeping an empty lock."
        )

    for name, entry in sorted(entries.items()):
        if not isinstance(entry, dict):
            continue  # already reported above; .get() would crash before printing it
        skill_path = entry.get("skillPath")
        if not skill_path:
            violations.append(
                f"VIOLATION: Lock entry {name!r} has no skillPath.\n"
                f"FIX: Every entry must name the file it pins."
            )
            continue

        # A lock entry names a file inside the repo. An absolute path or a `../`
        # escape would have the validator report on something outside it and then
        # print a PASS line asserting something false about this repository.
        if Path(skill_path).is_absolute() or ".." in Path(skill_path).parts:
            violations.append(
                f"VIOLATION: Lock entry {name!r} has a skillPath outside the repository: {skill_path}\n"
                f"FIX: skillPath must be a repo-relative path with no `..` segments."
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
        elif str(recorded).strip().lower() != actual:
            # Compared case-insensitively on purpose: an uppercase or whitespace-padded
            # but otherwise correct hash used to report "the vendored skill was edited
            # in place — restore it from upstream", which would have someone clobber a
            # clean file chasing a formatting difference.
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
