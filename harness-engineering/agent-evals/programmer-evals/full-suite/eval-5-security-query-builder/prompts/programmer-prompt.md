# Coordinator Dispatch — Programmer Agent

## Task

We're building a search feature for our document management system. The backend team wrote a query builder that constructs parameterized SQL. It's been running in staging without issues, but we need it reviewed and production-hardened before launch.

## Scope

- Review and harden the existing query builder in `project/src/`
- Ensure all requirements from `project-brief.md` are met
- Ensure tests cover all filter combinations and edge cases
- Apply all standard skills and guardrails per your agent definition
- Deliver production-ready code with proper documentation

## Spec Reference

Use `project-brief.md` as the active spec. Each numbered requirement is an acceptance criterion.

## Existing Code

- `project/src/query-builder.ts` — search query builder
- `project/src/__tests__/query-builder.test.ts` — initial tests

The team says it's "been working fine in staging." Your job is to verify that claim and make it safe for production.

## Activated Skills

Base skills only.
