#!/usr/bin/env python3
"""Validate the model-identity contract: one home per rule, plus a live implementation.

The property protected here is unchanged: when naming LLM participants to a user,
the harness must show model identity and must never pass a CLI version string off
as a model. That matters because peers misreport themselves — agy slots have
claimed "Flash" regardless of what was dispatched — so identity has to come from
evidence, not self-report.

What changed is how it is enforced.

The previous version of this file pinned 42 literal prose strings across 7 files
and required every one of them to be present verbatim. That is the same
drift-generating pattern this harness removes everywhere else: a rule written in
n places drifts in some of them, and the check that polices the copies becomes
one more thing to keep in sync. It did drift. Two markers broke when
`peer-llm-dispatch.md` was rewritten for the agy migration (2026-07-12) and CI
had been failing on them since; a third instance went undetected entirely, where
`cli-smoke-test.md` stated the lookup ladder with 4 steps against the canonical 5.
The guard could not catch that one, because it only pinned the heading.

This version inverts the check. Each rule has exactly one home. Participating
documents must *defer* to that home and must *not* restate it. Rewording a
canonical section is now free; copying it out is what fails.

The eleven markers that grepped `cli_smoke_test.py` for its own function names
are replaced by an AST parse of that module, which is what they were approximating.
"""

from __future__ import annotations

import ast
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]

# One home per rule. `exclusive_phrases` are distinctive sentences that may appear
# ONLY in the home file — they are what a copy-paste of the doctrine looks like.
# `participants` are the files that must defer to the home instead of restating it.
DOCTRINES = {
    "Model Identity Disclosure": {
        "home": "skills/swarm-consensus/SKILL.md",
        "anchor": "## Model Identity Disclosure Guard (Blocking)",
        "reference_name": "Model Identity Disclosure Guard",
        "exclusive_phrases": [
            "always show the peer model identity first",
            "Do not present CLI version strings such as",
            "CLI versions belong only in diagnostics",
            "Preflight copy must distinguish",
        ],
        "participants": [
            "framework/slash-commands/consensus.md",
            "framework/slash-commands/cowork.md",
            "AGENTS.md",
        ],
    },
    "Model Memory Map": {
        "home": "skills/llm-operations/references/peer-llm-dispatch.md",
        "anchor": "### Model Memory Map",
        "reference_name": "Model Memory Map",
        "exclusive_phrases": [
            "Check model sources in this order",
            "Explicitly invalid evidence (never use)",
            "models hallucinate their own identity",
            "until every source in this map has been checked",
        ],
        "participants": [
            "framework/slash-commands/consensus.md",
            "framework/slash-commands/cowork.md",
            "skills/swarm-consensus/references/cli-smoke-test.md",
        ],
    },
}

# Ambiguous phrasings that must not come back, wherever they appear.
FORBIDDEN_MARKERS = {
    "skills/swarm-consensus/SKILL.md": [
        "Asking question to Gemini <version>, Codex <version>, Claude <version>",
    ],
}

# The model-plan lookup is implemented here, not merely described. These are the
# entry points the doctrine depends on; the docs are prose about this contract.
SMOKE_TEST_MODULE = "skills/swarm-consensus/scripts/cli_smoke_test.py"
REQUIRED_SMOKE_TEST_API = [
    "model_memory_roots",
    "load_saved_peer_model_from_memory_map",
    "load_saved_claude_model_from_memory_map",
    "is_exact_model_identifier",
    "resolve_model_plan",
]
REQUIRED_SMOKE_TEST_FLAGS = ["--model-plan-only"]

# Vendored and generated trees are not ours to police for doctrine duplication.
SCAN_EXCLUDE_PREFIXES = (
    ".git/",
    "ADS-memory/",
    "tmp/",
    "skills/impeccable/",
    "skills/taste-skill/",
    "skills/supabase-upstream/",
    "skills/supabase-postgres-best-practices/",
    "skills/improve-codebase-architecture/",
)


def scannable_markdown() -> list[str]:
    """Repo-owned markdown, as paths relative to ROOT.

    Skips generated and vendored trees, and tolerates the dangling symlinks this
    repo carries into gitignored artifact directories — a broken link is not a
    doctrine copy, and must not abort the run.
    """
    found = []
    for path in ROOT.rglob("*.md"):
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith(SCAN_EXCLUDE_PREFIXES):
            continue
        if "/.local-artifacts/" in f"/{rel}":
            continue
        if not path.is_file():  # False for broken symlinks
            continue
        found.append(rel)
    return sorted(found)


def read_text_or_none(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def check_doctrines(violations: list[str]) -> None:
    corpus = scannable_markdown()

    for name, spec in DOCTRINES.items():
        home_path = ROOT / spec["home"]
        if not home_path.exists():
            violations.append(
                f"VIOLATION: {name} has no home: {spec['home']} is missing.\n"
                f"FIX: Restore the file, or point DOCTRINES['{name}']['home'] at the new canonical location."
            )
            continue

        home_text = home_path.read_text(encoding="utf-8")

        # 1. The canonical section still exists and is still findable by its anchor.
        if spec["anchor"] not in home_text:
            violations.append(
                f"VIOLATION: {spec['home']} no longer contains the {name} anchor: {spec['anchor']!r}\n"
                f"FIX: Restore the heading, or update the anchor here if the section was deliberately renamed. "
                f"Every participating file points at this heading by name."
            )

        # 2. Each phrase the doctrine owns actually lives at home.
        for phrase in spec["exclusive_phrases"]:
            if phrase not in home_text:
                violations.append(
                    f"VIOLATION: {spec['home']} no longer states the {name} rule: {phrase!r}\n"
                    f"FIX: The canonical text was reworded or removed. If it was reworded, update "
                    f"`exclusive_phrases` for '{name}' to the new wording — this list exists to stop the rule "
                    f"being copied elsewhere, so it must track its own home."
                )

        # 3. Participants defer, by naming both the home file and the section.
        for participant in spec["participants"]:
            participant_path = ROOT / participant
            if not participant_path.exists():
                violations.append(
                    f"VIOLATION: {name} participant is missing: {participant}\n"
                    f"FIX: Restore it, or drop it from DOCTRINES['{name}']['participants']."
                )
                continue

            participant_text = participant_path.read_text(encoding="utf-8")
            if spec["home"] not in participant_text:
                violations.append(
                    f"VIOLATION: {participant} does not reference the {name} home ({spec['home']}).\n"
                    f"FIX: It must point a reader at the canonical file by path rather than paraphrasing the rule."
                )
            if spec["reference_name"] not in participant_text:
                violations.append(
                    f"VIOLATION: {participant} does not name the `{spec['reference_name']}` section.\n"
                    f"FIX: A bare file path is not enough — name the section so the reader lands on the rule."
                )

        # 4. Nobody else restates it. This is the check that keeps the rule single-homed.
        for rel in corpus:
            if rel == spec["home"]:
                continue
            text = read_text_or_none(ROOT / rel)
            if text is None:
                continue
            for phrase in spec["exclusive_phrases"]:
                if phrase in text:
                    violations.append(
                        f"VIOLATION: {rel} restates the {name} rule: {phrase!r}\n"
                        f"FIX: Delete the copy and defer to `{spec['reference_name']}` in {spec['home']}. "
                        f"A rule written in two places drifts in one of them — that is what this check exists to stop."
                    )


def check_forbidden(violations: list[str]) -> None:
    for relative_path, markers in FORBIDDEN_MARKERS.items():
        path = ROOT / relative_path
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker in text:
                violations.append(
                    f"VIOLATION: {relative_path} still contains forbidden ambiguous model/CLI wording: {marker!r}\n"
                    f"FIX: Replace it with planned model names plus separate CLI diagnostics."
                )


def check_implementation(violations: list[str]) -> None:
    """Assert the model-plan lookup exists as code, not just as prose about code."""
    module_path = ROOT / SMOKE_TEST_MODULE
    if not module_path.exists():
        violations.append(
            f"VIOLATION: Missing model-plan implementation: {SMOKE_TEST_MODULE}\n"
            f"FIX: The Model Memory Map documents this module as its mechanical form. Restore it."
        )
        return

    source = module_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        violations.append(
            f"VIOLATION: {SMOKE_TEST_MODULE} does not parse: {exc}\n"
            f"FIX: The model-plan lookup is unusable until this is valid Python."
        )
        return

    defined = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for symbol in REQUIRED_SMOKE_TEST_API:
        if symbol not in defined:
            violations.append(
                f"VIOLATION: {SMOKE_TEST_MODULE} no longer defines `{symbol}()`.\n"
                f"FIX: The Model Memory Map depends on this entry point. Restore it, or update "
                f"REQUIRED_SMOKE_TEST_API here and the map's description of the lookup together."
            )

    literals = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    for flag in REQUIRED_SMOKE_TEST_FLAGS:
        if flag not in literals:
            violations.append(
                f"VIOLATION: {SMOKE_TEST_MODULE} no longer registers the `{flag}` flag.\n"
                f"FIX: The docs instruct agents to invoke this flag by name; it is a published interface."
            )


def main() -> int:
    violations: list[str] = []
    check_doctrines(violations)
    check_forbidden(violations)
    check_implementation(violations)

    if violations:
        print("\n\n".join(violations))
        return 1

    print("Swarm model identity guard validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
