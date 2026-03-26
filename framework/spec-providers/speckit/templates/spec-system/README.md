# Spec-System Templates

This folder is the strict Speckit compatibility package used by the default AI Dev Shop spec flow.

## Package Shape

A complete strict package has 10 logical files:

- `feature.spec.md`
- `api.spec.md`
- `state.spec.md`
- `orchestrator.spec.md`
- `ui.spec.md`
- `errors.spec.md`
- `behavior.spec.md`
- `traceability.spec.md`
- `spec-manifest.md`
- `spec-dod.md`

Only four are always required regardless of feature type:

- `feature.spec.md`
- `traceability.spec.md`
- `spec-manifest.md`
- `spec-dod.md`

The others are conditional and must either exist or be marked `OMITTED` with a concrete reason in `spec-manifest.md`.

## Authoring Rule

Do not hand off a spec package to `/plan` until:

1. `spec-dod.md` is PASS or NA throughout.
2. Zero `[NEEDS CLARIFICATION]` markers remain.
3. `traceability.spec.md` contains all REQ/AC/INV/EC ids from `feature.spec.md`.
4. `spec-manifest.md` accurately lists present and omitted files.

## Validator

When Python is available, validate a package with:

```bash
python3 framework/spec-providers/speckit/validators/validate_spec_package.py <spec-folder>
```

Treat any non-zero exit code as a blocking handoff failure.
