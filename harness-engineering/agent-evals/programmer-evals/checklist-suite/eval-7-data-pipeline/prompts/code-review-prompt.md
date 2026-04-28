# Coordinator Dispatch — Code Review Agent

## Task

Review the data pipeline transformer for CRM customer record sync. The Programmer agent has hardened it for real-time use (previously ran as a cron job). Perform a full code review against all activated skills and checklist items.

## Scope

- Review all code in `project/src/` for correctness, maintainability, and production-readiness
- Validate test quality and coverage in `project/src/__tests__/`
- Check alignment with `project-brief.md` requirements
- Apply all standard code review skills and guardrails
- Flag any issues with severity ratings

## Spec Reference

Use `project-brief.md` as the active spec.

## Files to Review

- `project/src/pipeline.ts` — main pipeline logic
- `project/src/__tests__/pipeline.test.ts` — test suite

## Activated Skills

Base skills only.
