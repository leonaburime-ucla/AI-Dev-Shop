#!/usr/bin/env python3
"""Case tables for every gate predicate, plus a regression case per historical bug.

Run: python3 -m pytest harness-engineering/gate-logic/ -q

Every `test_regression_*` corresponds to a defect a peer reviewer found in a
real review round. They are named so that if one starts failing, the failure
message says which bug came back.
"""
from __future__ import annotations

import pytest

from reference import (
    BREACH,
    COGNITIVE,
    INACTIVE,
    INCONCLUSIVE,
    NESTING,
    PASS,
    CANONICAL_INTEGRITY_IDS,
    NO_RECORDED_FINDINGS,
    RECOMMENDED,
    REQUIRED,
    REVIEW,
    UNVALIDATED,
    VALIDATED,
    BELOW_REPORTING_THRESHOLD,
    CHANGE_FREQUENCY_PERCENTILE,
    COVERAGE_FLOOR,
    LINE_FALLBACK_MIN_LINES,
    MIN_BRANCHES_TO_GATE,
    MIN_LINES,
    MIN_TOKENS,
    RULE_OF_THREE,
    ZERO_RULE_MIN_BRANCHES,
    _duplication_predicate_v1,
    _duplication_predicate_v2,
    apply_status_cap,
    complexity_gate,
    coverage_gate,
    duplication_gate,
    hotspot_tier,
    percentile_threshold,
)


# ==========================================================================
# Duplication -- wrong three times, so it gets the densest table
# ==========================================================================

@pytest.mark.parametrize(
    "base,head,expected,why",
    [
        (0, 3, True, "new 3-site group"),
        (2, 3, True, "the rule-of-three crossing -- the central catch"),
        (3, 4, True, "growth past three still gates"),
        (3, 5, True, "large growth from an already-breaching group"),
        (0, 2, False, "two sites is a warning, never a gate"),
        (2, 2, False, "touched but not duplicated further"),
        (3, 3, False, "editing duplicated code is not duplicating code"),
        (4, 3, False, "shrinking a clone group is an improvement"),
        (0, 1, False, "a single occurrence is not a clone"),
    ],
)
def test_duplication_growth_table(base, head, expected, why):
    assert duplication_gate(
        base_occurrences=base,
        head_occurrences=head,
        tokens=60,
        lines=10,
        clone_type=1,
        site_in_changed_scope=True,
    ) is expected, why


def test_regression_r1_v1_predicate_missed_the_third_site():
    """Round 1 shipped 'group not present at base'. A 2-site group IS present,
    so the third-site catch -- the entire point of the gate -- never fired."""
    assert _duplication_predicate_v1(base_occurrences=2, head_occurrences=3) is False
    assert duplication_gate(2, 3, 60, 10, 1, True) is True


def test_regression_r2_v2_predicate_missed_the_fourth_site():
    """Round 2 fixed v1 with 'base_occurrences < 3', but 3 < 3 is false, so a
    3-site group could be copied to 5 without breaching."""
    assert _duplication_predicate_v2(base_occurrences=3, head_occurrences=5) is False
    assert duplication_gate(3, 5, 60, 10, 1, True) is True


def test_regression_r3_relocation_cannot_swallow_growth():
    """Round 3: the relocation carve-out had no growth condition, so a diff that
    moved one site while adding another could be argued as 'just relocated'.

    Round 4: the first assertion here was tautological -- `relocated` never
    changed any output, because head == base already fails the growth condition.
    It is now asserted explicitly: the flag must be inert in BOTH directions, so
    no future edit can reintroduce it as a live excuse."""
    # Moved AND grew -> the gate fires regardless of the flag.
    assert duplication_gate(2, 3, 60, 10, 1, True, relocated=True) is True
    # The flag is inert: identical results with and without it, every combination.
    for base, head in [(0, 3), (2, 3), (3, 4), (2, 2), (3, 3), (4, 3)]:
        assert (duplication_gate(base, head, 60, 10, 1, True, relocated=True)
                is duplication_gate(base, head, 60, 10, 1, True, relocated=False)), (
            f"relocated changed the outcome at {base}->{head}; it must be a "
            "reporting label, never a gate input")


@pytest.mark.parametrize(
    "tokens,lines,expected",
    [(60, 10, True), (49, 10, False), (60, 4, False), (50, 5, True)],
)
def test_duplication_size_thresholds(tokens, lines, expected):
    assert duplication_gate(2, 3, tokens, lines, 1, True) is expected


@pytest.mark.parametrize("clone_type,expected", [(1, True), (2, True), (3, False), (4, False)])
def test_duplication_only_types_1_and_2_gate(clone_type, expected):
    """Type-3 is reported, never gated -- tool agreement on gap thresholds is poor."""
    assert duplication_gate(2, 3, 60, 10, clone_type, True) is expected


def test_duplication_requires_a_site_in_changed_scope():
    assert duplication_gate(2, 3, 60, 10, 1, site_in_changed_scope=False) is False


def test_raising_the_threshold_hides_a_real_clone():
    """Why loosening a declared threshold is INT-2 rather than a tuning choice."""
    assert duplication_gate(2, 3, 60, 10, 1, True, min_tokens=50) is True
    assert duplication_gate(2, 3, 60, 10, 1, True, min_tokens=100) is False


# ==========================================================================
# Cognitive complexity and nesting
# ==========================================================================

@pytest.mark.parametrize(
    "head,base,is_new,expected,why",
    [
        (20, 20, False, REVIEW, "unchanged legacy above band never blocks"),
        (18, 20, False, REVIEW, "improved but still above band -- no block, no credit"),
        (21, 20, False, BREACH, "worsened above the gate"),
        (16, None, True, BREACH, "new function faces the absolute gate"),
        (16, 14, False, BREACH, "crossed the gate this change"),
        (14, 14, False, REVIEW, "inside the review band"),
        (9, 9, False, PASS, "clean"),
        (9, None, True, PASS, "new and clean"),
    ],
)
def test_cognitive_delta_table(head, base, is_new, expected, why):
    assert complexity_gate(head, base, is_new, COGNITIVE) == expected, why


def test_regression_missing_value_is_never_pass():
    """The activation trap: a detector that never ran must not read as clean."""
    assert complexity_gate(None, None, True, NESTING, detector_declared=True) == INCONCLUSIVE
    assert complexity_gate(None, None, True, NESTING, detector_declared=False) == INACTIVE
    assert complexity_gate(None, None, True, NESTING) != PASS


def test_regression_r3_inactive_and_inconclusive_are_distinct():
    """Round 3: collapsing these left every non-JS/TS repo permanently
    unresolved on every PR, which trains agents to ignore the field."""
    no_detector = complexity_gate(None, None, True, NESTING, detector_declared=False)
    declared_but_silent = complexity_gate(None, None, True, NESTING, detector_declared=True)
    assert no_detector == INACTIVE
    assert declared_but_silent == INCONCLUSIVE
    assert no_detector != declared_but_silent


def test_unresolvable_base_is_inconclusive_not_new():
    """A rename that Git cannot follow must not be laundered into 'new function'."""
    assert complexity_gate(20, None, is_new=False, bands=COGNITIVE) == INCONCLUSIVE


def test_nesting_bands():
    assert complexity_gate(5, 3, False, NESTING) == BREACH
    assert complexity_gate(4, 4, False, NESTING) == REVIEW
    assert complexity_gate(3, 3, False, NESTING) == PASS


def test_exhaustive_switch_shape_does_not_breach_cognitive():
    """A 14-arm exhaustive switch scores cyclomatic ~15 but cognitive ~1.
    Gating on cyclomatic would hard-fail an idiom this toolkit mandates."""
    assert complexity_gate(1, None, True, COGNITIVE) == PASS


# ==========================================================================
# Changed-code coverage
# ==========================================================================

@pytest.mark.parametrize(
    "bt,bc,lt,lc,expected,why",
    [
        (10, 9, 40, 38, False, "90% branch, above floor"),
        (10, 7, 40, 30, True, "70% branch, below floor"),
        (10, 8, 40, 32, False, "exactly at the floor passes"),
        (0, 0, 0, 0, False, "comment-only diff -- negative control"),
        (None, None, 40, 20, True, "branch-null tooling, line ratio below floor"),
        (None, None, 10, 2, False, "branch-null and under the 15-line minimum"),
    ],
)
def test_coverage_table(bt, bc, lt, lc, expected, why):
    assert coverage_gate(bt, bc, lt, lc) is expected, why


def test_regression_r3_small_unit_escape_band():
    """Round 3: units under the 5-branch minimum fell through to the line rule,
    but the line rule carried its own 15-line minimum -- so a 4-branch, 12-line
    unit at 25% coverage triggered nothing, while the prose claimed
    'Nothing escapes by being small.'"""
    assert coverage_gate(branches_total=4, branches_covered=1, lines_total=12, lines_covered=3) is True


def test_regression_r3_two_branches_at_zero_under_line_minimum():
    """Same band, the other corner. NOTE: when written, the zero rule had a
    3-branch floor and this case was caught by the line fallback. The floor moved
    to 1 in round 7, so it is now caught by the zero rule directly. The assertion
    is unchanged and still correct; only the route changed."""
    assert coverage_gate(branches_total=2, branches_covered=0, lines_total=14, lines_covered=0) is True


def test_small_well_covered_unit_still_passes():
    """The escape-band fix must not turn every tiny diff into a finding."""
    assert coverage_gate(branches_total=2, branches_covered=2, lines_total=6, lines_covered=6) is False


def test_denominator_padding_is_invisible_to_the_aggregate():
    """Why per-file ratios are mandatory: padding lifts the total while the new
    logic stays untested. The aggregate passes; the file must still fail."""
    assert coverage_gate(100, 96, 300, 290) is False          # aggregate, padded
    assert coverage_gate(8, 0, 30, 0) is True                 # the real file


# ==========================================================================
# Status cap and integrity exemption
# ==========================================================================

def test_unvalidated_caps_required_to_recommended():
    assert apply_status_cap(REQUIRED, UNVALIDATED) == RECOMMENDED
    assert apply_status_cap(REQUIRED, VALIDATED) == REQUIRED


def test_integrity_findings_are_never_capped():
    """A harness whose anti-gaming rules were also advisory would have none."""
    for n in range(1, 10):
        assert apply_status_cap(REQUIRED, UNVALIDATED, integrity_id=f"INT-{n}") == REQUIRED


def test_regression_r4_uncapping_requires_a_registered_id():
    """Round 4: the cap took a caller-controlled boolean, so any caller could
    uncap any finding -- the normative implementation could not distinguish a
    registered ID from an invented local exemption."""
    with pytest.raises(ValueError):
        apply_status_cap(REQUIRED, UNVALIDATED, integrity_id="INT-10")
    with pytest.raises(ValueError):
        apply_status_cap(REQUIRED, UNVALIDATED, integrity_id="INT-REVIEWER-DISAGREEMENT")
    assert apply_status_cap(REQUIRED, UNVALIDATED) == RECOMMENDED


def test_regression_r4_below_threshold_passes_but_silence_does_not():
    """Round 4: a threshold linter at the band's lower edge emits nothing for a
    clean function -- that is a provable PASS. Detector silence for any other
    reason is not, and collapsing them would mark every conforming run
    unresolved."""
    assert complexity_gate(None, None, True, COGNITIVE,
                           value_source=BELOW_REPORTING_THRESHOLD,
                           reporting_threshold=10) == PASS
    # Round 5: the PASS used to be unconditional, which made an unconfigured
    # clippy (default 25) or PMD (default 15) run report a real breach as clean.
    assert complexity_gate(None, None, True, COGNITIVE,
                           value_source=BELOW_REPORTING_THRESHOLD,
                           reporting_threshold=25) == INCONCLUSIVE
    assert complexity_gate(None, None, True, COGNITIVE,
                           value_source=BELOW_REPORTING_THRESHOLD) == INCONCLUSIVE
    # Round 6: the comparison was `<=`, so a threshold EQUAL to review_low
    # returned PASS -- but review_low is inclusive-REVIEW, so silence there is
    # consistent with a real review-band value. Rust was configured at exactly
    # this boundary, making it a live wrong-PASS.
    assert complexity_gate(None, None, True, NESTING,
                           value_source=BELOW_REPORTING_THRESHOLD,
                           reporting_threshold=NESTING.review_low) == INCONCLUSIVE
    assert complexity_gate(None, None, True, NESTING,
                           value_source=BELOW_REPORTING_THRESHOLD,
                           reporting_threshold=NESTING.review_low - 1) == PASS


def test_regression_r6_threshold_needs_its_comparison_operator():
    """Round 6: recording the threshold without the operator broke Java.

    PMD's CognitiveComplexity reports on `>= reportLevel`, not `> N` like every
    other tool here. That is exactly why the doc sets PMD to 11 and the strict-`>`
    tools to 10 -- but a bare `threshold < review_low` test then made a correctly
    configured PMD run permanently INCONCLUSIVE for every clean Java function."""
    # PMD at reportLevel 11 with `>=`: silence means <= 10, provably under the band.
    assert complexity_gate(None, None, True, COGNITIVE,
                           value_source=BELOW_REPORTING_THRESHOLD,
                           reporting_threshold=11, reporting_operator=">=") == PASS
    # The same 11 under strict `>` means silence only proves <= 11 -- not enough.
    assert complexity_gate(None, None, True, COGNITIVE,
                           value_source=BELOW_REPORTING_THRESHOLD,
                           reporting_threshold=11, reporting_operator=">") == INCONCLUSIVE
    # Unconfigured PMD (default 15) is still INCONCLUSIVE under either operator.
    assert complexity_gate(None, None, True, COGNITIVE,
                           value_source=BELOW_REPORTING_THRESHOLD,
                           reporting_threshold=15, reporting_operator=">=") == INCONCLUSIVE
    assert complexity_gate(None, None, True, COGNITIVE) == INCONCLUSIVE
    assert complexity_gate(None, None, True, COGNITIVE,
                           detector_declared=False) == INACTIVE


def test_regression_r4_zero_branch_unit_is_small_not_branch_null():
    """Round 4: a branchless changed unit routed to the branch-null path and its
    15-line minimum, so a 14-line wholly untested helper escaped while a
    1-branch/6-line unit gated. One branch fewer must not mean a weaker gate."""
    assert coverage_gate(0, 0, 14, 0) is True
    assert coverage_gate(1, 0, 6, 0) is True
    assert coverage_gate(0, 0, 14, 14) is False


# ==========================================================================
# Constant pinning -- every threshold at / below / above.
# Round 4: Codex mutated MIN_BRANCHES_TO_GATE=6, ZERO_RULE_MIN_BRANCHES=4,
# LINE_FALLBACK_MIN_LINES=11, COGNITIVE.gate=14 and review_low=10, and every
# mutation survived. The predicates were tested; the constants were not.
# ==========================================================================

def test_regression_r5_operator_mutants_at_the_gate_edge():
    """Round 5: three `>=`/`>` operator mutants survived all 62 tests, because
    every at-boundary case was built with the OTHER clause of the compound
    condition already false, so the operator under test was never exercised.

    `head > bands.gate` -> `>=` survived: the only head==gate case had
    base==head and is_new=False, short-circuiting the delta clause. A NEW
    function at exactly the gate is the case that distinguishes them."""
    assert complexity_gate(15, None, True, COGNITIVE) == REVIEW    # new, at gate
    assert complexity_gate(15, 12, False, COGNITIVE) == REVIEW     # worsened, at gate
    assert complexity_gate(16, None, True, COGNITIVE) == BREACH    # new, one over
    assert complexity_gate(4, None, True, NESTING) == REVIEW       # new, at gate
    assert complexity_gate(5, None, True, NESTING) == BREACH


def test_regression_r5_coverage_boundary_operators():
    """Round 5: `branches_total >= MIN_BRANCHES_TO_GATE` -> `>` and
    `>= ZERO_RULE_MIN_BRANCHES` -> `>` both survived.

    The 5-branch cases were built with the line ratio numerically equal to the
    branch ratio, so both code paths returned the same verdict and the boundary
    was exercised but never DISTINGUISHED. And branches_total == 3 -- then the
    zero rule's edge -- was never called at all: the data jumped 2 -> 4.
    (The zero-rule floor has since moved to 1; 3 is no longer the edge, but these
    cases remain valid pins on the 5-branch gating boundary.)"""
    # 5 branches at 60% but 90% lines: only the branch path gates it.
    assert coverage_gate(5, 3, 20, 18) is True
    # Exactly 3 branches at 0%: with no line escape.
    assert coverage_gate(3, 0, 0, 0) is True
    assert coverage_gate(3, 0, 20, 18) is True


def test_regression_r5_percentile_rounding_is_pinned():
    """Round 5: `int(round(...))` -> `int(...)` survived, and round()'s
    half-to-even makes the quartile index non-monotonic at .5 cases."""
    assert percentile_threshold([1, 2, 3]) == 3.0        # idx 1.5 -> rounds up
    assert percentile_threshold(list(range(1, 8))) == 5.0
    assert percentile_threshold([1, 2, 3, 4, 5]) == 4.0


def test_pin_cognitive_band_edges():
    assert COGNITIVE.review_low == 11 and COGNITIVE.gate == 15
    assert complexity_gate(10, 10, False, COGNITIVE) == PASS      # below band
    assert complexity_gate(11, 11, False, COGNITIVE) == REVIEW    # at band edge
    assert complexity_gate(15, 15, False, COGNITIVE) == REVIEW    # at gate
    assert complexity_gate(16, None, True, COGNITIVE) == BREACH   # above gate


def test_pin_nesting_band_edges():
    assert NESTING.review_low == 4 and NESTING.gate == 4
    assert complexity_gate(3, 3, False, NESTING) == PASS
    assert complexity_gate(4, 4, False, NESTING) == REVIEW
    assert complexity_gate(5, None, True, NESTING) == BREACH


def test_pin_duplication_constants():
    assert RULE_OF_THREE == 3 and MIN_TOKENS == 50 and MIN_LINES == 5
    assert duplication_gate(1, 2, 60, 10, 1, True) is False   # below rule of three
    assert duplication_gate(2, 3, 60, 10, 1, True) is True    # at it
    assert duplication_gate(2, 3, 50, 5, 1, True) is True     # exactly at size floor
    assert duplication_gate(2, 3, 49, 5, 1, True) is False    # one token under
    assert duplication_gate(2, 3, 50, 4, 1, True) is False    # one line under


def test_pin_coverage_constants():
    assert COVERAGE_FLOOR == 0.80
    assert MIN_BRANCHES_TO_GATE == 5
    assert ZERO_RULE_MIN_BRANCHES == 1
    assert LINE_FALLBACK_MIN_LINES == 15
    assert coverage_gate(5, 4, 20, 16) is False               # exactly at floor
    assert coverage_gate(5, 3, 20, 12) is True                # just under
    assert coverage_gate(4, 0, 0, 0) is True                  # zero rule
    assert coverage_gate(1, 0, 0, 0) is True                  # one untaken branch is enough
    assert coverage_gate(None, None, 15, 0) is True           # branch-null at minimum
    assert coverage_gate(None, None, 14, 0) is False          # one line under


def test_regression_r6_every_line_ratio_floor_is_pinned():
    """Round 6: `< floor` -> `<= floor` survived on all THREE line-ratio paths.
    The at-the-floor case was asserted only on the branch ratio and assumed on
    the rest -- the same one-path-tested, others-assumed shape as round 5."""
    assert coverage_gate(0, 0, 20, 16) is False       # zero-branch path, at floor
    assert coverage_gate(4, 1, 20, 16) is False       # small-unit fallback, at floor
    assert coverage_gate(None, None, 20, 16) is False  # branch-null fallback, at floor
    assert coverage_gate(0, 0, 20, 15) is True        # just under, each path
    assert coverage_gate(4, 1, 20, 15) is True
    assert coverage_gate(None, None, 20, 15) is True


def test_regression_r6_zero_rule_is_equality_not_a_low_ratio():
    """Round 6: `ratio == 0` -> `ratio <= 0.3` survived, because no test used a
    small unit with a nonzero-but-low branch ratio."""
    assert coverage_gate(4, 1, 100, 100) is False     # 25% branches, fully covered lines
    assert coverage_gate(4, 0, 100, 100) is True      # genuinely zero


def test_regression_r6_reporting_threshold_pins_review_low_not_gate():
    """Round 6: `< bands.review_low` -> `< bands.gate` survived; nothing tested a
    threshold between the band edge and the gate."""
    for thr in (11, 12, 13, 14, 15):
        assert complexity_gate(None, None, True, COGNITIVE,
                               value_source=BELOW_REPORTING_THRESHOLD,
                               reporting_threshold=thr) == INCONCLUSIVE, thr
    assert complexity_gate(None, None, True, COGNITIVE,
                           value_source=BELOW_REPORTING_THRESHOLD,
                           reporting_threshold=10) == PASS


def test_regression_r7_ge_operator_arithmetic_is_pinned():
    """Round 7: `reporting_threshold - 1` -> `- 2` survived. The `>=` path was
    exercised only at 11 and 15, and 11 is the single value where -1 and -2
    agree. The sweep that does cover 12-14 uses the DEFAULT `>` operator, so it
    never touches this branch."""
    # PMD at 12 with `>=`: silence proves only <= 11, which is inside the band.
    assert complexity_gate(None, None, True, COGNITIVE,
                           value_source=BELOW_REPORTING_THRESHOLD,
                           reporting_threshold=12, reporting_operator=">=") == INCONCLUSIVE
    assert complexity_gate(None, None, True, COGNITIVE,
                           value_source=BELOW_REPORTING_THRESHOLD,
                           reporting_threshold=13, reporting_operator=">=") == INCONCLUSIVE
    # 11 is the highest `>=` threshold that proves the value is under the band.
    assert complexity_gate(None, None, True, COGNITIVE,
                           value_source=BELOW_REPORTING_THRESHOLD,
                           reporting_threshold=11, reporting_operator=">=") == PASS


def test_regression_r7_partial_branch_data_degrades_gracefully():
    """Round 7: `branches_total is not None and branches_covered is not None`
    -> `or` survived; no test supplied half-present branch data. A coverage tool
    emitting totals without covered counts is a real output shape, and under the
    mutant it raises TypeError instead of falling back to the line rule."""
    assert coverage_gate(10, None, 40, 20) is True    # falls back to lines
    assert coverage_gate(None, 5, 40, 36) is False    # falls back, above floor


def test_regression_r7_untaken_branch_is_never_excused_by_line_coverage():
    """Round 7: a 1- or 2-branch unit at 0% branch coverage passed whenever the
    surrounding lines were covered, because the zero rule had a 3-branch floor.

    A branch that never executed is the one-arm-covered case this sensor exists
    to catch. Line coverage is a different signal and must not launder it. The
    doc's own worked corner claimed this shape was a finding while the code let
    it through -- the fourth position this escape band has occupied."""
    assert coverage_gate(1, 0, 10, 10) is True
    assert coverage_gate(2, 0, 20, 20) is True
    assert coverage_gate(2, 0, 14, 14) is True   # the doc's worked-corner shape
    assert coverage_gate(2, 0, 14, 0) is True
    # A covered small unit is still clean -- the fix must not flag everything.
    assert coverage_gate(2, 2, 20, 20) is False
    assert coverage_gate(1, 1, 10, 10) is False


def test_regression_r9_line_fallback_pinned_when_no_line_data():
    """Round 9: the small-unit line fallback was unpinned at lines_total == 0.
    `> 0` -> `>= 0` raises ZeroDivisionError; `return False` -> `True` makes every
    such unit a finding. Branch data present with line data absent is a real tool
    output shape -- the same partial-data class round 7 closed for have_branches.
    The corner was pinned on two of the three line-ratio paths and assumed on the
    third, which is the exact shape round 6's floor test calls out."""
    assert coverage_gate(4, 1, 0, 0) is False    # small unit, no line data
    assert coverage_gate(2, 1, 0, 0) is False
    assert coverage_gate(0, 0, 1, 0) is True     # 1 uncovered line, no branches
    assert coverage_gate(0, 0, 1, 1) is False


def test_regression_r9_int_zero_is_not_in_the_closed_set():
    """Round 9: `range(1, 10)` -> `range(0, 10)` passed all 74 tests, admitting
    INT-0 to the closed integrity set so `apply_status_cap` would uncap on it.
    The validator catches this only as an accident of the literal `1,` in its
    regex, and reports a misleading message when it does."""
    assert "INT-0" not in CANONICAL_INTEGRITY_IDS
    assert CANONICAL_INTEGRITY_IDS == {f"INT-{n}" for n in range(1, 10)}
    with pytest.raises(ValueError):
        apply_status_cap(REQUIRED, UNVALIDATED, integrity_id="INT-0")


def test_pin_percentile_exactly():
    """An earlier version asserted only quiet < busy, which any monotone
    statistic satisfies -- max, mean and median all pass it."""
    assert CHANGE_FREQUENCY_PERCENTILE == 0.75
    assert percentile_threshold([1, 2, 3, 4, 5]) == 4.0
    assert percentile_threshold([10, 20, 30, 40]) == 30.0
    assert percentile_threshold([7]) == 7.0
    assert percentile_threshold([]) == 0.0


def test_regression_r8_cap_leaves_non_required_dispositions_alone():
    """Round 8: forcing `if disposition == REQUIRED` to True survived all 72
    tests -- NO_RECORDED_FINDINGS had zero call sites, and the only guard used
    VALIDATED, which returns at an earlier branch and never reaches this line.
    Under the mutant the cap invents a RECOMMENDED where the sensor recorded
    nothing."""
    assert apply_status_cap(NO_RECORDED_FINDINGS, UNVALIDATED) == NO_RECORDED_FINDINGS
    assert apply_status_cap(RECOMMENDED, UNVALIDATED) == RECOMMENDED
    assert apply_status_cap(INCONCLUSIVE, UNVALIDATED) == INCONCLUSIVE


def test_regression_r8_historical_predicates_are_faithful_reproductions():
    """Round 8: both historical predicates were pinned only on their False side,
    one assertion each -- so a constant-`False` stub would pass both regression
    tests. Eight surviving mutants lived here. They exist to prove the old rules
    were wrong, which requires they still BE the old rules."""
    # v1 fired only on a genuinely new group; that is what made it miss the third site.
    assert _duplication_predicate_v1(0, 3) is True
    assert _duplication_predicate_v1(2, 3) is False
    assert _duplication_predicate_v1(0, 2) is False
    # v2 fired below a base of three; that is what made it miss the fourth site.
    assert _duplication_predicate_v2(0, 3) is True
    assert _duplication_predicate_v2(2, 3) is True
    assert _duplication_predicate_v2(3, 5) is False


def test_cap_does_not_promote():
    assert apply_status_cap(RECOMMENDED, VALIDATED) == RECOMMENDED


# ==========================================================================
# Change history tiers
# ==========================================================================

def test_percentile_is_repo_relative():
    """20 commits is high for a stable library and low for an active service."""
    quiet = percentile_threshold([1, 1, 2, 2, 3])
    busy = percentile_threshold([10, 20, 30, 40, 50])
    assert quiet < busy


@pytest.mark.parametrize(
    "high_churn,above_band,expected",
    [(True, True, "T0"), (True, False, "T1"), (False, True, "T2"), (False, False, "T3")],
)
def test_hotspot_tiers(high_churn, above_band, expected):
    assert hotspot_tier(high_churn, above_band) == expected


def test_t2_is_the_mis_prioritised_tier():
    """A complex file nobody touches is rarely worth the risk of refactoring."""
    assert hotspot_tier(is_high_change_frequency=False, above_complexity_band=True) == "T2"
