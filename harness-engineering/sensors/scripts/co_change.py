#!/usr/bin/env python3
"""Compute co-change (logical) coupling from git history.

Files that change together without importing each other are the empirical form
of a hidden dependency: the import graph says they are unrelated, the history
says one cannot move without the other.

    support     commits touching both files
    coupling    support / max(revs_a, revs_b)     symmetric, conservative
    confidence  support / revs_a                  asymmetric, one direction

`coupling` divides by the *busier* file so a hot file cannot manufacture strong
pairs against everything it brushes past. The two `confidence` values are
reported alongside because their asymmetry is the interesting part: a helper
that always moves with its caller, while the caller often moves alone, is a
different finding from two files that are genuinely welded together.

This is a DIAGNOSTIC for `../change-history.md`. It prints numbers and exits 0.
It never gates a PR — that sensor is scheduled-only by design, because a change
is not worse for touching a file that changes often. Thresholds here are
defaults for reproducibility, not calibrated values.

`--import-graph` accepts the JSON from
`skills/codebase-analysis/scripts/main_sequence.py --json` and marks each pair
`linked` when an import edge already explains it, or `hidden` when nothing in
the import graph does. Hidden pairs are the ones worth reading.

**`hidden` requires both components to be in the graph.** Without the flag every
pair is `unknown`; with a graph that does not contain one of the endpoints the
pair is `ungraphed`. Neither is `hidden`, and a truncated graph is rejected
outright — otherwise missing scanner coverage becomes an undeclared-dependency
finding, which is the failure this classification exists to prevent.

**Renames are detected but not followed.** The rename commit reports only the
new path, so no file is paired with its own former name; but commits before the
rename still carry the old path, so a renamed file's history is split across two
names. Stitching that identity is not implemented.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path

# Paths are read from `git log -z`, which emits them raw and NUL-separated.
# Without `-z` git C-quotes any path containing a control byte, a quote or a
# non-ASCII byte (`"src/line\nbreak.py"`), and parsing that line-by-line invents
# a path string: the directory filter, the module mapping and the graph lookup
# all then operate on something no file is named.
#
# With `-z` the commit header needs a boundary a path cannot forge. `%x01%H%x00`
# puts the hash in its own NUL-delimited field, so a header is recognised by
# matching the whole field, not by a prefix a filename could imitate.
COMMIT_HEADER = re.compile(r"\x01([0-9a-f]{7,64})\Z")

# An unborn branch: `git log` exits non-zero, but this is a fact about the
# repository rather than a tool failure, and the two must not be conflated.
NO_COMMITS_YET = re.compile(
    r"does not have any commits yet|bad default revision|unknown revision", re.I
)

DEFAULT_WINDOW = "180 days ago"

# A commit touching hundreds of files (a reformat, a license header sweep, a
# dependency bump, a directory move) pairs every file with every other one and
# invents coupling that no one would recognise. It also makes the pair count
# quadratic in the worst place. Bulk commits are dropped, and how many were
# dropped is reported -- silently discarding evidence is how a diagnostic starts
# lying.
DEFAULT_MAX_COMMIT_FILES = 50

DEFAULT_MIN_SUPPORT = 5
DEFAULT_MIN_COUPLING = 0.5

DEFAULT_EXCLUDED_DIRS = frozenset(
    {
        ".git",
        "node_modules",
        "__pycache__",
        "vendor",
        "dist",
        "build",
        ".venv",
        "venv",
        "site-packages",
    }
)

# Lockfiles, snapshots and generated output co-change with everything that
# touches their generator. The pair is real and tells you nothing.
GENERATED_SUFFIXES = (
    ".lock",
    ".snap",
    ".min.js",
    ".map",
)
GENERATED_NAMES = frozenset(
    {
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "poetry.lock",
        "Cargo.lock",
        "go.sum",
        "composer.lock",
        "Gemfile.lock",
    }
)


@dataclass
class Pair:
    a: str
    b: str
    support: int = 0

    module_a: str = ""
    module_b: str = ""
    revs_a: int = 0
    revs_b: int = 0
    link: str = "unknown"

    @property
    def coupling(self) -> float:
        busier = max(self.revs_a, self.revs_b)
        return self.support / busier if busier else 0.0

    @property
    def confidence_a(self) -> float:
        return self.support / self.revs_a if self.revs_a else 0.0

    @property
    def confidence_b(self) -> float:
        return self.support / self.revs_b if self.revs_b else 0.0

    @property
    def cross_module(self) -> bool:
        return self.module_a != self.module_b


@dataclass
class LogResult:
    """Raw log text plus why it is empty, which are different facts.

    Collapsing "git failed", "no history", "no commits in this window" and
    "every commit was filtered out" into one empty string made the summary
    report a healthy repository as inactive and hid dropped bulk commits.
    """

    text: str = ""
    status: str = "ok"
    detail: str = ""


@dataclass
class History:
    raw_commits: int = 0
    commits: int = 0
    dropped_bulk: int = 0
    dropped_empty: int = 0
    status: str = "ok"
    detail: str = ""
    revs: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    pairs: dict[tuple[str, str], int] = field(default_factory=lambda: defaultdict(int))

    @property
    def files(self) -> int:
        return len(self.revs)

    @property
    def inactive(self) -> bool:
        """No usable history at all, as opposed to history that yielded no pairs."""
        return self.status != "ok" or self.raw_commits == 0


# ------------------------------------------------------------------- history


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            errors="surrogateescape",
            check=False,
        )
    except (OSError, ValueError):
        return None


def is_shallow(root: Path) -> bool:
    completed = run_git(root, "rev-parse", "--is-shallow-repository")
    return bool(completed and completed.returncode == 0 and completed.stdout.strip() == "true")


def git_log(root: Path, since: str, allow_shallow: bool) -> LogResult:
    """Log text plus a status saying why it is empty when it is.

    Merge commits show no paths under `--name-only` unless asked, and are left
    out: a merge's file list is the union of its branch, which would pair every
    file in a feature with every other one.

    Renames are always detected. `--no-renames` emits **both** the old and the
    new path on the rename commit, which manufactures a co-change pair between a
    file and itself under its previous name — the exact artefact an earlier
    version of this script claimed that flag prevented. Detecting renames emits
    only the new path. Note this does **not** stitch a file's history across the
    rename: commits before it still carry the old path, so revision counts are
    split. That continuity is not implemented; see change-history.md.
    """
    if not allow_shallow and is_shallow(root):
        # A shallow clone's boundary commit has no parent, so git reports it as
        # touching every file in the snapshot. That single commit pairs the whole
        # tree at coupling 1.0 -- confident, reproducible, and entirely an
        # artefact of the clone depth.
        return LogResult(
            status="shallow",
            detail="shallow clone: the boundary commit reads as touching the entire tree",
        )
    completed = run_git(
        root,
        "log",
        f"--since={since}",
        "-z",
        "--name-only",
        "--no-merges",
        "--find-renames",
        "--pretty=format:\x01%H%x00",
    )
    if completed is None:
        return LogResult(status="git-error", detail="git could not be executed")
    stderr = (completed.stderr or "").strip()
    if completed.returncode != 0:
        # An unborn branch exits non-zero, but "no commits yet" is a fact about
        # the repository, not a tool failure. Everything else is a real error and
        # must never be reported as a clean scan.
        if NO_COMMITS_YET.search(stderr):
            return LogResult(status="no-history", detail="repository has no commits")
        return LogResult(
            status="git-error",
            detail=stderr.splitlines()[-1] if stderr else f"git exited {completed.returncode}",
        )
    if completed.stdout.strip("\0\n "):
        return LogResult(text=completed.stdout)

    # Empty output. "This repository has no history" and "this window is empty"
    # are different facts, and only the second implicates `--since`. Git does not
    # validate date expressions -- an unparseable `--since` is silently replaced
    # with a window git picked, so an empty window is also the symptom of a typo.
    probe = run_git(root, "rev-list", "--count", "-1", "HEAD")
    if probe is not None and probe.returncode == 0 and probe.stdout.strip() not in {"", "0"}:
        return LogResult(
            status="empty-window",
            detail=(
                f"repository has commits but none matched --since={since!r}; "
                "git does not reject an unparseable date, it substitutes one"
            ),
        )
    return LogResult(status="no-history", detail="repository has no commits")


def parse_log(text: str) -> list[list[str]]:
    """Split `git log -z` output into one path list per commit.

    Fields are NUL-delimited. A commit header is a field that is entirely
    `\\x01<hash>`; every other non-empty field is a path, whose leading newline
    (git's separator between the pretty format and the file list) is removed.
    Paths are otherwise untouched — no quoting to undo, no stripping that could
    alter a name with leading or trailing whitespace.
    """
    commits: list[list[str]] = []
    current: list[str] | None = None
    first_path = False
    for chunk in text.split("\0"):
        if COMMIT_HEADER.match(chunk):
            if current is not None:
                commits.append(current)
            current = []
            first_path = True
            continue
        if current is None:
            continue
        # Git writes its separator newline between the pretty format and the
        # file list, so it precedes the FIRST path only. Stripping it from every
        # field corrupted a file legitimately named "\nsecond.py".
        path = chunk[1:] if (first_path and chunk.startswith("\n")) else chunk
        first_path = False
        if path:
            current.append(path)
    if current is not None:
        commits.append(current)
    return commits


def is_excluded(path: str, extra_excludes: frozenset[str]) -> bool:
    parts = Path(path).parts
    if any(part in DEFAULT_EXCLUDED_DIRS | extra_excludes for part in parts[:-1]):
        return True
    name = parts[-1] if parts else path
    if name in GENERATED_NAMES:
        return True
    return name.endswith(GENERATED_SUFFIXES)


def module_for(path: str, depth: int) -> str:
    parts = Path(path).parts[:-1]
    if not parts:
        return "."
    if depth > 0:
        parts = parts[:depth]
    return "/".join(parts)


def build_history(
    log: LogResult | list[list[str]],
    max_commit_files: int,
    extra_excludes: frozenset[str],
) -> History:
    if isinstance(log, LogResult):
        commits = parse_log(log.text)
        history = History(status=log.status, detail=log.detail)
    else:
        commits = log
        history = History()

    for paths in commits:
        history.raw_commits += 1
        kept = sorted({p for p in paths if not is_excluded(p, extra_excludes)})
        if not kept:
            # Real commit, nothing measurable in it. Counted separately so an
            # all-lockfile window is not reported as "no history".
            history.dropped_empty += 1
            continue
        # The cap applies to the filtered list. Applying it to the raw list
        # dropped commits that were only large because of a lockfile churn the
        # filter was about to remove.
        if len(kept) > max_commit_files:
            history.dropped_bulk += 1
            continue
        history.commits += 1
        for path in kept:
            history.revs[path] += 1
        for a, b in combinations(kept, 2):
            history.pairs[(a, b)] += 1
    return history


# -------------------------------------------------------------- import graph


def load_import_graph(path: Path) -> dict[str, set[str]] | None:
    """Component adjacency from a main_sequence.py --json run.

    Returns undirected adjacency: an import in either direction explains a pair,
    because co-change does not have a direction to match against.
    """
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    components = payload.get("components")
    if not isinstance(components, list):
        return None
    run = payload.get("run")
    if isinstance(run, dict):
        total, shown = run.get("components"), run.get("components_shown")
        if isinstance(total, int) and isinstance(shown, int) and shown < total:
            # A `--top`-truncated graph is missing components, and every missing
            # one makes its pairs look unlinked. Accepting it would convert the
            # truncation into `hidden` findings. Rejected rather than used
            # partially, because a partial graph is indistinguishable from a
            # complete one once loaded.
            return None
    adjacency: dict[str, set[str]] = defaultdict(set)
    for component in components:
        if not isinstance(component, dict):
            continue
        name = component.get("name")
        if not isinstance(name, str):
            continue
        adjacency.setdefault(name, set())
        for key in ("depends_on", "depended_on_by"):
            for other in component.get(key) or []:
                if isinstance(other, str):
                    adjacency[name].add(other)
                    adjacency[other].add(name)
    return dict(adjacency)


def classify_link(pair: Pair, adjacency: dict[str, set[str]] | None) -> str:
    if adjacency is None:
        return "unknown"
    if not pair.cross_module:
        # Same module: an import edge between a component and itself is not
        # recorded, so "hidden" would be an artefact of the graph's granularity
        # rather than a finding.
        return "same-module"
    if pair.module_a not in adjacency or pair.module_b not in adjacency:
        # **Both** endpoints must be in the graph. If either is missing the
        # scanner never looked at it, so no edge to it could have been observed
        # and its absence is not evidence of anything.
        #
        # An earlier version required both to be *absent* before saying
        # `ungraphed`, which meant one Python component paired with one Go
        # component came back `hidden` -- turning "this language was not
        # scanned" into an undeclared-dependency finding that Observer may
        # escalate across an architecture boundary. That is precisely the
        # coverage-gap-as-finding error this sensor's own doc forbids.
        return "ungraphed"
    if pair.module_b in adjacency.get(pair.module_a, set()):
        return "linked"
    return "hidden"


# ------------------------------------------------------------------ analysis


def analyse(
    history: History,
    depth: int,
    min_support: int,
    min_coupling: float,
    adjacency: dict[str, set[str]] | None,
    cross_module_only: bool,
) -> list[Pair]:
    pairs: list[Pair] = []
    for (a, b), support in history.pairs.items():
        if support < min_support:
            continue
        pair = Pair(a=a, b=b, support=support)
        pair.revs_a = history.revs[a]
        pair.revs_b = history.revs[b]
        pair.module_a = module_for(a, depth)
        pair.module_b = module_for(b, depth)
        if pair.coupling < min_coupling:
            continue
        if cross_module_only and not pair.cross_module:
            continue
        pair.link = classify_link(pair, adjacency)
        pairs.append(pair)

    return sorted(
        pairs,
        key=lambda item: (
            # Hidden pairs first: they are the reason the measure exists. Within
            # a class, strength then volume then a stable name order.
            item.link != "hidden",
            -item.coupling,
            -item.support,
            item.a,
            item.b,
        ),
    )


# -------------------------------------------------------------------- output


def render_table(pairs: list[Pair], limit: int | None) -> str:
    shown = pairs if limit is None else pairs[:limit]
    if not shown:
        return "No co-change pairs above the thresholds."
    width = max(max(len(p.a), len(p.b)) for p in shown)
    header = (
        f"{'file pair'.ljust(width)}  supp  revs   coupling  conf   {'link'.ljust(11)}"
    )
    lines = [header, "-" * len(header)]
    for pair in shown:
        lines.append(
            f"{pair.a.ljust(width)}  {pair.support:4d}  {pair.revs_a:4d}  "
            f"{pair.coupling:8.2f}  {pair.confidence_a:4.2f}   {pair.link.ljust(11)}"
        )
        lines.append(
            f"{pair.b.ljust(width)}  {'':4}  {pair.revs_b:4d}  {'':8}  "
            f"{pair.confidence_b:4.2f}"
        )
        lines.append("")
    return "\n".join(lines).rstrip()


INACTIVE_REASONS = {
    "shallow": (
        "INACTIVE (shallow clone). The boundary commit reads as touching the entire "
        "tree, which would pair everything at coupling 1.00. Deepen the clone or pass "
        "--allow-shallow to measure anyway and treat every result as suspect."
    ),
    "git-error": (
        "INACTIVE (git error). This is not the same as a clean repository -- report "
        "the failure, never a zero."
    ),
    "no-history": "INACTIVE (repository has no commits). Report the absence, not a zero.",
    "empty-window": (
        "INACTIVE (no commits matched the window). The repository does have history, "
        "so check the --since expression: git substitutes a window for an "
        "unparseable date rather than rejecting it."
    ),
}


def render_summary(history: History, pairs: list[Pair], limit: int | None) -> str:
    if history.inactive:
        reason = INACTIVE_REASONS.get(
            history.status, "INACTIVE (no usable history). Report the absence, not a zero."
        )
        return f"{reason}{(' — ' + history.detail) if history.detail else ''}"

    hidden = [p for p in pairs if p.link == "hidden"]
    lines = [
        f"{history.raw_commits} commit(s) in window, {history.commits} measured, "
        f"{history.files} files, {len(pairs)} pair(s) above thresholds",
    ]
    if history.dropped_bulk:
        lines.append(
            f"{history.dropped_bulk} bulk commit(s) dropped above the file cap -- "
            "sweeps and directory moves pair every file with every other one."
        )
    if history.dropped_empty:
        lines.append(
            f"{history.dropped_empty} commit(s) touched only excluded files "
            "(lockfiles, generated output, excluded directories)."
        )
    if not history.commits:
        lines.append(
            "No commit survived filtering, so no pair could be formed. This is a "
            "filtering result, not an empty repository."
        )
    if hidden:
        lines.append(
            f"{len(hidden)} hidden pair(s): co-change with no import edge between "
            "their components. These are the candidates for a real dependency the "
            "code does not declare."
        )
    elif any(p.link == "unknown" for p in pairs):
        lines.append(
            "Link status is `unknown`: no --import-graph was supplied, so no pair "
            "can be called hidden. Unknown is not hidden."
        )
    if limit is not None and len(pairs) > limit:
        lines.append(f"showing {limit} of {len(pairs)} pair(s) (--top).")
    return "\n".join(lines)


def to_json(history: History, pairs: list[Pair], shown: list[Pair], config: dict) -> str:
    return json.dumps(
        {
            "config": config,
            "run": {
                "status": history.status,
                "detail": history.detail,
                "inactive": history.inactive,
                "raw_commits": history.raw_commits,
                "commits": history.commits,
                "files": history.files,
                "dropped_bulk_commits": history.dropped_bulk,
                "dropped_empty_commits": history.dropped_empty,
                "pairs_above_threshold": len(pairs),
                "pairs_shown": len(shown),
            },
            "pairs": [
                {
                    "a": pair.a,
                    "b": pair.b,
                    "module_a": pair.module_a,
                    "module_b": pair.module_b,
                    "support": pair.support,
                    "revs_a": pair.revs_a,
                    "revs_b": pair.revs_b,
                    "coupling": round(pair.coupling, 4),
                    "confidence_a": round(pair.confidence_a, 4),
                    "confidence_b": round(pair.confidence_b, 4),
                    "cross_module": pair.cross_module,
                    "link": pair.link,
                }
                for pair in shown
            ],
        },
        indent=2,
    )


def non_negative(raw: str) -> int:
    value = int(raw)
    if value < 0:
        raise argparse.ArgumentTypeError("must be 0 or greater")
    return value


def positive(raw: str) -> int:
    value = int(raw)
    if value < 1:
        raise argparse.ArgumentTypeError("must be 1 or greater")
    return value


def unit_interval(raw: str) -> float:
    value = float(raw)
    if not 0.0 <= value <= 1.0:
        raise argparse.ArgumentTypeError("must be between 0.0 and 1.0")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="co_change.py",
        description=(
            "Compute co-change coupling from git history. Diagnostic only -- "
            "always exits 0, never gates."
        ),
    )
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    parser.add_argument(
        "--since",
        default=DEFAULT_WINDOW,
        help=f"history window, any git date expression (default: {DEFAULT_WINDOW!r})",
    )
    parser.add_argument(
        "--min-support",
        type=positive,
        default=DEFAULT_MIN_SUPPORT,
        help=f"minimum shared commits for a pair (default: {DEFAULT_MIN_SUPPORT})",
    )
    parser.add_argument(
        "--min-coupling",
        type=unit_interval,
        default=DEFAULT_MIN_COUPLING,
        help=f"minimum support/max(revs) ratio (default: {DEFAULT_MIN_COUPLING})",
    )
    parser.add_argument(
        "--max-commit-files",
        type=positive,
        default=DEFAULT_MAX_COMMIT_FILES,
        help=(
            "drop commits touching more than N files after filtering "
            f"(default: {DEFAULT_MAX_COMMIT_FILES})"
        ),
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=0,
        help="collapse modules to the first N path segments (0 = containing directory)",
    )
    parser.add_argument(
        "--import-graph",
        metavar="JSON",
        default=None,
        help=(
            "main_sequence.py --json output; marks each pair linked or hidden. "
            "Without it every pair is `unknown`, which is not the same as hidden."
        ),
    )
    parser.add_argument(
        "--all-pairs",
        action="store_true",
        help="include same-module pairs (off by default: those are usually expected)",
    )
    parser.add_argument(
        "--allow-shallow",
        action="store_true",
        help=(
            "measure a shallow clone anyway; off by default because the boundary "
            "commit reads as touching the whole tree and pairs it at 1.00"
        ),
    )
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    parser.add_argument(
        "--top",
        type=non_negative,
        default=None,
        help="show only the first N pairs (0 shows none)",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="DIR",
        help="additional directory name to skip (repeatable)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root)
    if not root.is_dir():
        raise SystemExit(f"not a directory: {root}")

    adjacency = None
    if args.import_graph:
        adjacency = load_import_graph(Path(args.import_graph))
        if adjacency is None:
            raise SystemExit(f"could not read an import graph from: {args.import_graph}")

    history = build_history(
        git_log(root, args.since, args.allow_shallow),
        max_commit_files=args.max_commit_files,
        extra_excludes=frozenset(args.exclude),
    )
    pairs = analyse(
        history=history,
        depth=args.depth,
        min_support=args.min_support,
        min_coupling=args.min_coupling,
        adjacency=adjacency,
        cross_module_only=not args.all_pairs,
    )
    shown = pairs if args.top is None else pairs[: args.top]

    if args.json:
        print(
            to_json(
                history,
                pairs,
                shown,
                {
                    "since": args.since,
                    "min_support": args.min_support,
                    "min_coupling": args.min_coupling,
                    "max_commit_files": args.max_commit_files,
                    "depth": args.depth,
                    "cross_module_only": not args.all_pairs,
                    "import_graph": args.import_graph,
                    "allow_shallow": args.allow_shallow,
                },
            )
        )
        return 0

    print(render_table(shown, None))
    print()
    print(render_summary(history, pairs, args.top))
    return 0


if __name__ == "__main__":
    sys.exit(main())
