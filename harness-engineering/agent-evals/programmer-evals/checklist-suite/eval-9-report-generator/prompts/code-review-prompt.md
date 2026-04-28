# Code Review Agent — Sales Report Generator

## Context

The programmer agent has completed work on the sales report generator. This module aggregates transaction data into summary, detailed, and executive report formats. It is being promoted from an internal nightly job to a customer-facing API endpoint.

## Task

Perform a full code review of the report generator:

1. Read the project brief (`project-brief.md`) to understand requirements and constraints.
2. Review `project/src/reporter.ts` for correctness, security, design quality, and adherence to the brief.
3. Review `project/src/__tests__/reporter.test.ts` for coverage adequacy and test quality.
4. Validate all function quality scores using the function-quality-assessment skill. Apply skepticism pass to any score that looks miscalibrated.
5. Check that coverage claims are backed by evidence (actual coverage reports, not comments).
6. Flag any security, privacy, or data handling concerns — especially important since this is becoming customer-facing.

## Deliverables

- Code review findings with severity ratings
- Validated function quality scores (with skepticism pass results)
- Coverage assessment
- List of required changes before production deployment

## Files

- `project-brief.md` — requirements specification
- `project/src/reporter.ts` — main implementation
- `project/src/__tests__/reporter.test.ts` — test suite
