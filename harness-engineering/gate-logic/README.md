# Gate Logic — the executable specification

`reference.py` is the **normative definition of every gate predicate** in the
code-quality metrics harness. `test_reference.py` is its case table.

When a sensor doc and this module disagree about what a gate computes, **this
module is correct and the prose is a defect.**

## Why this exists

The gate rules used to live only in markdown. Across three review rounds by five
models, the duplication predicate alone was wrong three times, in three different
ways, each fix breaking a neighbouring case:

<!-- historical:start -->
| Version | Predicate | Failure |
|---|---|---|
| v1 | group not present at base | a 2-site group **is** present, so the third-site catch could never fire |
| v2 | `base_occurrences < 3` | `3 < 3` is false, so a 3-site group could grow to 5 without breaching |
| v3 | `head > base AND head >= 3` | current; fires on growth past three from any starting count |
<!-- historical:end -->

Every reviewer read prose that looked right. Prose cannot be executed, so nothing
caught the arithmetic — and the same class of bug appeared in the coverage
small-unit rule, where a fix routed small units to a fallback that carried its
own size minimum, leaving a 4-branch/12-line unit at 25% coverage triggering
nothing while the prose claimed "Nothing escapes by being small."

Both bugs are now regression tests. Reintroducing either fails immediately with a
test name that says which round found it.

## What is and is not covered

**Covered — arithmetic.** Delta comparisons, threshold crossings, band
boundaries, occurrence counting, status capping, tier assignment. These are pure
functions over numbers and they are fully testable here, with no host project and
no toolchain.

**Not covered — tool capability.** Whether `lizard` emits nesting, whether
`diff-cover` reports branches, whether an ESLint rule configured at its gate
value can report sub-gate values. Those are claims about the world, not about
arithmetic, and no test in this directory can settle them. They are what the
per-sensor **conformance fixtures** exist for — and those fixtures have been
specified but never executed, which remains the largest open gap in this
program.

## Running

```bash
python3 -m pytest harness-engineering/gate-logic/ -q
```

Also runs as part of `harness-engineering/validators/run-all.sh` (hard checks).

## Adding a gate

1. Implement the predicate in `reference.py` as a pure function.
2. Add a case table covering every boundary — at, one below, one above.
3. Add a regression test for any defect a review found, named for the round.
4. Mutation-check it: break the predicate deliberately and confirm a test fails.
   A test suite that cannot fail is decoration.

## Related

- `../quality/gate-validation-status.md` — which gates may block, and the closed integrity set
- `../sensors/` — intent, tooling, custody, and worked examples per gate
- `../validators/validate_harness_consistency.py` — checks the prose agrees with itself across files
