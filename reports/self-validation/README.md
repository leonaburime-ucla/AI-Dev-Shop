# Self-Validation Reports

Store runtime validation results here when a feature or maintenance task requires boot-level verification before handoff.

Naming pattern:

`SV-<feature-or-workstream>-<YYYY-MM-DD-HHmm>.md`

Use the stack templates under `<AI_DEV_SHOP_ROOT>/templates/self-validation/` and the policy in `<AI_DEV_SHOP_ROOT>/harness-engineering/self-validation.md`.

If the run produces long logs or raw payload dumps, store those in `reports/offloads/` or the feature-local `offloads/` folder and reference the paths from the self-validation report.
