# Spec Manifest: Payments Ledger Modernization

---

## Header Metadata

| Field | Value |
|-------|-------|
| spec_id | SPEC-203 |
| feature_name | FEAT-203-payments-ledger-modernization |
| version | 1.0.0 |
| last_edited | 2026-04-27T12:10:00Z |
| spec_naming | standard |
| spec_root | harness-engineering/agent-evals/architect-evals/benchmark-suite/eval-3-payments-ledger-modernization/seed-state/project/reports/pipeline/203-payments-ledger-modernization |
| spec_entrypoint | feature.spec.md |
| spec_readiness_artifact | spec-dod.md |

## Package Applicability Matrix

| Logical File | Status (`PRESENT|OMITTED`) | Actual Filename | Why Present / Why Omitted |
|---|---|---|---|
| `feature.spec.md` | PRESENT | `feature.spec.md` | Canonical macro requirements for the architecture benchmark |
| `api.spec.md` | OMITTED | `—` | Endpoint-level contract detail is intentionally out of scope for this architecture-only eval |
| `state.spec.md` | OMITTED | `—` | Detailed state typing is deferred because this suite tests architecture tradeoffs |
| `orchestrator.spec.md` | OMITTED | `—` | Orchestrator contract detail is intentionally deferred in this macro benchmark |
| `ui.spec.md` | OMITTED | `—` | UI contracts are not the target of this payments architecture benchmark |
| `errors.spec.md` | OMITTED | `—` | Error registry detail is intentionally deferred; audit and failure behavior are covered at macro level |
| `behavior.spec.md` | OMITTED | `—` | Rule-ordering detail is not the benchmark target in this suite |
| `traceability.spec.md` | PRESENT | `traceability.spec.md` | Seeds REQ/AC/INV/EC coverage before downstream stages |
| `spec-manifest.md` | PRESENT | `spec-manifest.md` | Required package index for downstream stages |
| `spec-dod.md` | PRESENT | `spec-dod.md` | Readiness gate proving this macro package is architecture-ready |

## Stage Read Set

| Stage | Must Read |
|---|---|
| `architect` | `feature.spec.md`, `traceability.spec.md`, `spec-dod.md`, `system-blueprint.md` |
| `tdd` | `feature.spec.md`, `traceability.spec.md`, `spec-dod.md`, `adr.md` |
| `programmer` | `feature.spec.md`, `traceability.spec.md`, `adr.md`, certified tests |

## Brownfield References

| Existing Touchpoint | Why It Matters |
|---|---|
| existing payments modernization effort | Brownfield modernization; correctness and audit pressure come from live regulated context |

## Validation Notes

- Validator last run: 2026-04-27T12:10:00Z
- Validator result: PASS
- Notes: Macro-only Speckit package retained intentionally for Architect scorecard evaluation.
