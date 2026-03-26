# Spec Manifest: <feature-name>

<!-- SPEC PACKAGE FILE: framework/spec-providers/speckit/templates/spec-system/spec-manifest.md -->
<!-- Part of the spec-system package. See framework/spec-providers/speckit/templates/spec-system/ for all required files. -->

---

## Header Metadata

| Field | Value |
|-------|-------|
| spec_id | SPEC-<NNN> |
| feature_name | FEAT-<NNN>-<short-feature-name> |
| version | <semver — must match feature.spec.md version> |
| last_edited | <ISO-8601 UTC> |
| spec_naming | prefixed \| standard |
| spec_root | <absolute or repo-relative path to this spec folder> |
| spec_entrypoint | <actual filename for the canonical feature spec> |
| spec_readiness_artifact | <actual filename for the readiness gate, usually spec-dod.md> |

**Purpose:** This manifest is the package index for the strict Speckit compatibility flow.

It exists to make downstream stages read the full package instead of guessing filenames from memory.

Use it to answer:
- which spec files actually exist for this feature
- which files were intentionally omitted and why
- which files Architect, TDD, and Programmer must read

---

## Package Applicability Matrix

Fill one row for every logical file in the strict package.

Rules:
- `PRESENT` means the file exists in this folder and is part of the read set for at least one downstream stage
- `OMITTED` is allowed only for conditional files and requires a concrete why
- `feature.spec.md`, `traceability.spec.md`, `spec-manifest.md`, and `spec-dod.md` must always be `PRESENT`

| Logical File | Status (`PRESENT|OMITTED`) | Actual Filename | Why Present / Why Omitted |
|---|---|---|---|
| `feature.spec.md` | PRESENT | `<actual filename>` | Canonical primary requirements spec |
| `api.spec.md` | OMITTED | `—` | <why the feature has no API surface or why this file exists> |
| `state.spec.md` | OMITTED | `—` | <why the feature has no stateful contract or why this file exists> |
| `orchestrator.spec.md` | OMITTED | `—` | <why the feature has no coordinator/orchestrator layer or why this file exists> |
| `ui.spec.md` | OMITTED | `—` | <why the feature has no UI surface or why this file exists> |
| `errors.spec.md` | OMITTED | `—` | <why the feature defines no new error registry or why this file exists> |
| `behavior.spec.md` | OMITTED | `—` | <why the feature has no precedence/ordering/dedup rules or why this file exists> |
| `traceability.spec.md` | PRESENT | `<actual filename>` | Seeds REQ/AC/INV/EC coverage mapping before TDD |
| `spec-manifest.md` | PRESENT | `<actual filename>` | Required package index for downstream stages |
| `spec-dod.md` | PRESENT | `<actual filename>` | Readiness gate and quality proof |

---

## Stage Read Set

List the actual files each downstream stage must read.

| Stage | Must Read |
|---|---|
| `architect` | `<actual feature spec>`, `<actual traceability spec>`, `<actual spec-dod>`, plus every other `PRESENT` contract file relevant to architecture decisions |
| `tdd` | `<actual feature spec>`, `<actual traceability spec>`, `<actual spec-dod>`, ADR, tasks |
| `programmer` | `<actual feature spec>`, `<actual traceability spec>`, all relevant `PRESENT` contract files, ADR, certified tests |

---

## Brownfield References (optional but recommended)

If this feature extends an existing system, cite the exact files, functions, APIs, or tables it must integrate with.
Do not restate the legacy behavior here; cite it.

| Existing Touchpoint | Why It Matters |
|---|---|
| `<path or symbol>` | <constraint or integration boundary> |
| `<path or symbol>` | <constraint or integration boundary> |

---

## Validation Notes

- Validator last run: <ISO-8601 UTC or `not-run`>
- Validator result: PASS \| FAIL
- Notes: <brief summary of what was corrected or any remaining human-reviewed exceptions>
