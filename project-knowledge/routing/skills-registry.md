---
name: skills-registry
version: 1.0.0
last_updated: 2026-03-04
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
| `skills/coordination/SKILL.md` | Coordinator |
| `skills/context-engineering/SKILL.md` | Coordinator, Observer |
| `skills/memory-systems/SKILL.md` | Coordinator |
| `skills/tool-design/SKILL.md` | Programmer |
| `skills/agent-evaluation/SKILL.md` | Observer |
| `skills/codebase-analysis/SKILL.md` | CodeBase Analyzer |
| `skills/architecture-migration/SKILL.md` | CodeBase Analyzer |
| `skills/design-patterns/SKILL.md` | Architect, CodeBase Analyzer, System Blueprint Agent (secondary) |
| `skills/system-blueprint/SKILL.md` | System Blueprint Agent, Coordinator |
| `skills/frontend-react-orcbash/SKILL.md` | Programmer (React frontends) |
| `skills/testable-design-patterns/SKILL.md` | Architect, Programmer, Refactor Agent, TDD Agent |
| `skills/vercel-react-best-practices/SKILL.md` | Programmer, Code Review Agent (React/Next tactical guidance) |
| `skills/vercel-composition-patterns/SKILL.md` | Programmer, Code Review Agent (React component API patterns) |
| `skills/vercel-web-design-guidelines/SKILL.md` | Code Review Agent, QA/E2E Agent (UI/UX guideline audits) |
| `skills/vercel-react-native-skills/SKILL.md` | Programmer, QA/E2E Agent, Code Review Agent (React Native/Expo tactical guidance) |
| `skills/sql-data-modeling/SKILL.md` | Database Agent |
| `skills/postgresql/SKILL.md` | Database Agent, Supabase Sub-Agent |
| `skills/supabase/SKILL.md` | Supabase Sub-Agent |
| `skills/systematic-debugging/SKILL.md` | Skills Librarian, Programmer (debug process reference) |
| `skills/shadcn-ui/SKILL.md` | Skills Librarian, Programmer (frontend component integration reference) |
| `skills/seo-geo/SKILL.md` | Skills Librarian, Programmer, Docs Agent (SEO/GEO reference) |
| `skills/find-skills/SKILL.md` | Skills Librarian only (external discovery) |
| `skills/enterprise-spec/SKILL.md` | Spec Agent (enterprise contexts) |
| `skills/evaluation/eval-rubrics.md` | Observer |
| `skills/swarm-consensus/SKILL.md` | All agents (opt-in via Coordinator) |
| `skills/observability-implementation/SKILL.md` | Architect, Programmer, Security Agent |
| `skills/devops-delivery/SKILL.md` | DevOps Agent |
| `skills/security-review/SKILL.md` | Security, Code Review, DevOps |
| `skills/performance-engineering/SKILL.md` | TestRunner Agent, Architect |
| `skills/api-contracts/SKILL.md` | Spec Agent, Code Review Agent, Docs Agent |
| `skills/frontend-accessibility/SKILL.md` | Code Review Agent, QA/E2E Agent |
| `skills/e2e-test-architecture/SKILL.md` | QA/E2E Agent, TDD Agent |
| `skills/rag-ai-integration/SKILL.md` | Architect, Programmer, Database Agent |
| `skills/change-management/SKILL.md` | Programmer, DevOps Agent, Architect, Database Agent |
| `skills/infrastructure-as-code/SKILL.md` | DevOps Agent, Architect |
| `skills/vibe-coding/SKILL.md` | VibeCoder Agent (optional, Agent Direct Mode) |
| `project-knowledge/governance/tool-permission-policy.md` | All agents (security guardrails) |
| `project-knowledge/governance/skill-conflict-resolution.md` | All agents (cross-skill conflict handling and user choice protocol) |
| `project-knowledge/governance/skills-librarian-policy.md` | Coordinator, Skills Librarian (external skill discovery/ingestion governance) |
| `project-knowledge/operations/react-skill-operations.md` | Coordinator, Programmer, Code Review, QA/E2E (React skill preflight, precedence, and evaluation loop) |
| `project-knowledge/operations/skills-librarian-sop.md` | Skills Librarian, Coordinator (inbox workflow and audit lifecycle) |
| `project-knowledge/governance/data-classification.md` | All agents (PII and secret handling) |
| `project-knowledge/routing/model-routing.md` | Coordinator (dispatch tier selection) |
| `project-knowledge/governance/escalation-policy.md` | Coordinator (retry budgets and escalation triggers) |
| `project-knowledge/quality/agent-performance-scorecard.md` | Observer (quality tracking) |
