# Agent Index

Full operating procedure for each agent lives in its `skills.md`. Use this file as the roster and persona-entrypoint map.

| Agent | Role | File |
|---|---|---|
| VibeCoder (optional) | Fast exploratory prototyping — optional on-ramp before the structured pipeline | `agents/vibecoder/skills.md` |
| System Blueprint (optional, pre-spec) | Macro-level system planning and spec decomposition before feature specs | `agents/system-blueprint/skills.md` |
| Coordinator | Pipeline orchestration, routing, convergence, human escalation | `agents/coordinator/skills.md` |
| Skills Librarian (optional) | Centralized external skill discovery, audit, and canonical merge governance | `agents/skills-librarian/skills.md` |
| Spec | Converts intent into versioned, testable spec packages | `agents/spec/skills.md` |
| Architect | Selects patterns, defines boundaries, produces ADR | `agents/architect/skills.md` |
| TDD | Writes certified test suite before implementation | `agents/tdd/skills.md` |
| Programmer | Implements code to satisfy certified tests | `agents/programmer/skills.md` |
| UX/UI Designer (optional) | Defines visual direction, UI style system, and implementation-ready design specs for frontend work | `agents/ux-ui-designer/skills.md` |
| QA/E2E | Writes browser-level tests that validate user journeys and frontend ACs | `agents/qa-e2e/skills.md` |
| TestRunner | Executes test suite, reports pass/fail evidence | `agents/testrunner/skills.md` |
| Code Review | Reviews spec alignment, architecture, test quality, security surface | `agents/code-review/skills.md` |
| Refactor | Proposes non-behavioral structural improvements post-review | `agents/refactor/skills.md` |
| Security | Analyzes threat surface, classifies findings, blocks Critical/High | `agents/security/skills.md` |
| DevOps | Produces Dockerfiles, CI/CD configs, IaC, and deployment runbooks | `agents/devops/skills.md` |
| Docs | Publishes OpenAPI specs, writes user guides, and produces release notes | `agents/docs/skills.md` |
| Observer (optional) | Watches pipeline, detects patterns, produces system improvements | `agents/observer/skills.md` |
| Red-Team | Adversarially probes approved specs before Architect dispatch | `agents/red-team/skills.md` |
| CodeBase Analyzer | Analyzes existing codebase before pipeline begins | `agents/codebase-analyzer/skills.md` |
| Database | Owns schema design, migrations, query patterns | `agents/database/skills.md` |
| Supabase Sub-Agent | Supabase-specific implementation under Database Agent | `agents/database/supabase/skills.md` |

Use `<AI_DEV_SHOP_ROOT>/project-knowledge/routing/skills-registry.md` when you need shared-skill ownership and reuse mapping rather than the persona roster.
