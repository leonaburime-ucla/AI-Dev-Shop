# System Blueprint Evals

Seeded eval infrastructure for the System Blueprint agent.

- `benchmark-suite/` contains the generated 30-seed pilot benchmark suite.
- `system-blueprint-eval-design.md` records the seed design, cowork provenance, and acceptance checks.

Validate with:

```bash
python3 harness-engineering/validators/validate_eval_suite.py harness-engineering/agent-evals/system-blueprint-evals/benchmark-suite
```
