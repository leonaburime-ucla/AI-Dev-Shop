# Spec Manifest: Team Chat Platform

---

## Header Metadata

| Field | Value |
|-------|-------|
| spec_id | SPEC-201 |
| feature_name | FEAT-201-team-chat-platform |
| version | 1.0.0 |
| last_edited | 2026-04-27T12:00:00Z |
| spec_naming | standard |
| spec_root | harness-engineering/agent-evals/architect-evals/scorecard-suite/eval-1-team-chat-saas/seed-state/project/reports/pipeline/201-team-chat-platform |
| spec_entrypoint | feature.spec.md |
| spec_readiness_artifact | spec-dod.md |

## Package Applicability Matrix

| Logical File | Status (`PRESENT|OMITTED`) | Actual Filename | Why Present / Why Omitted |
|---|---|---|---|
| `feature.spec.md` | PRESENT | `feature.spec.md` | Canonical macro requirements for the architecture benchmark |
| `api.spec.md` | OMITTED | `—` | This eval targets architecture scoring, not endpoint-level contract design |
| `state.spec.md` | OMITTED | `—` | Durable state concerns are described at macro level in feature and blueprint inputs |
| `orchestrator.spec.md` | OMITTED | `—` | Orchestration detail is intentionally deferred because the eval targets pattern selection rather than orchestrator typing |
| `ui.spec.md` | OMITTED | `—` | UI component contracts are out of scope for this architecture-only benchmark |
| `errors.spec.md` | OMITTED | `—` | Error registry detail is intentionally deferred; the eval focuses on architecture tradeoffs |
| `behavior.spec.md` | OMITTED | `—` | Rule ordering and dedup detail are not the benchmark target in this suite |
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
| — | Greenfield eval fixture |

## Validation Notes

- Validator last run: 2026-04-27T12:00:00Z
- Validator result: PASS
- Notes: Macro-only Speckit package retained intentionally for Architect scorecard evaluation.
