# Coordinator Dispatch — Programmer Agent

## Task

We need a rate limiter for our API gateway. The platform team started the implementation using a sliding window approach. They got the basic algorithm working but haven't had time to make it production-grade.

## Scope

- Review and improve the existing rate limiter in `project/src/`
- Ensure all requirements from `project-brief.md` are met
- Ensure tests are reliable and deterministic
- Apply all standard skills and guardrails per your agent definition
- Deliver production-ready code with proper documentation

## Spec Reference

Use `project-brief.md` as the active spec. Each numbered requirement is an acceptance criterion.

## Existing Code

- `project/src/rate-limiter.ts` — rate limiter implementation
- `project/src/__tests__/rate-limiter.test.ts` — initial tests

The basic sliding window logic works. Your job is to verify it meets all requirements and make it production-ready.

## Activated Skills

Base skills only.
