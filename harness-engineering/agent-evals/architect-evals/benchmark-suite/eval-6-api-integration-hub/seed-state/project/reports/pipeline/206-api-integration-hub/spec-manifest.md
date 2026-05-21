# Spec Manifest: API Integration Hub

---

## Header Metadata

| Field | Value |
|-------|-------|
| spec_id | SPEC-206 |
| feature_name | FEAT-206-api-integration-hub |
| version | 1.0.0 |
| last_edited | 2026-04-29T09:10:00Z |
| spec_naming | standard |
| spec_root | harness-engineering/agent-evals/architect-evals/benchmark-suite/eval-6-api-integration-hub/seed-state/project/reports/pipeline/206-api-integration-hub |
| spec_entrypoint | feature.spec.md |
| spec_readiness_artifact | spec-dod.md |

## Package Applicability Matrix

| Logical File | Status (`PRESENT|OMITTED`) | Actual Filename | Why Present / Why Omitted |
|---|---|---|---|
| `feature.spec.md` | PRESENT | `feature.spec.md` | Canonical macro requirements for the API integration architecture benchmark |
| `api.spec.md` | OMITTED | `—` | Endpoint-level contract detail is intentionally out of scope for this architecture-only eval |
| `state.spec.md` | OMITTED | `—` | Detailed state typing is intentionally deferred |
| `orchestrator.spec.md` | OMITTED | `—` | Orchestrator contract detail is intentionally deferred in this macro benchmark |
| `ui.spec.md` | OMITTED | `—` | UI contracts are not the target of this integration architecture benchmark |
| `errors.spec.md` | OMITTED | `—` | Error registry detail is deferred; failure behavior is covered at macro level |
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
| existing partner APIs, webhooks, and internal consumers | Integration boundaries and drift pressure come from live external contracts |

## Validation Notes

- Validator last run: 2026-04-29T09:10:00Z
- Validator result: PASS
- Notes: Macro-only Speckit package retained intentionally for Architect scorecard evaluation.
