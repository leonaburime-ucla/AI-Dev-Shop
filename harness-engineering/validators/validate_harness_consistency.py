#!/usr/bin/env python3
"""Cross-file consistency checks for the code-quality metrics harness.

WHY THIS EXISTS
---------------
The gate rules are stated in prose across ~12 files. Three review rounds found
the same rule written correctly in one file and incorrectly in two or three
siblings -- the traversal scope was wrong in four places at once, and the
duplication predicate was correct in the sensor while the contract carried a
formulation rejected two rounds earlier. Every one of those was found by a human
or a peer model grepping, and the greps missed things twice.

Each check below encodes an invariant that has actually been violated. Adding a
check here is cheaper than another review round.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SENSORS = ROOT / "harness-engineering/sensors"
QUALITY = ROOT / "harness-engineering/quality"
CONTRACTS = ROOT / "framework/contracts"
REGISTRY = QUALITY / "gate-validation-status.md"

# Files that carry gate doctrine and must stay mutually consistent.
DOCTRINE_FILES = [
    *sorted(SENSORS.glob("*.md")),
    REGISTRY,
    CONTRACTS / "computational-controls.md",
    CONTRACTS / "architecture-fitness.md",
    ROOT / "agents/code-review/skills.md",
    ROOT / "agents/observer/skills.md",
    ROOT / "skills/code-review/SKILL.md",
    ROOT / "skills/function-quality-assessment/references/finding-rubric.md",
    ROOT / "skills/testable-design-patterns/SKILL.md",
    # The directory that declares itself normative was unpoliced by the
    # consistency validator -- gate-logic/README.md carried an unmarked
    # statement of a rejected predicate.
    ROOT / "harness-engineering/gate-logic/README.md",
    # Glob, do not hand-list: `quality/README.md` carried a live hard-coded gate
    # status for two rounds solely because only the registry was listed from
    # this directory. Every allowlist in this file has rotted at least once.
    *sorted(QUALITY.glob("*.md")),
]
DOCTRINE_FILES = sorted({p for p in DOCTRINE_FILES if p.is_file()}, key=str)

# Sensors whose detector compares fragments against each other, so scoping the
# SCAN to changed files destroys the check (as opposed to scoping attribution).
FULL_SCAN_SENSORS = {"duplication"}

failures: list[str] = []
checked = 0

# Per-check match census.
#
# Check 10 shipped with a regex that could not match this repo's canonical
# `INT-1`…`INT-9` form. It evaluated ZERO ranges, for an entire round, while a
# live stale range sat in the contract -- and the summary line said PASS the
# whole time, because a check that matches nothing is indistinguishable from a
# check that found nothing wrong.
#
# Every check now reports how many assertions it actually evaluated, and a check
# that evaluates zero on a corpus known to contain its subject FAILS. Silence is
# no longer a pass.
census: dict[str, int] = {}


def record(check: str, n: int = 1) -> None:
    global checked
    checked += n
    census[check] = census.get(check, 0) + n


# Checks that MUST find something to evaluate in this repo. If one of these
# reports zero, its matcher is broken -- that is the F1 failure mode.
MUST_MATCH = {
    "int-ids-resolve",
    "int-range-currency",
    "boundary-overclaim",
    "cycle-traversal",
    "registry-completeness",
    "never-capped-ids",
    "matcher-self-test",
    "duplication-predicate",
    "self-test-coverage",
    "integrity-set-parity",
    "capture-self-test",
    "window-self-test",
}

# F6: MUST_MATCH is a floor of ONE, so a check could lose 99% of its coverage
# silently -- anchoring INT_REF collapsed check 1 from 83 assertions to 3 and
# still passed. These are the observed stable counts; a large drop means a
# matcher narrowed, not that the corpus shrank.
CENSUS_FLOORS = {
    "int-ids-resolve": 60,
    "never-capped-ids": 40,
    "duplication-predicate": 8,
    "int-range-currency": 8,
    "registry-completeness": 4,
    "boundary-overclaim": 3,
    "cycle-traversal": 2,
}

# Checks whose violations are legitimately ABSENT from a healthy corpus, so zero
# is a real pass and no census can witness them. An earlier attempt gave them
# proxy counters over nearby vocabulary; sabotaging the real detectors left those
# numbers unchanged, which is worse than no number at all. They are protected
# solely by MATCHER_SELF_TESTS -- every one of their regexes is listed there.
CENSUS_CANNOT_WITNESS = {
    "gate-status-vocabulary",
    "clone-scan-scope",
    # Genuinely empty NOW. It previously read zero for the wrong reason: the
    # check scanned only `sensors/`, so five live witnesses in agents/, skills/
    # and framework/contracts/ were invisible and the exemption's stated
    # justification was false. Scope is now DOCTRINE_FILES and those five are
    # fixed, so the zero is real. Protected by STATUS_HARDCODE's self-test.
    "no-duplicated-status",
}

# Checks whose subject may legitimately be absent from a clean corpus: they fire
# only when a violation exists, so zero is a real pass. They are still printed in
# the census so a reader can see they ran.


def fail(path: Path, line_no: int, msg: str, fix: str) -> None:
    rel = path.relative_to(ROOT)
    failures.append(f"VIOLATION: {rel}:{line_no}\n  {msg}\n  FIX: {fix}")


def read(path: Path) -> list[str]:
    if not path.is_file():
        return []
    return path.read_text(encoding="utf-8").splitlines()


# Historical exemption is EXPLICIT, never inferred.
#
# An earlier version inferred "this is a record of a past mistake" from marker
# phrases ("earlier draft", "rejected", ...) within a 12-line window. Two
# independent reviewers defeated it in minutes: these docs narrate history
# immediately before stating the live rule, so the window covered exactly the
# positions where a wrong rule would be written. A live `base_occurrences < 3`
# predicate placed 12 lines after "An earlier draft was wrong" passed clean.
#
# Proximity cannot distinguish "this was wrong" from "this is the rule". So the
# author must mark it, on the line itself:
#
#     <!-- historical: the v2 predicate, kept so it cannot return silently -->
#
# Explicit, unambiguous, and impossible to trigger by writing ordinary prose.
HISTORICAL_MARKER_RE = re.compile(r"<!--\s*historical\b(?!:(?:start|end))", re.I)
# Region form, for a multi-line record such as a table of superseded rules,
# where a per-line marker would wreck the rendering:
#     <!-- historical:start -->  ... <!-- historical:end -->
HISTORICAL_START_RE = re.compile(r"<!--\s*historical:start\s*-->", re.I)
HISTORICAL_END_RE = re.compile(r"<!--\s*historical:end\s*-->", re.I)


def historical_regions(lines: list[str]) -> list[tuple[int, int]]:
    """1-based [start, end] line spans enclosed by explicit region markers."""
    spans, open_at = [], None
    for i, line in enumerate(lines, 1):
        if HISTORICAL_START_RE.search(line):
            open_at = i
        elif HISTORICAL_END_RE.search(line) and open_at is not None:
            spans.append((open_at, i))
            open_at = None
    return spans



# Detector regexes live at module level so MATCHER_SELF_TESTS can exercise every
# one of them. A detector defined inline inside its check is unreachable from the
# self-test, and three such detectors were silently dead.
NEVER_CAPPED = re.compile(r"never[- ]capped|not\s+capped|regardless of gate status", re.I)
STATUS_HARDCODE = re.compile(
    r"(?:currently|therefore|remains|now|today|sits at)\s+"
    r"`?(unvalidated|validated|inactive)`?",
    re.I,
)
CLONE_TOOL_FILES_SCOPE = re.compile(
    r"(jscpd|pmd\s+cpd|duplicate-code|cpd|simian|dupl)[^`|\n]*\{files\}", re.I
)
INT_REF = re.compile(r"`(INT-\d+)`")
# Hoisted from inside their checks so check_self_test_coverage can see them.
# Both were live detectors invisible to the coverage assertion; widening
# INT_ID_IN_CLAIM back to `[\d*]+` restores the `INT-*` skeleton key, and
# de-anchoring REGISTRY_ID_ROW makes any ID merely mentioned in registry prose
# count as registered.
INT_ID_IN_CLAIM = re.compile(r"`INT-\d+`")
REGISTRY_ID_ROW = re.compile(r"^\|\s*`(INT-\d+)`\s*\|", re.M)
# These three CAPTURE values that other numbers are compared against. Round 8
# pinned INT_RANGE_RE (the left operand of check 10's comparison) and left
# REGISTRY_ID_NUM -- the right operand -- inline and unasserted, so a
# single-digit mutation there silently made every range compare clean.
REGISTRY_ID_NUM = re.compile(r"^\|\s*`INT-(\d+)`\s*\|", re.M)
REGISTRY_ID_PAIR = re.compile(r"^\|\s*`(INT-(\d+))`\s*\|", re.M)
INTEGRITY_RANGE_LITERAL = re.compile(r"(?<![A-Za-z_])range\(1,\s*(\d+)\)")

# Detectors whose CAPTURE (not merely whether they match) feeds a comparison.
# Listed explicitly so deleting a CAPTURE_SELF_TESTS entry is a failure, not a
# silent census tick-down.
CAPTURING_DETECTORS = (
    "INT_REF", "INT_RANGE_RE", "REGISTRY_ID_NUM",
    "REGISTRY_ID_PAIR", "INTEGRITY_RANGE_LITERAL",
)


def _window(lines: list[str], line_no: int) -> list[str]:
    """The symmetric span a wrapped claim can occupy: the line, plus one each side.

    Forward-only was wrong in both directions. It flagged a claim from the two
    lines ABOVE it -- so a marker on the offending line could not reach those
    iterations, which forced bare marker lines to be stacked above the real one
    as a workaround. And it could not see an `INT-N` id that had wrapped onto the
    PREVIOUS line, failing correct text like
    "Findings mapped to `INT-4`\\nare never capped."
    """
    return lines[max(0, line_no - 2):line_no + 1]


def flatten(lines: list[str], line_no: int) -> str:
    """Join a line with its neighbours so a claim wrapped across a line break is
    still visible. Several checks used to match per-line, which meant
    'is never\\ncapped' evaded them."""
    return " ".join(_window(lines, line_no))


def is_historical_note(lines: list[str], line_no: int) -> bool:
    """True only when an explicit marker sits in the same span the check reads.

    Scoped to exactly the window `flatten()` examines -- no wider, no narrower.
    Still explicit: an author must write the marker; no amount of ordinary
    historical prose triggers it.
    """
    # Scans exactly the span the claim is READ from. Any narrower and a marker
    # on the offending line cannot exempt the iterations that flag the same
    # wrapped claim from a neighbouring line -- which forced bare marker lines to
    # be stacked as a workaround. Any wider and it exempts unmarked rules nearby.
    if any(HISTORICAL_MARKER_RE.search(c) for c in _window(lines, line_no)):
        return True
    return any(lo <= line_no <= hi for lo, hi in historical_regions(lines))


# --------------------------------------------------------------------------
# 1. Every INT-N reference resolves to an ID registered in the registry
# --------------------------------------------------------------------------

def check_int_ids_resolve() -> None:
    registry_text = REGISTRY.read_text(encoding="utf-8") if REGISTRY.is_file() else ""
    registered = set(REGISTRY_ID_ROW.findall(registry_text))
    if not registered:
        failures.append(
            f"VIOLATION: {REGISTRY.relative_to(ROOT)}\n"
            "  No INT-* IDs found in the canonical integrity table.\n"
            "  FIX: the registry must define the closed integrity set."
        )
        return
    for path in DOCTRINE_FILES:
        for i, line in enumerate(read(path), 1):
            for ref in INT_REF.findall(line):
                record("int-ids-resolve")
                if ref not in registered:
                    fail(path, i, f"references {ref}, which is not registered.",
                         f"add {ref} to the canonical table in gate-validation-status.md, "
                         "or cite a registered ID.")


# --------------------------------------------------------------------------
# 2. No "never capped" claim without a registered INT ID
#    (an un-ID'd uncapped class silently breaks the closed-list guarantee)
# --------------------------------------------------------------------------

def check_never_capped_rows_carry_ids() -> None:
    pattern = NEVER_CAPPED
    for path in DOCTRINE_FILES:
        if path == REGISTRY:
            continue  # the registry defines them; it need not cite itself per row
        lines = read(path)
        for i, line in enumerate(lines, 1):
            window = flatten(lines, i)
            if not pattern.search(window):
                continue
            if is_historical_note(lines, i):
                continue  # explicitly marked as a record of a past mistake
            record("never-capped-ids")
            # A CONCRETE id, or the canonical collective range. The bare `INT-*`
            # wildcard used to satisfy this, which let any sensor invent a new
            # uncapped class by appending it -- a skeleton key to the closed set.
            if not INT_ID_IN_CLAIM.search(window):
                fail(path, i,
                     "claims a finding is never capped without naming a registered INT ID.",
                     "cite the specific `INT-N`, or remove the uncapped claim. An "
                     "un-ID'd uncapped class breaks the closed integrity set.")


# --------------------------------------------------------------------------
# 3. advisory/blocking must not be used as GATE STATUS
#    (they are per-rule severity in architecture-fitness; the collision caused
#     a real misreading in round 2)
# --------------------------------------------------------------------------

STALE_STATUS = re.compile(
    r"currently\s+`?advisory`?"
    r"|at\s+`blocking`\s+status"
    r"|`advisory`\s+gate\s+status"
    r"|advisory\s+gate\s+status"
    r"|while\s+it\s+is\s+`advisory`"
    r"|gates?\s+are\s+currently\s+`?advisory`?"
    r"|gate\s+status\s+is\s+(?:advisory|blocking)"
    r"|is\s+advisory\s+(?:until|pending)",
    re.I,
)


def check_gate_status_vocabulary() -> None:
    for path in DOCTRINE_FILES:
        lines = read(path)
        joined = "\n".join(lines)
        # also catch the phrase split across a line wrap
        flat = re.sub(r"\s*\n\s*", " ", joined)
        if STALE_STATUS.search(flat):
            # Gate the census on the DETECTION PATTERN, never on file existence.
            # Counting files scanned made this number independent of whether
            # STALE_STATUS still matches anything -- monkeypatching the regex to
            # an unmatchable string left the census at 19 and raised nothing,
            # which is precisely the dead-check ambiguity the census exists to
            # remove, reintroduced one level up.
            record("gate-status-vocabulary")
            for i, line in enumerate(lines, 1):
                window = " ".join(lines[max(0, i - 1):i + 2])
                if STALE_STATUS.search(window):
                    record("gate-status-vocabulary")
                    fail(path, i,
                         "uses advisory/blocking as a GATE STATUS.",
                         "gate statuses are `unvalidated` / `validated` / `inactive`. "
                         "advisory/blocking are per-rule Severity in architecture-fitness.md.")


# --------------------------------------------------------------------------
# 4. Sensors must not hard-code a status value the registry owns
# --------------------------------------------------------------------------

def check_no_duplicated_status_value() -> None:
    pattern = STATUS_HARDCODE
    for path in DOCTRINE_FILES:
        for i, line in enumerate(read(path), 1):
            if pattern.search(line):
                record("no-duplicated-status")
                fail(path, i,
                     "hard-codes a gate status value the registry owns.",
                     "defer to gate-validation-status.md instead. Two copies drift, and "
                     "the copy an agent reads decides whether a pipeline blocks.")


# --------------------------------------------------------------------------
# 5. Scan-scope: fragment-comparing detectors must not be given {files}
# --------------------------------------------------------------------------

def check_full_scan_commands() -> None:
    # Scan every doctrine file. An earlier version broadened the tool regex but
    # left a two-file allowlist, so `jscpd ... {files}` in sensors/README.md and
    # `pmd cpd ... {files}` in agents/code-review/skills.md both escaped -- the
    # second being the file a reviewing agent actually reads.
    targets = DOCTRINE_FILES
    # Named-tool allowlists rot: `pylint --enable=duplicate-code {files}` sat in
    # the same table and escaped, because it was not one of the two names.
    # Match ANY command in a clone-detector context that takes {files}.
    tool_re = CLONE_TOOL_FILES_SCOPE

    for path in targets:
        for i, line in enumerate(read(path), 1):
            if tool_re.search(line):
                record("clone-scan-scope")
                fail(path, i,
                     "passes {files} to a clone detector.",
                     "use {src}. A detector given only changed files cannot see that a "
                     "new copy matches two untouched ones -- the rule-of-three catch dies.")


# --------------------------------------------------------------------------
# 6. Cycle detection must never be scoped to one importer level
# --------------------------------------------------------------------------

ONE_LEVEL = re.compile(r"one level of direct importers", re.I)
CARVE_OUT = re.compile(r"full reachable closure|cycle detection needs", re.I)


def check_cycle_traversal_scope() -> None:
    targets = [
        SENSORS / "dependency-structure.md",
        CONTRACTS / "computational-controls.md",
        ROOT / "agents/code-review/skills.md",
    ]
    for path in targets:
        lines = read(path)
        for i, line in enumerate(lines, 1):
            if not ONE_LEVEL.search(line):
                continue
            record("cycle-traversal")
            window = " ".join(lines[max(0, i - 2):i + 2])
            if not CARVE_OUT.search(window):
                fail(path, i,
                     "states one-importer-level scope with no full-closure carve-out for cycles.",
                     "a cycle can close through files the diff never touched; one level "
                     "cannot support a 'no cycles' result.")


# --------------------------------------------------------------------------
# 7. The dependency graph covers three rule types, never four
# --------------------------------------------------------------------------

OVERCLAIM = re.compile(
    r"all four (?:rule )?types"
    r"|(?:and|cycles)\s+\*?\*?the other three rule types"
    r"|covers all four",
    re.I,
)
# Deliberately specific. An earlier version accepted the bare word "never",
# which meant a live overclaim reading "covers all four rule types and never
# misses a violation" neutralised its own check.
NEGATED = re.compile(
    r"do not describe|never claim|not covered|it covers three|is wrong"
    r"|covers three|not all four|is not covered",
    re.I,
)


def check_boundary_ownership_overclaim() -> None:
    for path in DOCTRINE_FILES:
        lines = read(path)
        for i, line in enumerate(lines, 1):
            window = flatten(lines, i)
            if not OVERCLAIM.search(window):
                continue
            record("boundary-overclaim")
            if NEGATED.search(window):
                continue  # a sentence forbidding the overclaim is fine
            fail(path, i,
                 "claims the dependency graph covers all four architecture rule types.",
                 "boundary_ownership asserts a human approval; no import graph can "
                 "observe one. It covers three.")


# --------------------------------------------------------------------------
# 8. Every gate that defers to the registry must appear in the registry
# --------------------------------------------------------------------------

def check_registry_completeness() -> None:
    if not REGISTRY.is_file():
        return
    registry_text = REGISTRY.read_text(encoding="utf-8")
    for path in sorted(SENSORS.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if "gate-validation-status.md" not in text:
            continue
        record("registry-completeness")
        if path.name not in registry_text:
            fail(path, 1,
                 f"defers to the registry but {path.name} has no row there.",
                 "add its gate(s) to the status registry, or drop the deferral.")


# --------------------------------------------------------------------------
# 9. Duplication predicate must be stated identically wherever it appears
# --------------------------------------------------------------------------

REJECTED_PREDICATES = [
    (re.compile(
        r"only a (?:\*\*)?new(?:\*\*)? Type-1/Type-2 clone group"
        r"|(?:group|clone)[^.\n]{0,60}?not present (?:in the merge base|at base)"
        r"|not present (?:in the merge base|at base)[^.\n]{0,60}?(?:group|clone)",
        re.I),
     "the v1 'new group' predicate, rejected in round 2"),
    (re.compile(r"base_occurrences\s*<\s*3", re.I),
     "the v2 'base < 3' predicate, rejected in round 3"),
]


def check_duplication_predicate() -> None:
    for path in DOCTRINE_FILES:
        lines = read(path)
        for i, line in enumerate(lines, 1):
            window = flatten(lines, i)
            for pattern, label in REJECTED_PREDICATES:
                if not pattern.search(window):
                    continue
                # Count the site as evaluated BEFORE the exemption is consulted.
                # Recording below the early-continue hid three live corpus
                # witnesses and made this check look unwitnessable.
                record("duplication-predicate")
                if is_historical_note(lines, i):
                    continue  # explicitly marked as a historical mistake
                fail(path, i,
                     f"states {label}.",
                     "the canonical predicate is "
                     "`head_occurrences > base_occurrences && head_occurrences >= 3` "
                     "(see harness-engineering/gate-logic/reference.py).")


# --------------------------------------------------------------------------
# 10. Every stated INT range must end at the registry's highest ID
#     (adding INT-9 and leaving five files saying INT-1..INT-8 is exactly the
#      drift this validator existed to catch, and it passed clean)
# --------------------------------------------------------------------------

INT_RANGE_RE = re.compile(
    r"`?INT-(\d+)`?\s*(?:…|\.\.\.|\.\.|—|–|-|through|to)\s*`?INT-(\d+)`?"
)


def check_int_range_currency() -> None:
    if not REGISTRY.is_file():
        return
    registry_text = REGISTRY.read_text(encoding="utf-8")
    ids = [int(n) for n in REGISTRY_ID_NUM.findall(registry_text)]
    if not ids:
        return
    top = max(ids)
    for path in DOCTRINE_FILES:
        for i, line in enumerate(read(path), 1):
            for lo, hi in INT_RANGE_RE.findall(line):
                record("int-range-currency")
                if int(hi) != top:
                    fail(path, i,
                         f"states the integrity set as INT-{lo}..INT-{hi}, but the "
                         f"registry defines {len(ids)} IDs up to INT-{top}.",
                         f"update the range to INT-1…INT-{top}. A stale range means the "
                         "agent reading it will never raise the missing ID.")


# --------------------------------------------------------------------------
# 11. Threshold literals in a reference command must agree across files
#     (the sensor was rewritten to configure at the band's lower edge; the
#      contract hosts actually copy from stayed at the gate value)
# --------------------------------------------------------------------------






# --------------------------------------------------------------------------
# Matcher self-test — the only dead-check protection that works for a check
# whose violations are legitimately ABSENT from a healthy corpus.
#
# The census proves a matcher ran against real content. It cannot prove a
# matcher still WORKS when the corpus is clean, because "no violations" and
# "regex is broken" both produce zero. Round 6 demonstrated this by
# monkeypatching STALE_STATUS to an unmatchable string: the check went silent
# and nothing noticed. So every detection regex is exercised here against a
# known-bad sample it MUST match and a known-good sample it must NOT.
# --------------------------------------------------------------------------

MATCHER_SELF_TESTS = [
    # One sample PER BRANCH -- four of eight branches previously had none, so
    # half the detector could be deleted with no signal. Plus a capitalised
    # sample: every sample was lowercase, so `re.I` could be stripped silently.
    ("STALE_STATUS", lambda: STALE_STATUS,
     ["this gate is currently `advisory`",
      "the gate sits at `blocking` status",
      "it has `advisory` gate status",
      "this is an advisory gate status",
      "while it is `advisory` nothing blocks",
      "the gates are currently advisory",
      "gate status is blocking",
      "is advisory until validated",
      "Currently `advisory` — do not block on it"],
     ["this gate is currently `unvalidated`", "a `blocking`-severity rule"]),
    ("OVERCLAIM", lambda: OVERCLAIM,
     ["it covers all four rule types",
      "covers cycles and the other three rule types",
      "the graph covers all four",
      "All four rule types are covered by the graph"],
     ["it covers three rule types"]),
    ("NEGATED", lambda: NEGATED,
     ["do not describe it as covering all four", "it covers three",
      "Do not describe it as covering all four"],
     # Over-broadening this silently disables check 7 entirely.
     ["never misses a violation", "the graph does not miss anything",
      "not all of the rule types are graph-checkable is fine"]),
    ("INT_RANGE_RE", lambda: INT_RANGE_RE,
     ["`INT-1`…`INT-9`", "INT-1..INT-8", "`INT-1`-`INT-9`",
      "`INT-1`…`INT-12`", "INT-1 through INT-12", "INT-1 to INT-9",
      "INT-1—INT-9", "INT-1–INT-9", "INT-1...INT-9"],
     ["INT-9 is registered"]),
    ("HISTORICAL_MARKER_RE", lambda: HISTORICAL_MARKER_RE,
     ["<!-- historical -->", "<!--historical: the v2 predicate -->",
      "<!-- HISTORICAL -->"],
     # A bare `<!--` must NOT exempt: over-broadening this regex would let any
     # HTML comment within one line silently disable two checks.
     ["this is historical prose", "<!-- TODO: revisit -->", "<!-- nosec -->"]),
    ("HISTORICAL_START_RE", lambda: HISTORICAL_START_RE,
     ["<!-- historical:start -->", "<!-- HISTORICAL:START -->"],
     ["<!-- historical -->", "<!-- start -->"]),
    ("HISTORICAL_END_RE", lambda: HISTORICAL_END_RE,
     ["<!-- historical:end -->", "<!-- Historical:End -->"],
     ["<!-- historical -->", "<!-- end -->"]),
    ("CARVE_OUT", lambda: CARVE_OUT,
     ["the full reachable closure of every changed module", "cycle detection needs",
      "Full reachable closure is required for cycles"],
     # Over-broadening this silently disables check 6 entirely, so the negatives
     # pin the exact words a lazy widening would reach for.
     ["nothing to do with transitive closure of anything",
      "a cycle can close through untouched files",
      "resolve the import graph first",
      "detection of cycles is the point"]),
    ("ONE_LEVEL", lambda: ONE_LEVEL,
     ["plus one level of direct importers", "One level of direct importers"],
     ["the full closure"]),
    ("REJECTED_PREDICATES[v1]", lambda: REJECTED_PREDICATES[0][0],
     ["only a **new** Type-1/Type-2 clone group with 3+ sites",
      "the clone group is Not present in the merge base",
      "Only a new Type-1/Type-2 clone group with 3+ sites"],
     ["a clone group crossing to 3+ sites"]),
    ("REJECTED_PREDICATES[v2]", lambda: REJECTED_PREDICATES[1][0],
     ["breaches when `base_occurrences < 3` and the head count",
      "breaches when `Base_Occurrences < 3` and the head count"],
     ["head_occurrences > base_occurrences"]),
    ("NEVER_CAPPED", lambda: NEVER_CAPPED,
     ["this row is never capped", "is not capped by gate status",
      "blocks regardless of gate status", "Not capped by the registry",
      "this row is never-capped"],
     ["capped at `RECOMMENDED`"]),
    ("STATUS_HARDCODE", lambda: STATUS_HARDCODE,
     ["currently `unvalidated`", "currently validated",
      "nesting is currently `inactive` on this stack",
      "Currently `unvalidated`, so REQUIRED is capped",
      "this gate's status is therefore `unvalidated`",
      "the gate remains `unvalidated`",
      "the gate is now `validated`",
      "the gate sits at `inactive`"],
     # Must NOT fire on a deferral -- that is the phrasing we want authors using.
     # Must NOT fire on a deferral, nor on CONDITIONAL phrasing that states the
     # rule rather than asserting a current value.
     ["status is recorded in the registry",
      "each gate's status is recorded there",
      "read the current status in the registry",
      "blocks only when the gate is `validated`",
      "while a gate is not `validated` its findings are capped"]),
    # One sample per tool branch -- the branch added BECAUSE pylint escaped had
    # no sample of its own, so it was one deletion from regressing.
    ("CLONE_TOOL_FILES_SCOPE", lambda: CLONE_TOOL_FILES_SCOPE,
     ["`npx jscpd --min-tokens 50 {files}`", "`pmd cpd --dir {files}`",
      "pylint --enable=duplicate-code {files}", "simian -threshold=50 {files}",
      "dupl -t 50 {files}", "JSCPD --min-tokens 50 {files}"],
     ["`npx jscpd --min-tokens 50 {src}`"]),
    # Multi-digit: both INT regexes go blind the day INT-10 lands, which is the
    # first day check 10 matters.
    ("INT_REF", lambda: INT_REF, ["`INT-4`", "`INT-12`"], ["INT4", "`INT`"]),
    ("INT_ID_IN_CLAIM", lambda: INT_ID_IN_CLAIM, ["`INT-4`", "`INT-12`"],
     # Must NOT accept the wildcard: that was the skeleton key to the closed set.
     ["`INT-*`", "INT-4", "`INT`"]),
    ("REGISTRY_ID_NUM", lambda: REGISTRY_ID_NUM,
     ["| `INT-7` | some finding |"], ["see `INT-7` for details"]),
    ("REGISTRY_ID_PAIR", lambda: REGISTRY_ID_PAIR,
     ["| `INT-7` | some finding |"], ["see `INT-7` for details"]),
    ("INTEGRITY_RANGE_LITERAL", lambda: INTEGRITY_RANGE_LITERAL,
     ["range(1, 10)", "range(1,10)"], ["range(2, 10)", "xrange(1, 10)"]),
    ("REGISTRY_ID_ROW", lambda: REGISTRY_ID_ROW,
     ["| `INT-7` | some finding |"],
     # Must NOT match an ID merely mentioned in prose outside the table.
     ["see `INT-7` for details", "`INT-7`"]),
]


def check_self_test_coverage() -> None:
    """Every module-level detector regex must appear in MATCHER_SELF_TESTS.

    The list was previously maintained by convention: individual entries could be
    deleted silently, and dropping all four entries for the checks that have no
    census witness still exited 0. Coverage is now asserted, not assumed.
    """
    # Key on the IDENTITY of the object each entry actually exercises, not on
    # its label. A label-keyed set was satisfied by an entry named "STALE_STATUS"
    # whose lambda returned a different regex entirely. And the `_`-prefix
    # exemption was a pure escape hatch -- no underscore-prefixed pattern exists,
    # so it could only ever be used to hide one.
    tested_ids = set()
    for _n, get, *_rest in MATCHER_SELF_TESTS:
        try:
            tested_ids.add(id(get()))
        except Exception:
            pass
    rejected_tested = {n for n, *_ in MATCHER_SELF_TESTS if n.startswith("REJECTED_PREDICATES")}
    for idx, (pat, _label) in enumerate(REJECTED_PREDICATES):
        record("self-test-coverage")
        if f"REJECTED_PREDICATES[v{idx + 1}]" not in rejected_tested:
            fail(Path(__file__), 1,
                 f"REJECTED_PREDICATES[{idx}] has no MATCHER_SELF_TESTS entry.",
                 "this list self-exempted from the id() walk, so both entries could "
                 "be deleted silently -- removing all protection on the predicates "
                 "this validator most exists to police.")
        tested_ids.add(id(pat))

    def _patterns_in(obj):
        if isinstance(obj, re.Pattern):
            yield obj
        elif isinstance(obj, (list, tuple, set, frozenset)):
            for item in obj:
                yield from _patterns_in(item)
        elif isinstance(obj, dict):
            for k, v in obj.items():
                yield from _patterns_in(k)   # keys too: a detector hid here
                yield from _patterns_in(v)
        elif hasattr(obj, "__dict__") and not isinstance(obj, type(re)):
            for item in vars(obj).values():
                yield from _patterns_in(item)

    for name, value in sorted(globals().items()):
        for pat in _patterns_in(value):
            record("self-test-coverage")
            if id(pat) not in tested_ids:
                fail(Path(__file__), 1,
                     f"detector regex in `{name}` has no entry in MATCHER_SELF_TESTS.",
                     "every detector must be exercised against known-bad and "
                     "known-good samples; an untested regex can be broken silently.")
    # Every CAPTURING detector must have a CAPTURE_SELF_TESTS entry, asserted by
    # identity. Matching is not enough for these: they extract a value another
    # number is compared against, and a pattern that matches while mis-capturing
    # makes every such comparison silently wrong.
    captured_ids = set()
    for _n, get, *_r in CAPTURE_SELF_TESTS:
        try:
            captured_ids.add(id(get()))
        except Exception:
            pass
    for name in CAPTURING_DETECTORS:
        record("self-test-coverage")
        pat = globals().get(name)
        if pat is None or id(pat) not in captured_ids:
            fail(Path(__file__), 1,
                 f"capturing detector `{name}` has no CAPTURE_SELF_TESTS entry.",
                 "its extraction is unasserted; a mis-capturing pattern reports "
                 "clean while every comparison against its value is wrong.")





def check_integrity_set_parity() -> None:
    """`reference.py`'s CANONICAL_INTEGRITY_IDS must equal the registry's set.

    The module declares itself normative over prose, yet its frozenset was a
    hand-maintained copy of the registry that owns the set. Registering INT-10
    made `apply_status_cap(..., integrity_id="INT-10")` raise -- it failed in the
    safe direction, but nothing tied the copies together.
    """
    ref = ROOT / "harness-engineering/gate-logic/reference.py"
    if not (ref.is_file() and REGISTRY.is_file()):
        return
    registered = set(REGISTRY_ID_PAIR.findall(REGISTRY.read_text(encoding="utf-8")))
    top = max((int(n) for _, n in registered), default=0)
    m = INTEGRITY_RANGE_LITERAL.search(ref.read_text(encoding="utf-8"))
    record("integrity-set-parity")
    if not m:
        fail(ref, 1, "CANONICAL_INTEGRITY_IDS is not in the expected range() form.",
             "the parity check cannot read it; keep the literal range or update the check.")
    elif int(m.group(1)) - 1 != top:
        fail(ref, 1,
             f"CANONICAL_INTEGRITY_IDS covers INT-1..INT-{int(m.group(1)) - 1}, "
             f"but the registry defines up to INT-{top}.",
             "the registry owns the closed set; a newly-registered ID would raise "
             "ValueError in the normative implementation.")


# (regex name, sample, expected capture tuple)
CAPTURE_SELF_TESTS = [
    ("INT_REF", lambda: INT_REF, "`INT-12`", ["INT-12"]),
    ("REGISTRY_ID_NUM", lambda: REGISTRY_ID_NUM, "| `INT-12` | a finding |", ["12"]),
    ("REGISTRY_ID_PAIR", lambda: REGISTRY_ID_PAIR, "| `INT-12` | a finding |",
     [("INT-12", "12")]),
    ("INTEGRITY_RANGE_LITERAL", lambda: INTEGRITY_RANGE_LITERAL,
     "frozenset(f\"INT-{n}\" for n in range(1, 12))", ["12"]),
    ("INT_RANGE_RE", lambda: INT_RANGE_RE, "`INT-1`…`INT-12`", [("1", "12")]),
    ("INT_RANGE_RE", lambda: INT_RANGE_RE, "INT-10 through INT-12", [("10", "12")]),
]






def check_window_self_test() -> None:
    """Pin `_window`'s exact bounds.

    Every regex is self-tested; the function that slices the text FOR them was
    not. Widening it by one line (`- 2` -> `- 3`) lets a marker three lines above
    an unmarked live rule exempt it, and no census catches that because the count
    goes UP.
    """
    lines = ["a", "b", "c", "d", "e"]
    cases = [(1, ["a", "b"]), (2, ["a", "b", "c"]), (3, ["b", "c", "d"]),
             (5, ["d", "e"])]
    for line_no, expected in cases:
        record("window-self-test")
        got = _window(lines, line_no)
        if got != expected:
            fail(Path(__file__), 1,
                 f"_window(line {line_no}) returned {got!r}, expected {expected!r}.",
                 "the window feeds three checks; widening it exempts unmarked "
                 "rules near a marker, and the census rises rather than falls.")
    # A marker must reach exactly one line each way, never two.
    marked = ["x", "<!-- historical -->", "y", "z"]
    record("window-self-test")
    if not is_historical_note(marked, 3):
        fail(Path(__file__), 1, "_window: a marker one line above does not exempt.",
             "a wrapped claim must be coverable by one marker.")
    record("window-self-test")
    if is_historical_note(marked, 4):
        fail(Path(__file__), 1, "_window: a marker two lines above still exempts.",
             "too wide -- unmarked live rules near a marker become invisible.")


def check_capture_self_test() -> None:
    """Assert what each capturing detector EXTRACTS, not merely that it matched.

    `INT_REF`/`INT_RANGE_RE` exist to pull an ID number out for comparison. A
    single-digit mutation still matches `INT-12` while capturing "1", which makes
    check 10 compare 1 against a registry top of 10 -- the day INT-10 lands, every
    range in the repo is either falsely stale or falsely accepted.
    """
    for name, get, sample, expected in CAPTURE_SELF_TESTS:
        record("capture-self-test")
        got = get().findall(sample)
        if got != expected:
            fail(Path(__file__), 1,
                 f"capturing matcher `{name}` extracted {got!r} from {sample!r}, "
                 f"expected {expected!r}.",
                 "the pattern matches but mis-captures; every consumer comparing "
                 "the captured value is silently wrong.")


def check_matchers_self_test() -> None:
    for name, get, positives, negatives in MATCHER_SELF_TESTS:
        rx = get()
        for sample in positives:
            record("matcher-self-test")
            if not rx.search(sample):
                failures.append(
                    f"VIOLATION: harness-engineering/validators/validate_harness_consistency.py\n"
                    f"  matcher `{name}` FAILED to match a known-bad sample: {sample!r}\n"
                    f"  FIX: the regex is broken. A broken matcher reports PASS on a clean "
                    f"corpus forever -- this is how a dead INT-range regex hid a live stale "
                    f"range for a full round."
                )
        for sample in negatives:
            record("matcher-self-test")
            if rx.search(sample):
                failures.append(
                    f"VIOLATION: harness-engineering/validators/validate_harness_consistency.py\n"
                    f"  matcher `{name}` matched a known-GOOD sample: {sample!r}\n"
                    f"  FIX: over-broad regex; it will produce false violations."
                )


def main() -> int:
    check_int_ids_resolve()
    check_never_capped_rows_carry_ids()
    check_gate_status_vocabulary()
    check_no_duplicated_status_value()
    check_full_scan_commands()
    check_cycle_traversal_scope()
    check_boundary_ownership_overclaim()
    check_registry_completeness()
    check_duplication_predicate()
    check_int_range_currency()
    check_matchers_self_test()
    check_self_test_coverage()
    check_capture_self_test()
    check_window_self_test()
    check_integrity_set_parity()

    dead = sorted(name for name in MUST_MATCH if census.get(name, 0) == 0)
    for name in ("matcher-self-test", "self-test-coverage", "capture-self-test"):
        CENSUS_FLOORS.setdefault(name, 3)
    for name, floor in sorted(CENSUS_FLOORS.items()):
        got = census.get(name, 0)
        if 0 < got < floor:
            failures.append(
                f"VIOLATION: harness-engineering/validators/validate_harness_consistency.py\n"
                f"  check `{name}` evaluated {got} assertions, below its floor of {floor}.\n"
                f"  FIX: a large drop means the matcher narrowed, not that the corpus "
                f"shrank. 'Matched almost nothing' was indistinguishable from healthy."
            )
    for name in dead:
        failures.append(
            f"VIOLATION: harness-engineering/validators/validate_harness_consistency.py\n"
            f"  check `{name}` evaluated ZERO assertions -- its matcher is broken.\n"
            f"  FIX: a check that matches nothing reports PASS forever. This is how a "
            f"dead INT-range regex hid a live stale range for a full round."
        )

    if failures:
        print(f"Harness consistency: {len(failures)} violation(s) across "
              f"{checked} checked assertions.\n")
        for f in failures:
            print(f)
            print()
        _print_census()
        return 1
    print(f"PASS: harness gate doctrine consistent ({checked} assertions checked).")
    _print_census()
    return 0


def _print_census() -> None:
    print("\n  per-check census (zero on a MUST_MATCH check is itself a failure):")
    for name in sorted(set(census) | MUST_MATCH | CENSUS_CANNOT_WITNESS):
        n = census.get(name, 0)
        if name in CENSUS_CANNOT_WITNESS:
            note = "  (self-test only: no positive corpus)"
        elif n == 0 and name in MUST_MATCH:
            note = "  <-- DEAD"
        else:
            note = ""
        print(f"    {name:24s} {n:4d}{note}")


if __name__ == "__main__":
    sys.exit(main())
