# Code Review Benchmark Suite

Canonical benchmark suite for Code Review evals.

- 3 evals: easy (cr-eval-1), medium (cr-eval-2), hard (cr-eval-3)
- Tests Code Review agent in isolation using seeded code + fake Programmer handoff
- Each eval has a `seed-state/` with Python source, tests, and a fake handoff report

Suite-scoped TSVs and seed-ledgers are the source of truth.

