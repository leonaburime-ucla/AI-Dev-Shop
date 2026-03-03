# React Skill Operations

- Version: 1.0.0
- Last Updated: 2026-02-28
- Scope: React and Next.js implementation, review, and QA work

This file operationalizes React skill usage across agents.

## 1) Skill Loading Enforcement (Preflight)

For any React/Next.js component task, load these by default:

- `skills/frontend-react-orcbash/SKILL.md`
- `skills/vercel-react-best-practices/SKILL.md`
- `skills/vercel-composition-patterns/SKILL.md`

If UI audit/review is requested, also load:

- `skills/vercel-web-design-guidelines/SKILL.md`
- `skills/frontend-accessibility/SKILL.md`

If React Native/Expo scope is present, add:

- `skills/vercel-react-native-skills/SKILL.md`

Do not load any React-specific skills from this file for non-React tasks (Python, backend TypeScript APIs, Go, Java, database-only work, or infrastructure-only work).

## 2) Precedence Matrix (When Guidance Differs)

Apply this priority order:

1. Spec acceptance criteria and explicit user constraints
2. Security and data-classification rules
3. Accessibility requirements
4. Architecture boundaries (Orc-BASH and ADR constraints)
5. Performance and rendering tactics (Vercel best-practices)
6. Style/readability preferences

If two items conflict at the same level, use `project-knowledge/governance/skill-conflict-resolution.md`.

## 3) Source Pin and Update Process

Imported source of truth:

- Repository: `https://github.com/vercel-labs/agent-skills`
- Imported commit: `e23951b`
- Imported folders:
  - `react-best-practices`
  - `composition-patterns`
  - `react-native-skills`
  - `web-design-guidelines`

Refresh process:

1. Pull latest into local mirror at `/Users/la/Desktop/Multi-Agent Swarm Foundation/vercel-agent-skills`
2. Review upstream diff of `skills/*/rules`
3. Copy changes into local `skills/vercel-*` folders
4. Update `project-knowledge/routing/skills-registry.md` only if folder names or ownership changed
5. Record new commit hash and date in this file

## 4) Evaluation Loop (Benchmark Set)

Use these benchmark prompts to validate skill adherence:

1. Build a Next.js page that fetches three independent resources and streams UI without waterfalls.
2. Refactor a component with six boolean props into compound/explicit variant components.
3. Optimize a list-heavy React view with avoidable re-renders and unstable callbacks.
4. Perform UI audit for accessibility and design findings on a provided component file.
5. Convert a sequential data-fetching path to parallelized, cache-aware server-side fetching.

For each benchmark, score:

- Correct skill selection
- Rule citation quality
- Architecture boundary adherence
- Performance outcome quality
- Regression risk

## 5) Quick User Shortcut

Use this one-liner to force deterministic skill loading:

`React strict mode: apply frontend-react-orcbash + vercel-react-best-practices + vercel-composition-patterns, and cite the exact rules used.`
