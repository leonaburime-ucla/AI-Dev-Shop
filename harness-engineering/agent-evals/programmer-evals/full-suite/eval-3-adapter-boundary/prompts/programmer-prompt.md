# Coordinator Dispatch — Programmer Agent

## Task

We're integrating a third-party payment SDK and need a clean adapter layer. An engineer on the team wrote the initial wrapper but got pulled into incident response. The code works for the happy path but hasn't been hardened.

## Scope

- Review and harden the existing adapter in `project/src/`
- Ensure all requirements from `project-brief.md` are met
- Ensure tests are thorough, especially around error handling
- Apply all standard skills and guardrails per your agent definition
- Deliver production-ready code with proper documentation

## Spec Reference

Use `project-brief.md` as the active spec. Each numbered requirement is an acceptance criterion.

## Existing Code

- `project/src/types.ts` — SDK interface (do not modify)
- `project/src/adapter.ts` — payment adapter implementation
- `project/src/__tests__/adapter.test.ts` — initial tests

The adapter handles basic charge/refund/get operations. Your job is to make it safe for production traffic.

## Activated Skills

Base skills only.
