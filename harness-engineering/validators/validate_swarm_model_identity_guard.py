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
import os
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
            # The fallback-label rule: what to print when identity cannot be proven,
            # and that the label blocks. This is the line that stops a CLI version
            # being substituted at the exact moment substituting one is tempting.
            "say `model unresolved` or `local default, exact model unknown`",
            "that unresolved label is a blocking status and must not be dispatched",
        ],
        # Reworded copies of the same rule. These are NOT the canonical wording, so
        # they are not required at home — they are only ever evidence that someone
        # re-authored the doctrine instead of deferring to it. `routing-guards.md`
        # carried the first two for months without any check noticing.
        "forbidden_paraphrases": [
            "CLI version strings are diagnostics only",
            "must not be presented as model identity",
        ],
        "participants": [
            "framework/slash-commands/consensus.md",
            "framework/slash-commands/cowork.md",
            "framework/operations/routing-guards.md",
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
            # Long enough to be unmistakably a copy. The bare clause "models
            # hallucinate their own identity" is a true general statement that
            # eval and taxonomy docs have every right to make.
            "models hallucinate their own identity. Self-report is not evidence",
            "until every source in this map has been checked",
            # The ladder itself, step by step. Without these the home could be
            # gutted — the ordering replaced wholesale — while the four phrases
            # above still matched. The home is now the only copy, so its contents
            # need more protection than the old design gave them, not less.
            "1. Per-run controls:",
            "2. Project knowledge root evidence:",
            "3. AI Dev Shop repo evidence:",
            "4. Workspace and home CLI config files",
            "5. Candidate ladders:",
            "takes precedence over home config",
        ],
        "forbidden_paraphrases": [
            "until every source in the map has been checked",
            "Model-plan-only lookup order",
        ],
        "participants": [
            "framework/slash-commands/consensus.md",
            "framework/slash-commands/cowork.md",
            "skills/swarm-consensus/references/cli-smoke-test.md",
            # Carried its own 5-step ladder until 2026-07-27, already drifted from
            # canonical in four ways while line 147 called peer-llm-dispatch.md the
            # canonical map. Registered so it cannot quietly grow one again.
            "skills/swarm-consensus/SKILL.md",
        ],
    },
    "Peer Dispatch Brief": {
        "home": "skills/llm-operations/references/peer-llm-dispatch.md",
        "anchor": "## Peer Dispatch Brief",
        "reference_name": "Peer Dispatch Brief",
        # The field list existed in three places with three different field sets:
        # consensus.md alone carried the mandatory file-context line, SKILL.md
        # omitted planned peers, and the reference lacked file context entirely.
        # The union now lives here.
        "exclusive_phrases": [
            "The brief must include:",
            "**Current positions** —",
            "**Reasoning summary** —",
            "**Next ask** —",
            "**Run meaning** —",
            "**File context (mandatory)** —",
        ],
        "forbidden_paraphrases": [
            "The `Peer Dispatch Brief` must include:",
            "file-context line (mandatory)",
            "what replying `run` will execute",
        ],
        "participants": [
            "framework/slash-commands/consensus.md",
            "skills/swarm-consensus/SKILL.md",
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
REQUIRED_SMOKE_TEST_EVIDENCE = [
    "last-known-good.json",
    "peer-dispatch",
    ".gemini",
    ".codex",
    ".claude",
]

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


# Directory names never worth descending into. Pruned during the walk rather than
# filtered afterwards: rglob() over this repo descends into .git and the vendored
# upstream clones under integrations/, which dominated the runtime.
SCAN_PRUNE_DIRS = {
    ".git",
    ".local-artifacts",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "archive",
}

# Under integrations/<name>/, these hold cloned upstream code that is not ours to
# police. Kept identical to IGNORED_INTEGRATION_ARTIFACT_DIRS in
# validate_path_references.py so the two validators agree on what "repo-owned"
# means; if that set changes, change it here too.
IGNORED_INTEGRATION_ARTIFACT_DIRS = frozenset(
    {"upstream", "bin", ".venv", "venv", "node_modules", "dist", "build"}
)


def is_ignored_integration_artifact(rel_dir: str) -> bool:
    parts = rel_dir.split("/")
    return (
        len(parts) == 3
        and parts[0] == "integrations"
        and parts[2] in IGNORED_INTEGRATION_ARTIFACT_DIRS
    )


def scannable_markdown() -> list[str]:
    """Repo-owned markdown, as paths relative to ROOT.

    Skips generated and vendored trees, and tolerates the dangling symlinks this
    repo carries into gitignored artifact directories — a broken link is not a
    doctrine copy, and must not abort the run.

    Note `.claude/commands/` is deliberately in scope: those are installed copies
    of the slash commands, and a doctrine restatement there is exactly as harmful
    as one in the source.
    """
    found = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        rel_dir = Path(dirpath).relative_to(ROOT).as_posix()
        prefix = "" if rel_dir == "." else f"{rel_dir}/"

        dirnames[:] = [
            d
            for d in dirnames
            if d not in SCAN_PRUNE_DIRS
            and not f"{prefix}{d}/".startswith(SCAN_EXCLUDE_PREFIXES)
            and not is_ignored_integration_artifact(f"{prefix}{d}")
        ]

        for filename in filenames:
            # ORIGINAL.md files are pre-import snapshots of vendored skills, kept for
            # diffing against upstream. They are not repo-authored doctrine, and
            # validate_path_references.py skips them for the same reason.
            if not filename.endswith(".md") or filename == "ORIGINAL.md":
                continue
            rel = f"{prefix}{filename}"
            if rel.startswith(SCAN_EXCLUDE_PREFIXES):
                continue
            if not (ROOT / rel).is_file():  # False for broken symlinks
                continue
            found.append(rel)
    return sorted(found)


POINTER_PROXIMITY_LINES = 3


def has_proximate_pointer(text: str, home: str, reference_name: str) -> bool:
    """True when the section name and the home path appear close enough to be one pointer."""
    lines = text.splitlines()
    name_lines = [i for i, line in enumerate(lines) if reference_name in line]
    path_lines = [i for i, line in enumerate(lines) if home in line]
    return any(
        abs(n - p) <= POINTER_PROXIMITY_LINES for n in name_lines for p in path_lines
    )


def read_text_or_none(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def load_corpus() -> dict[str, str]:
    """Read every scannable file once, not once per doctrine."""
    corpus = {}
    for rel in scannable_markdown():
        text = read_text_or_none(ROOT / rel)
        if text is not None:
            corpus[rel] = text
    return corpus


def check_doctrines(violations: list[str]) -> None:
    corpus = load_corpus()

    for name, spec in DOCTRINES.items():
        home_path = ROOT / spec["home"]
        if not home_path.exists():
            violations.append(
                f"VIOLATION: {name} has no home: {spec['home']} is missing.\n"
                f"FIX: Restore the file, or point DOCTRINES['{name}']['home'] at the new canonical location."
            )
            continue

        home_text = read_text_or_none(home_path)
        if home_text is None:
            violations.append(
                f"VIOLATION: {spec['home']} could not be read as UTF-8.\n"
                f"FIX: The {name} home must be readable. A decode error here would otherwise abort "
                f"run-all.sh under `set -euo pipefail` before any later validator runs."
            )
            continue

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

            participant_text = read_text_or_none(participant_path)
            if participant_text is None:
                violations.append(
                    f"VIOLATION: {participant} could not be read as UTF-8.\n"
                    f"FIX: Participants must be readable for the {name} deferral to be checkable."
                )
                continue

            if spec["home"] not in participant_text:
                violations.append(
                    f"VIOLATION: {participant} does not reference the {name} home ({spec['home']}).\n"
                    f"FIX: It must point a reader at the canonical file by path rather than paraphrasing the rule."
                )
            elif spec["reference_name"] not in participant_text:
                violations.append(
                    f"VIOLATION: {participant} does not name the `{spec['reference_name']}` section.\n"
                    f"FIX: A bare file path is not enough — name the section so the reader lands on the rule."
                )
            elif not has_proximate_pointer(
                participant_text, spec["home"], spec["reference_name"]
            ):
                # Both halves present but far apart is not a pointer. In cowork.md the
                # home path appears at :47 and again under an unrelated protocol at
                # :121, so a scattered pair would satisfy the check by coincidence
                # while the line that should defer says something else entirely.
                violations.append(
                    f"VIOLATION: {participant} mentions {spec['home']} and `{spec['reference_name']}`, "
                    f"but never together — so nothing in it actually points at the {name} rule.\n"
                    f"FIX: Put the section name and the file path in one deferral, within "
                    f"{POINTER_PROXIMITY_LINES} lines of each other."
                )

        # 4. Nobody else restates it. This is the check that keeps the rule single-homed.
        #    Verbatim copies alone are not enough to look for: the first version of
        #    this check passed while routing-guards.md carried a reworded copy.
        copies = [(p, "restates") for p in spec["exclusive_phrases"]]
        copies += [(p, "paraphrases") for p in spec.get("forbidden_paraphrases", [])]

        for rel, text in corpus.items():
            if rel == spec["home"]:
                continue
            for phrase, kind in copies:
                if phrase in text:
                    violations.append(
                        f"VIOLATION: {rel} {kind} the {name} rule: {phrase!r}\n"
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

    # Module level only. A nested helper of the same name is not the entry point,
    # and counting occurrences lets us see a shadowing redefinition appended later.
    top_level = [
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    for symbol in REQUIRED_SMOKE_TEST_API:
        count = top_level.count(symbol)
        if count == 0:
            violations.append(
                f"VIOLATION: {SMOKE_TEST_MODULE} no longer defines `{symbol}()` at module level.\n"
                f"FIX: The Model Memory Map depends on this entry point. Restore it, or update "
                f"REQUIRED_SMOKE_TEST_API here and the map's description of the lookup together."
            )
        elif count > 1:
            violations.append(
                f"VIOLATION: {SMOKE_TEST_MODULE} defines `{symbol}()` {count} times at module level.\n"
                f"FIX: The later definition silently shadows the real one, so the lookup can be "
                f"stubbed out while every name the guard checks still appears. Remove the duplicate."
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

    # Every evidence source the Model Memory Map promises the lookup consults. Without
    # these, a source can be deleted from the implementation while the five entry-point
    # names still resolve and the guard still passes — the map would then describe a
    # lookup the code no longer performs.
    joined_literals = "\n".join(literals)
    for source in REQUIRED_SMOKE_TEST_EVIDENCE:
        if source not in joined_literals:
            violations.append(
                f"VIOLATION: {SMOKE_TEST_MODULE} no longer references the evidence source {source!r}.\n"
                f"FIX: The Model Memory Map lists this as a source the lookup checks. Either restore it, "
                f"or change the map and this list together so prose and code still agree."
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
