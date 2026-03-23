# File Trigger Table

This table helps the Coordinator choose the likely owner agent when the changed files or requested paths are already known.

It is a routing aid, not an absolute law. Human intent and explicit mode switches still take precedence.

## Trigger Rules

| File Pattern or Area | Likely Owner | Why |
|---|---|---|
| `agents/**`, `skills/**`, `workflows/**`, `templates/**`, `harness-engineering/**` | Coordinator + Observer maintenance flow | Toolkit source changes affect the framework itself and should trigger harness maintenance behavior. |
| `project-knowledge/governance/**` | Coordinator or Architect | Governance and policy changes often affect global operating rules or architectural constraints. |
| `project-knowledge/routing/**` | Coordinator | Routing docs are Coordinator-owned source-of-truth artifacts. |
| `project-knowledge/operations/**` | Coordinator | Operational quickstarts, reminders, and runtime maps are Coordinator-owned. |
| `reports/codebase-analysis/**` | CodeBase Analyzer | Analysis artifacts belong to discovery and brownfield mapping. |
| `reports/pipeline/**/feature.spec.md`, `specs/**` | Spec Agent | Spec packages and clarifications belong to Spec. |
| `reports/pipeline/**/red-team-findings.md` | Red-Team Agent | Adversarial preflight belongs to Red-Team. |
| `reports/pipeline/**/adr.md`, `reports/pipeline/**/research.md` | Architect | ADRs and architecture research are Architect outputs. |
| `reports/pipeline/**/tasks.md`, `.pipeline-state.md` | Coordinator | Task generation and pipeline state are Coordinator-owned artifacts. |
| `reports/pipeline/**/test-certification.md`, `__tests__/**`, `tests/**` (test-definition work) | TDD Agent | Test design and certification belong to TDD. |
| `src/**/*.sql`, `db/**`, `migrations/**`, `supabase/migrations/**` | Database Agent | Schema, migration, and query ownership start with Database. |
| `supabase/functions/**`, Supabase platform wiring | Database Agent -> Supabase Sub-Agent when needed | Supabase-specific implementation belongs to the platform specialist under Database. |
| frontend UI files such as `app/**`, `pages/**`, `components/**`, `src/ui/**` | Programmer or UX/UI Designer depending on task | UI implementation belongs to Programmer; design-system or visual-direction work belongs to UX/UI Designer. |
| browser journey tests such as `__tests__/e2e/**`, `playwright/**` | QA/E2E Agent | Browser-level user-journey verification belongs to QA/E2E. |
| CI/CD, deployment, infra such as `.github/workflows/**`, `Dockerfile*`, `infra/**`, `terraform/**` | DevOps Agent | Delivery and environment automation belong to DevOps. |
| API docs, release notes, OpenAPI, changelog files | Docs Agent | User-facing and integrator-facing documentation belongs to Docs. |
| security reviews, authz policy reviews, threat reports | Security Agent | Threat modeling and severity classification belong to Security. |

## Brownfield Rule

If a request targets an existing codebase and the relevant file area is not yet clear, default to CodeBase Analyzer before downstream planning.

## Unknown Area Rule

If the file pattern does not clearly map to one owner:

1. run a small read-only discovery pass first
2. return the likely owner plus the evidence paths
3. then dispatch the owner agent
