---
name: skills-registry
version: 1.2.10
last_updated: 2026-04-10
description: Maps every shared skill to the agents that use it. Reference when dispatching agents or updating skills.
---

# Skills Registry

All agents draw from `<AI_DEV_SHOP_ROOT>/skills/`. Do not duplicate skill content in agent files — reference the skill file instead.

| Skill | Used By |
|---|---|
| `skills/spec-writing/SKILL.md` | Spec Agent |
| `skills/test-design/SKILL.md` | TDD Agent |
| `skills/architecture-decisions/SKILL.md` | Architect, Programmer, System Blueprint Agent (secondary) |
| `skills/code-review/SKILL.md` | Code Review Agent |
| `skills/refactor-patterns/SKILL.md` | Refactor Agent |
| `skills/coordination/SKILL.md` | Coordinator, Observer |
| `skills/context-engineering/SKILL.md` | Coordinator, Observer |
| `skills/browser-live-analysis/SKILL.md` | Programmer, QA/E2E Agent |
| `skills/memory-systems/SKILL.md` | Coordinator, Observer |
| `skills/tool-design/SKILL.md` | Programmer |
| `skills/syntax-aware-editing/SKILL.md` | Inactive by default; not wired to a default agent and available for future activation when parser-backed tooling is adopted |
| `skills/agent-evaluation/SKILL.md` | Observer |
| `skills/codebase-analysis/SKILL.md` | CodeBase Analyzer |
| `skills/architecture-migration/SKILL.md` | CodeBase Analyzer |
| `skills/design-patterns/SKILL.md` | Architect, CodeBase Analyzer, System Blueprint Agent (secondary) |
| `skills/backend-implementation/SKILL.md` | Programmer (default backend/service/worker implementation entrypoint) |
| `skills/hexagonal-architecture/SKILL.md` | Architect, Programmer, CodeBase Analyzer, System Blueprint Agent |
| `skills/system-blueprint/SKILL.md` | System Blueprint Agent, Coordinator |
| `skills/system-design/SKILL.md` | System Blueprint Agent, Architect (shared macro-topology and architecture-spec reference) |
| `skills/frontend-react-orcbash/SKILL.md` | Programmer (React frontends) |
| `skills/testable-design-patterns/SKILL.md` | Architect, Programmer, Refactor Agent, TDD Agent |
| `skills/vercel-react-best-practices/SKILL.md` | Programmer, Code Review Agent (React/Next tactical guidance) |
| `skills/vercel-composition-patterns/SKILL.md` | Programmer, Code Review Agent (React component API patterns) |
| `skills/ux-design/SKILL.md` | UX/UI Designer Agent (design system creation, visual direction, component/state design, implementation-ready handoff) |
| `skills/interface-design/SKILL.md` | UX/UI Designer Agent, Programmer (app/tool interface-system consistency and design-memory reference) |
| `skills/vercel-web-design-guidelines/SKILL.md` | UX/UI Designer Agent, Code Review Agent, QA/E2E Agent (UI/UX guideline audits) |
| `skills/vercel-react-native-skills/SKILL.md` | Programmer, QA/E2E Agent, Code Review Agent (React Native/Expo tactical guidance) |
| `skills/sql-data-modeling/SKILL.md` | Database Agent |
| `skills/postgresql/SKILL.md` | Database Agent, Supabase Sub-Agent |
| `skills/supabase/SKILL.md` | Supabase Sub-Agent |
| `skills/systematic-debugging/SKILL.md` | Skills Librarian, Programmer (debug process reference) |
| `skills/pattern-priming/SKILL.md` | Programmer |
| `skills/inline-code-documentation/SKILL.md` | Programmer |
| `skills/constitution-compliance/SKILL.md` | Architect |
| `skills/superpowers-brainstorming/SKILL.md` | VibeCoder Agent |
| `skills/superpowers-using-git-worktrees/SKILL.md` | Programmer, VibeCoder Agent |
| `skills/superpowers-verification-before-completion/SKILL.md` | Programmer, TestRunner Agent, DevOps Agent |
| `skills/superpowers-finishing-a-development-branch/SKILL.md` | Programmer, VibeCoder Agent |
| `skills/superpowers-receiving-code-review/SKILL.md` | Programmer |
| `skills/superpowers-requesting-code-review/SKILL.md` | Programmer |
| `skills/superpowers-dispatching-parallel-agents/SKILL.md` | Coordinator |
| `skills/superpowers-writing-plans/SKILL.md` | Coordinator |
| `skills/shadcn-ui/SKILL.md` | Skills Librarian, Programmer, UX/UI Designer Agent (frontend component integration reference) |
| `skills/seo-geo/SKILL.md` | Skills Librarian, Programmer, Docs Agent, UX/UI Designer Agent (SEO/GEO reference) |
| `skills/web-compliance/SKILL.md` | UX/UI Designer Agent, Code Review Agent, Security Agent, QA/E2E Agent (website legal/compliance UX risk checks) |
| `skills/find-skills/SKILL.md` | Skills Librarian only (external discovery) |
| `skills/enterprise-spec/SKILL.md` | Spec Agent (enterprise contexts) |
| `skills/evaluation/eval-rubrics.md` | Observer |
| `skills/swarm-consensus/SKILL.md` | Coordinator (owns consensus dispatch; injects to other agents only when consensus mode is active) |
| `skills/external-audit/SKILL.md` | Coordinator (packages current work for one external LLM auditor and synthesizes the result back to the user) |
| `skills/observability-implementation/SKILL.md` | Architect, Programmer, Security Agent |
| `skills/incident-response/SKILL.md` | DevOps Agent, Coordinator (production incident routing), Observer (post-incident pattern analysis) |
| `skills/data-engineering/SKILL.md` | Database Agent, Architect, Programmer |
| `skills/developer-documentation/SKILL.md` | Docs Agent |
| `skills/llm-operations/SKILL.md` | Architect, Programmer, Coordinator (via shared peer-dispatch rules used by external-audit and swarm-consensus) |
| `skills/devops-delivery/SKILL.md` | DevOps Agent |
| `skills/security-review/SKILL.md` | Security, Code Review, DevOps |
| `skills/performance-engineering/SKILL.md` | TestRunner Agent, Architect |
| `skills/api-contracts/SKILL.md` | Spec Agent, Code Review Agent, Docs Agent |
| `skills/api-design/SKILL.md` | Spec Agent, Architect, Code Review Agent, Docs Agent |
| `skills/frontend-accessibility/SKILL.md` | Code Review Agent, QA/E2E Agent |
| `skills/e2e-test-architecture/SKILL.md` | QA/E2E Agent, TDD Agent |
| `skills/rag-ai-integration/SKILL.md` | Architect, Programmer, Database Agent |
| `skills/change-management/SKILL.md` | Programmer, DevOps Agent, Architect, Database Agent |
| `skills/infrastructure-as-code/SKILL.md` | DevOps Agent, Architect |
| `skills/vibe-coding/SKILL.md` | VibeCoder Agent (optional, Agent Direct Mode) |
| `framework/governance/tool-permission-policy.md` | All agents (security guardrails) |
| `harness-engineering/skills-inbox/skill-conflict-resolution.md` | All agents (cross-skill conflict handling and user choice protocol) |
| `harness-engineering/skills-inbox/skills-librarian-policy.md` | Coordinator, Skills Librarian (external skill discovery/ingestion governance) |
| `framework/operations/react-skill-operations.md` | Coordinator, Programmer, Code Review, QA/E2E (React skill preflight, precedence, and evaluation loop) |
| `harness-engineering/skills-inbox/skills-librarian-sop.md` | Skills Librarian, Coordinator (inbox workflow and audit lifecycle) |
| `framework/governance/data-classification.md` | All agents (PII and secret handling) |
| `framework/routing/model-routing.md` | Coordinator (dispatch tier selection) |
| `framework/governance/escalation-policy.md` | Coordinator (retry budgets and escalation triggers) |
| `harness-engineering/quality/agent-performance-scorecard.md` | Observer (quality tracking) |
