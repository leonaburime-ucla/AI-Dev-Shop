# Observer Cadence

This is the source of truth for recurring harness-maintenance passes.

## Trigger Conditions

Run an Observer maintenance pass when any of these happen:

- every 3rd completed feature
- any convergence escalation
- any repeated failure class that reaches the promotion threshold in `harness-engineering/failure-promotion-policy.md`
- any toolkit-maintenance change touching `AGENTS.md`, `agents/`, `skills/`, `workflows/`, `templates/`, or `harness-engineering/`
- weekly while framework-maintenance work is active

## Required Actions Per Pass

1. Run `bash harness-engineering/validators/run-all.sh`.
2. Capture the `doc_garden_audit.py` output inside the Observer report.
3. Review benchmark impact if instructions, routing, or persona files changed.
4. Check whether any recurring failure now needs promotion into a validator, benchmark, checklist, or skills update.

## Output Expectations

The Observer should produce one pattern report that includes:

- recurring failure clusters
- benchmark regressions or newly seeded fixtures
- doc-garden audit summary
- recommended harness promotions

## Scope Notes

- This cadence is for framework maintenance and system learning, not feature delivery blocking on every run.
- When the trigger is a toolkit-maintenance change, consider the Observer pass part of the definition of done for that change.
