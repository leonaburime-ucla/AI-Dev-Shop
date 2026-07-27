#!/usr/bin/env python3
"""Executable reference implementation of every gate predicate in the harness.

WHY THIS FILE EXISTS
--------------------
The gate rules used to live only in markdown prose. Across three review rounds
the duplication predicate alone was wrong three times in three different ways,
each fix breaking a neighbouring case, and every reviewer read prose that
"looked right." Prose cannot be executed, so nothing caught the arithmetic.

This module is the normative definition of the arithmetic. The sensor docs
describe intent, worked examples, and tooling; **when prose and this file
disagree about what a gate computes, this file is correct and the prose is a
defect.** `test_reference.py` holds the case tables, including a regression case
for every historical bug so none can return silently.

Hosts may port these predicates; the toolkit itself runs no metrics.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# --------------------------------------------------------------------------
# Shared vocabulary
# --------------------------------------------------------------------------

PASS = "PASS"
REVIEW = "REVIEW"
BREACH = "BREACH"
INCONCLUSIVE = "INCONCLUSIVE"
INACTIVE = "INACTIVE"

REQUIRED = "REQUIRED"
RECOMMENDED = "RECOMMENDED"
NO_RECORDED_FINDINGS = "NO_RECORDED_FINDINGS"

# Gate validation states, per harness-engineering/quality/gate-validation-status.md.
# Deliberately NOT named advisory/blocking -- those words mean per-rule severity
# in architecture-fitness.md and the collision caused a real misreading.
UNVALIDATED = "unvalidated"
VALIDATED = "validated"


# Mirrors the closed set in
# `<AI_DEV_SHOP_ROOT>/harness-engineering/quality/gate-validation-status.md`.
# The registry OWNS this set; this is a duplicate kept in sync by
# `validate_harness_consistency.py`'s integrity-set parity check, because a
# hand-maintained second copy is the "two copies drift" defect this harness
# raises against sensors.
CANONICAL_INTEGRITY_IDS = frozenset(f"INT-{n}" for n in range(1, 10))  # INT-1..INT-9


def apply_status_cap(
    disposition: str,
    gate_status: str,
    integrity_id: Optional[str] = None,
) -> str:
    """Cap REQUIRED to RECOMMENDED while a gate is unvalidated.

    Canonical integrity findings are never capped -- they are findings about the
    measurement itself, not threshold judgments, so their correctness does not
    depend on an unvalidated band.

    Takes an **ID validated against the closed set**, not a boolean. An earlier
    version accepted `is_integrity: bool`, which meant any caller could uncap any
    finding by passing True -- the normative implementation could not tell a
    registered ID from an invented local exemption, while the registry it
    implements says the set is closed. An unknown ID raises rather than silently
    uncapping; failing loudly is the only safe direction here.
    """
    if integrity_id is not None:
        if integrity_id not in CANONICAL_INTEGRITY_IDS:
            raise ValueError(
                f"{integrity_id!r} is not in the closed integrity set "
                f"{sorted(CANONICAL_INTEGRITY_IDS)}; sensors may not invent exemptions"
            )
        return disposition
    if gate_status == VALIDATED:
        return disposition
    if disposition == REQUIRED:
        return RECOMMENDED
    return disposition


# --------------------------------------------------------------------------
# Metrics 1 + 3 -- cognitive complexity and nesting depth
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class ComplexityBands:
    review_low: int
    gate: int


COGNITIVE = ComplexityBands(review_low=11, gate=15)   # review 11-15, breach 16+
NESTING = ComplexityBands(review_low=4, gate=4)       # review 4, breach 5+


MEASURED = "measured"
BELOW_REPORTING_THRESHOLD = "below_reporting_threshold"


def complexity_gate(
    head: Optional[int],
    base: Optional[int],
    is_new: bool,
    bands: ComplexityBands,
    detector_declared: bool = True,
    value_source: str = MEASURED,
    reporting_threshold: Optional[int] = None,
    reporting_operator: str = ">",
) -> str:
    """Delta-gated structural complexity.

    BREACH = head > gate AND (function is new OR head > base)

    A missing value is never PASS. It is INACTIVE when no detector exists for
    the stack, and INCONCLUSIVE when a detector was declared but produced
    nothing -- two different states that an earlier draft collapsed, which would
    have left every non-JS/TS repo permanently unresolved.
    """
    if head is None:
        # Three different reasons a value can be absent, and they are NOT the
        # same verdict. A threshold linter configured at the band's lower edge
        # emits nothing for a clean function: the tool ran correctly and the
        # value is provably under the band, so that is a PASS. Detector silence
        # for any other reason is unresolved, and no detector at all is INACTIVE.
        if value_source == BELOW_REPORTING_THRESHOLD:
            # Silence proves the value is under the band ONLY if we know the
            # highest value the tool would NOT have reported. That depends on the
            # threshold AND the comparison operator, which differ across tools:
            # eslint/pylint/gocognit/clippy report on `> N` (so silence means
            # <= N), while PMD's CognitiveComplexity reports on `>= N` (silence
            # means <= N-1). Recording the threshold without the operator made a
            # correctly-configured PMD at reportLevel 11 permanently
            # INCONCLUSIVE -- trading a wrong-PASS for a dead gate on Java.
            #
            # An unconfigured clippy (default 25) or PMD (default 15) still says
            # nothing about a real breach, so an unknown threshold stays
            # INCONCLUSIVE: that silence is INT-8 if reported as PASS.
            if reporting_threshold is None:
                return INCONCLUSIVE
            highest_unreported = (
                reporting_threshold if reporting_operator == ">"
                else reporting_threshold - 1
            )
            if highest_unreported < bands.review_low:
                return PASS
            return INCONCLUSIVE
        return INCONCLUSIVE if detector_declared else INACTIVE
    if not is_new and base is None:
        # Unresolvable base match. Never "treat it as a new function".
        return INCONCLUSIVE
    if head > bands.gate and (is_new or head > base):
        return BREACH
    if head >= bands.review_low:
        return REVIEW
    return PASS


# --------------------------------------------------------------------------
# Metric 6 -- duplication
# --------------------------------------------------------------------------

MIN_TOKENS = 50
MIN_LINES = 5
RULE_OF_THREE = 3


def duplication_gate(
    base_occurrences: int,
    head_occurrences: int,
    tokens: int,
    lines: int,
    clone_type: int,
    site_in_changed_scope: bool,
    relocated: bool = False,
    min_tokens: int = MIN_TOKENS,
    min_lines: int = MIN_LINES,
) -> bool:
    """True when a clone group breaches.

    BREACH = type in {1,2}
             AND a site is in changed scope
             AND size >= thresholds
             AND head_occurrences > base_occurrences
             AND head_occurrences >= 3

    The growth condition is what took three attempts to get right:

      v1  "group not present at base"  -> a 2-site group IS present, so the
                                          third-site catch could never fire.
      v2  "base_occurrences < 3"       -> 3 < 3 is false, so a 3-site group
                                          could grow to 5 without breaching.
      v3  "head > base AND head >= 3"  -> fires on any growth past the rule of
                                          three, from any starting count.

    Relocation only excuses a group whose site count did NOT grow. Without that
    condition, "I moved a file" becomes an argument template against the gate.
    """
    if clone_type not in (1, 2):
        return False
    if not site_in_changed_scope:
        return False
    if tokens < min_tokens or lines < min_lines:
        return False
    # `relocated` is a REPORTING label, not a gate input. It is deliberately not
    # consulted here: `head == base` already fails the growth condition below, so
    # a relocation carve-out could only ever excuse something the arithmetic
    # already excuses. An earlier version branched on it, which was dead code and
    # made its own regression test half-vacuous. Any site-count increase is
    # evaluated on growth regardless of how many sites moved.
    return head_occurrences > base_occurrences and head_occurrences >= RULE_OF_THREE


# --------------------------------------------------------------------------
# Metric 9 -- changed-code coverage
# --------------------------------------------------------------------------

COVERAGE_FLOOR = 0.80
MIN_BRANCHES_TO_GATE = 5
# Any branch that never executed is a finding. An earlier value of 3 was meant to
# suppress noise on tiny units, but it let a 1- or 2-branch unit at 0% branch
# coverage pass whenever the surrounding LINES were covered -- which is exactly
# the one-arm-covered case this sensor exists to catch, excused by an unrelated
# signal. Fourth position this escape band has occupied; the floor is now 1.
ZERO_RULE_MIN_BRANCHES = 1
LINE_FALLBACK_MIN_LINES = 15


def coverage_gate(
    branches_total: Optional[int],
    branches_covered: Optional[int],
    lines_total: int,
    lines_covered: int,
    floor: float = COVERAGE_FLOOR,
) -> bool:
    """True when a changed unit (file or aggregate) breaches the coverage floor.

    Evaluated absolutely on the diff, not delta-gated: this metric measures only
    code the change touched, so there is no legacy portion to grandfather.

    The small-unit path is the part that was wrong. An earlier draft said units
    under the branch minimum "report it, do not gate it", which let 4-branch
    functions land at 0%. The fix routed them to the line rule -- but the line
    rule carried its own 15-line minimum, so a 4-branch / 12-line unit at 25%
    still escaped every trigger. Small units now fall back to the line ratio
    with NO line minimum; the 15-line minimum applies only to genuinely
    branch-null tooling, where there is no branch signal to fall back from.
    """
    have_branches = branches_total is not None and branches_covered is not None

    if have_branches and branches_total == 0:
        # Branch data exists and this unit simply has no branches (straight-line
        # code). It is a SMALL UNIT, not branch-null tooling, so the line rule
        # applies with no minimum. Routing it to the branch-null path let a
        # 14-line wholly untested helper escape while a 1-branch/6-line unit
        # gated -- one branch fewer, weaker gate.
        if lines_total > 0:
            return (lines_covered / lines_total) < floor
        return False

    if have_branches and branches_total > 0:
        ratio = branches_covered / branches_total
        if branches_total >= MIN_BRANCHES_TO_GATE:
            return ratio < floor
        # Small unit: zero-rule first, then an unconditional line fallback.
        # The zero rule is absolute -- no branch count excuses a branch that was
        # never taken, and line coverage must not launder it.
        if ratio == 0 and branches_total >= ZERO_RULE_MIN_BRANCHES:
            return True
        if lines_total > 0:
            return (lines_covered / lines_total) < floor
        return False

    # Branch-null tooling: line fallback, with the size minimum.
    if lines_total >= LINE_FALLBACK_MIN_LINES:
        return (lines_covered / lines_total) < floor
    return False


# --------------------------------------------------------------------------
# Metrics 11 + 12 -- change history tiers
# --------------------------------------------------------------------------

CHANGE_FREQUENCY_PERCENTILE = 0.75


def percentile_threshold(values: list[int], percentile: float = CHANGE_FREQUENCY_PERCENTILE) -> float:
    """Cut point for 'high' relative to this repository.

    Files with zero activity are excluded by the caller so they cannot drag the
    quartile down. Absolute commit counts are meaningless across repos, which is
    why the cut is relative.
    """
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = int(round(percentile * (len(ordered) - 1)))
    return float(ordered[idx])


def hotspot_tier(is_high_change_frequency: bool, above_complexity_band: bool) -> str:
    """T0 refactor first, T1 watch, T2 usually leave alone, T3 ignore.

    The tier input is **change frequency** (distinct commits touching the file),
    NOT churn (lines added + deleted). change-history.md documents that naming
    this "churn" defeated tier reproducibility; an earlier version of this module
    re-committed that exact conflation in its parameter name while formally
    outranking the prose that fixed it.

    Ordered tiers rather than a weighted score: the weights in the source
    research are assumed, and calibrating them needs an outcome dataset this
    harness does not collect.
    """
    if is_high_change_frequency and above_complexity_band:
        return "T0"
    if is_high_change_frequency:
        return "T1"
    if above_complexity_band:
        return "T2"
    return "T3"


# --------------------------------------------------------------------------
# Historical predicates -- kept ONLY so tests can prove they were wrong
# --------------------------------------------------------------------------

def _duplication_predicate_v1(base_occurrences: int, head_occurrences: int) -> bool:
    """Round-1 formulation: 'group is not present in the merge base'."""
    return base_occurrences == 0 and head_occurrences >= RULE_OF_THREE


def _duplication_predicate_v2(base_occurrences: int, head_occurrences: int) -> bool:
    """Round-2 formulation: 'base_occurrences < 3'."""
    return base_occurrences < RULE_OF_THREE and head_occurrences >= RULE_OF_THREE
