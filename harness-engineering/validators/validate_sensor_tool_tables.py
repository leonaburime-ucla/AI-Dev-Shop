#!/usr/bin/env python3
"""Keep per-stack tool recommendations out of the harness docs.

A sensor declares a **capability** — what a command must emit, and that the
sensor is `inactive` when nothing can. It does not recommend a tool per language
with a reference command, because those claims cannot be checked from this
repository and have been wrong every time anyone checked them upstream: a PyPI
package that does not exist, a wrong clippy default, a linter blind to `with`, a
non-existent `revive` flag, a formatter emitting no symbol name.

## Why this is the second version

The first matched a hardcoded list of language names at the start of a markdown
table row. An adversarial review defeated it 18 times out of 18 with nothing more
than a backtick, a bold marker, a swapped column, an HTML table, a bullet list, or
any language outside the list — Elixir, Dart, Zig, "Backend (Python)". Its `C#`
entry could never match at all, because `\\b` between `#` and `|` is not a word
boundary. It scanned only `harness-engineering/sensors/`, while the deleted
tables were sitting verbatim in `framework/contracts/computational-controls.md`,
which is the file hosts actually copy from.

So this version does not look for languages. It looks for the thing that is
actually dangerous: **an executable command, presented as guidance, in a doc that
is meant to declare capabilities.** That is language-agnostic, survives
reformatting, and covers the contract templates.

## What is allowed

- Naming a tool to **warn against** it ("it is not valid to declare X alone").
  Warnings are protective; recommendations are the defect. Detected by negation
  vocabulary on the same line.
- File and report **formats** (lcov, Cobertura, JaCoCo). Verifiable specs, and
  the sensors depend on their field names.
- Commands this repository actually ships and can execute — its own scripts and
  validators.
- An explicit inline waiver: `<!-- tool-command-ok: reason -->` on the line
  before. The reason is required, so a waiver is a decision someone recorded.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]

# Docs whose job is to declare capabilities, not to recommend tooling.
SCAN_DIRS = [
    Path("harness-engineering/sensors"),
    Path("harness-engineering/quality"),
    Path("framework/contracts"),
]

# Matching by tool name needs a list, and a list is always one tool short — the
# first version missed Elixir, Dart and "Backend (Python)" because they were not
# in it. So match on **shape** instead: a backticked argv, meaning an
# executable-looking first token followed by arguments.
BACKTICKED = re.compile(r"`([^`\n]+)`|<code>([^<\n]+)</code>")
EXECUTABLE = re.compile(r"^[a-z][a-z0-9._-]*$")
ARGUMENT_EVIDENCE = re.compile(r"(^|\s)(--?[a-zA-Z]|[^\s]*/|[^\s]+=)")

# Runners whose bare subcommand form carries no flag or path (`npm audit`).
RUNNERS = {
    "npx", "npm", "pnpm", "yarn", "bun", "bunx", "deno", "node",
    "pip", "pip3", "pipx", "poetry", "uv", "python", "python3",
    "go", "cargo", "mvn", "gradle", "dotnet", "gem", "bundle", "composer",
    "mix", "swift", "stack", "cabal", "rebar3", "make", "bash", "sh",
}


# Code and expressions also live in backticks. `head == base`, `counter type="X"`
# and `a && b` are not invocations, and an `=` alone does not make one.
EXPRESSION = re.compile(r"(==|!=|>=|<=|&&|\|\||=\"|=>|\bor\b|\band\b)")


def looks_like_command(text: str) -> bool:
    """True for an argv, false for prose, an expression, or a filename."""
    tokens = text.split()
    if len(tokens) < 2:
        return False  # a bare name is not a reference command
    if EXPRESSION.search(text):
        return False
    head = tokens[0]
    if not EXECUTABLE.match(head):
        return False
    if head in RUNNERS:
        return True
    return bool(ARGUMENT_EVIDENCE.search(" ".join(tokens[1:])))

# A line that warns against something is not recommending it.
NEGATION = re.compile(
    r"\b(not valid|never|do not|don'?t|must not|cannot|can not|no longer|"
    r"invalid|forbidden|deprecated|does not|doesn'?t|fails?\b|wrong|"
    r"defect|trap|instead of|rather than|no branch mode|has no|have no|"
    r"is blind|no such|unavailable|does nothing)\b",
    re.IGNORECASE,
)

WAIVER = re.compile(r"<!--\s*tool-command-ok:\s*\S+.*-->")

# Commands this repo ships and can run. Naming them is not an unverifiable claim.
OWN_COMMAND = re.compile(
    r"`[^`]*(harness-engineering/|framework/|skills/|scripts/|run-all\.sh)[^`]*`"
)

# `git` is the one tool the toolkit may name outright: it is present wherever this
# repo is, its behaviour is checkable here, and change-history.md is deliberately
# built on `git log` with no command slot at all.
GIT_COMMAND = re.compile(r"`\s*git\s")

# A contract template showing the *shape* of a declaration is not recommending the
# tool in it. The marker has to be explicit — "e.g." — not inferred.
ILLUSTRATIVE = re.compile(r"(\be\.g\.|\bfor example|\bfor instance|\bsuch as\b)", re.IGNORECASE)

# An "e.g." does not launder a recommendation. `computational-controls.md` slipped
# a full per-stack table past the first version of this check by opening with
# "e.g." and then saying "recommended for JS/TS" — which is exactly the claim that
# cannot be verified from here.
RECOMMENDATION = re.compile(
    r"\b(recommended|recommend|preferred|prefer|default choice|best option|"
    r"the standard|use\s+`)\b",
    re.IGNORECASE,
)


def scannable() -> list[Path]:
    files: list[Path] = []
    for rel in SCAN_DIRS:
        base = ROOT / rel
        if base.is_dir():
            files.extend(sorted(p for p in base.rglob("*.md") if p.is_file()))
    return files


def main() -> int:
    violations: list[str] = []

    for path in scannable():
        rel = path.relative_to(ROOT).as_posix()
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            violations.append(f"VIOLATION: {rel} could not be read as UTF-8.")
            continue

        for number, line in enumerate(lines, start=1):
            # `findall` yields a tuple per alternation branch; an HTML <code> block
            # is a reference command exactly as much as a backticked one is.
            candidates = [g for groups in BACKTICKED.findall(line) for g in groups if g]
            commands = [c for c in candidates if looks_like_command(c)]
            if not commands:
                continue
            # The negation has to be about *this* command. A first attempt scanned
            # whole neighbouring lines and let "both reported, never gated" — an
            # unrelated clause — exempt a tool recommendation on the same line. So
            # look only near the command, plus the next line when the sentence
            # visibly continues onto it (prose wraps, and type-safety.md names a
            # command then calls it "broken in two independent ways" one line down).
            match = commands[0]
            position = line.find(match)
            nearby = line[max(0, position - 60) : position + len(match) + 45]
            if not line.rstrip().endswith((".", ":", "|")) and number < len(lines):
                nearby += " " + lines[number]

            recommending = bool(RECOMMENDATION.search(line))
            if not recommending and (NEGATION.search(nearby) or ILLUSTRATIVE.search(nearby)):
                continue
            if OWN_COMMAND.search(line) or GIT_COMMAND.search(line):
                continue
            previous = lines[number - 2] if number >= 2 else ""
            if WAIVER.search(previous) or WAIVER.search(line):
                continue

            violations.append(
                f"VIOLATION: {rel}:{number} presents a tool command as guidance.\n"
                f"  {line.strip()[:110]}\n"
                f"  matched: {match[:60]}\n"
                f"FIX: State the capability instead — what the declared command must emit, and "
                f"that the sensor is `inactive` when none can. Tool names, versions, flags and "
                f"defaults cannot be verified from this repository, and every one that was "
                f"checked upstream turned out to be wrong. To name a tool in order to warn "
                f"against it, say so on the same line. To keep it deliberately, add "
                f"`<!-- tool-command-ok: <reason> -->` on the line above."
            )

    if violations:
        print("\n\n".join(violations))
        return 1

    print(f"PASS: no tool commands presented as guidance in {len(scannable())} doc(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
