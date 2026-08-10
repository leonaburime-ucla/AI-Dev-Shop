# Harness Maintenance Report

Generated from current repo state. Refresh with `python3 harness-engineering/validators/generate_maintenance_report.py`.

## Hard Validator Summary

- Path references: PASS
- Registry integrity: PASS

```text
PASS: repo-local markdown path references resolved cleanly.

PASS: all paths referenced by skills-registry exist.
PASS: canonical skill coverage is complete for skills-registry.
```

## Advisory Audit

- Doc-garden audit: PASS
- Doc staleness audit: PASS

```text
Harness Doc-Garden Audit
------------------------
AGENTS.md lines: 252
ADVISORY: AGENTS.md is over 200 lines. Continue shrinking it toward a map-first entrypoint.
Canonical skill files: 99
Agent persona files: 21
Benchmark sample directories: 7
File-trigger routes: 13
ADVISORY: run this audit after framework changes and pair it with the hard validators.

Harness Doc Staleness Audit
---------------------------
Watchlist entries: 6
ADVISORY: watchlist review dates are within declared cadence.
ADVISORY: run this after routing/workflow changes to catch source-of-truth drift early.
```

## Benchmark Coverage

| Agent Dir | Sample Count |
|---|---:|
| `spec-agent` | 1 |
| `architect-agent` | 1 |
| `tdd-agent` | 1 |
| `programmer-agent` | 1 |
| `testrunner-agent` | 1 |
| `code-review-agent` | 1 |
| `security-agent` | 1 |

## Repo Signals

- `AGENTS.md` line count: 252
- Registry exceptions in use: 6

## Maintenance Recommendations

- Keep shrinking `AGENTS.md` or move new detail into linked source docs.
- Review whether every registry exception is still intentional and temporary.
