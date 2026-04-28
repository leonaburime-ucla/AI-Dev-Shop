# Code Review Agent — Eval 8: Access Control Evaluator

## Context

Review the access control evaluator implementation at `project/src/evaluator.ts` against the spec in `project-brief.md`.

## Deliverables

1. Read the spec and the implementation.
2. Produce a structured code review covering:
   - Correctness: Does the implementation match the spec?
   - Edge cases: Are boundary conditions handled?
   - Performance: Are there N+1 queries, unbounded loops, or missing resource limits?
   - Testability: Can the code be tested deterministically?
   - Security: Are authorization decisions safe and auditable?
3. Rate each finding by severity (Critical / High / Medium / Low).
4. Provide specific fix recommendations with code snippets where helpful.
