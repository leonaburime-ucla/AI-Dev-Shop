---
name: function-quality-assessment
version: 1.2.0
last_updated: 2026-04-27
description: Use when writing, reviewing, or refactoring logic-bearing functions so low-level function quality is assessed consistently with an overall score, severity-graded findings, complexity notes, and clear pass/debt/block routing.
---

# Skill: Function Quality Assessment

Apply this skill to every new or materially changed logic-bearing function.

This skill is both a build-time coding guide and an operational audit wrapper.
It does not replace the source skills below; it turns their rules into a
per-function assessment with `@overallScore`, severity findings, fix-before-
handoff behavior, and review reporting.

Use it twice:

- before coding, to shape the function correctly from the start
- after coding, to score the result, catch gaps, and decide whether the change
  can be handed off

## Writing Posture

When writing a logic-bearing function:

1. Give the function one clear job. Keep validation, business rules, and
   orchestration separate unless the existing boundary is intentionally broader.
2. Prefer pure functions for rules, calculations, and transformations. Keep
   side effects at explicit boundaries.
3. Do not mutate input objects unless an in-place contract is required by the
   existing API and documented clearly.
4. Make important dependencies explicit. Do not hide behavior behind module
   state, environment reads, clocks, randomness, caches, or feature flags
   unless that dependency is intentional, controlled, and testable.
5. For exported or boundary functions, default to a required input object as
   the first parameter and an optional options object as the second parameter,
   unless compatibility or language convention justifies another shape.
6. Keep return shapes and error behavior stable. Do not mix unrelated failure
   signals such as booleans, strings, `null`, and thrown errors for the same
   kind of problem.
7. Decide the test seam before coding. If the function cannot be tested with
   direct inputs and direct assertions, redesign the boundary first.
8. Think about scale before coding. Identify complexity, query or I/O shape,
   resource bounds, idempotency needs, and concurrency risks for caller-
   controlled or unbounded input.
9. For rule, validation, batch, reducer, or cross-record workflows, name at
   least one aggregate or adversarial edge case before coding and add coverage
   for it before handoff.
10. If a function still has avoidable quality findings after implementation,
    refactor locally before handoff instead of documenting obvious debt as if it
    were final design.

## Source Skills

Use these as the source of truth for definitions:

- `<AI_DEV_SHOP_ROOT>/skills/coding-foundations/SKILL.md` — explicit dependencies, pure-by-default decisions, effect boundaries, stable contracts, fail-fast defaults, and small readable units
- `<AI_DEV_SHOP_ROOT>/skills/testable-design-patterns/SKILL.md` — two-object exported signatures, typed contracts, coverage-friendly branch design, test seams, typed error paths, and test anti-pattern bans
- `<AI_DEV_SHOP_ROOT>/skills/implementation-guardrails/SKILL.md` — complexity, scale, query shape, resource bounds, per-item I/O, and tradeoff notes
- `<AI_DEV_SHOP_ROOT>/skills/inline-code-documentation/SKILL.md` — language-idiomatic function documentation format

If this skill appears to conflict with a source skill, keep the source skill's
definition and use this skill only to score, report, and route the result.

## Ownership

- Programmer applies this skill before and after implementation, fixes locally
  fixable findings, and documents the final function score.
- Code Review validates the Programmer's assessment independently and records a
  Function Quality Assessment section in the saved code review report.
- Refactor uses failed assessment findings as targeted cleanup input.
- Coordinator sees only the routing summary: score, status, Critical/High count,
  blocked flag, and suggested next route.

## Scope

Assess:

- exported functions and public module boundaries
- workflow, orchestration, adapter, rule, validation, and transformation functions
- local helpers with meaningful branching, business logic, I/O, error handling,
  complexity, or reuse pressure

Tiny local helpers may be covered by the closest parent assessment when a full
comment would add noise. Do not use that exception for code that is hard to
test, hard to scale, security-sensitive, or likely to be reused.

Use assessment units, not raw function count. A tiny private helper may inherit
the nearest assessed parent only when it has no meaningful branching, I/O, error
handling, scale risk, security/privacy risk, or independent reuse pressure. If a
helper owns a rule, policy decision, data transformation, effect, error contract,
or complexity tradeoff, assess it directly.

## Programmer Procedure

Before coding a logic-bearing function:

1. Identify the function's required input object and optional options object,
   unless existing API compatibility or language convention justifies another
   shape.
2. Identify the test seam and expected assertions.
3. Identify time complexity, space complexity, query/I/O shape, and resource
   bounds for caller-controlled or unbounded input.
4. Decide whether the function should be pure decision logic or an explicit
   effect boundary.

After coding:

1. Apply the checklist in `references/checklist.md` to each assessment unit.
2. Refactor locally fixable findings before handoff.
3. Add or update language-idiomatic function documentation.
4. Include time and space complexity.
5. Include `@tradeoffs` or the language-equivalent section only when the tradeoff
   is meaningful.
6. Include `@overallScore`.
7. Include severity-graded findings when the score is below 100.
8. For rule engines, validators, batch processors, reducers, reconciliation
   logic, or any workflow where behavior depends on multiple records, add at
   least one adversarial aggregate/cross-item test or direct probe.
9. If a non-trivial change has every assessed unit at `100/100`, run a score
   skepticism pass before handoff. Re-check requirements, edge cases, scale,
   hidden dependencies, error paths, and test coverage. If every score remains
   `100/100`, state why in the handoff.
10. Report coverage metrics when a local coverage command is available. If
   coverage cannot be measured, say why and identify the direct tests that cover
   each assessed unit.

## Code Review Procedure

For every new or materially changed function in scope:

1. Confirm the Programmer assessment exists when required.
2. Confirm the Programmer handoff includes the compact assessment table.
3. Re-assess the function using the same checklist.
4. Validate that `@overallScore` is plausible.
5. Flag missing, inflated, or inconsistent scores.
6. For non-trivial changes where every score is `100/100`, verify that the
   Programmer performed and documented the score skepticism pass.
7. Check whether tiny helpers were over-documented or under-assessed. Treat
   over-documentation as Recommended cleanup unless it hides a required finding.
8. For rule, validation, batch, or reducer workflows, confirm at least one
   adversarial aggregate/cross-item behavior test or probe exists.
9. Classify findings using the thresholds below.
10. Add a Function Quality Assessment section to the saved code review report at
   `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/code-review/CR-<feature-id>-<YYYY-MM-DD>.md`.

Do not create a separate function-quality report by default. Code Review already
owns the retained review artifact; this assessment belongs inside that report.

## Scoring And Blocking

Use `references/scoring-rubric.md` as the canonical scoring rubric.

- `Critical` finding: hard block regardless of score.
- `< 80`: hard block.
- `80-89`: Programmer must attempt one local fix cycle. If still `80-89`, handoff
  may proceed only with documented tech debt, smallest compliant refactor, and
  Coordinator notification.
- `90-99`: pass with findings.
- `100`: clean pass.

Code Review may upgrade any unresolved `High` finding to Required when it is
likely to cause production failure, security exposure, scale failure, or
coverage-hostile design.

## Report Shape

Programmer handoff Style Notes must include:

- a compact function-quality table:
  `function | score | Critical/High count | below-100 reason | local fix attempted`
- score skepticism result when every assessed unit is `100/100` in a non-trivial
  change
- assessed functions with `@overallScore` below 100
- Critical/High finding count
- any score below 90 after the local fix cycle
- justified deviations from the two-object parameter convention
- adversarial aggregate/cross-item tests or probes added for rule, validation,
  batch, or reducer workflows
- coverage metrics, or the reason coverage could not be measured
- remaining complexity, scale, I/O, determinism, concurrency, security, or
  extensibility risks

Code Review report must include:

```text
## Function Quality Assessment

- Status: PASS | DEBT | BLOCKED
- Functions assessed: <count>
- Lowest score: <score or n/a>
- Critical findings: <count>
- High findings: <count>
- Missing assessments: <count>
- Missing handoff-table evidence: <yes/no>
- Missing score-skepticism evidence: <yes/no/n/a>
- Missing adversarial aggregate/cross-item evidence: <yes/no/n/a>
- Required fixes: <summary or none>
- Recommended refactors: <summary or none>
- Suggested next route: Programmer | Refactor | Security | Architect | None
```

## References

- `references/checklist.md`
- `references/scoring-rubric.md`
