# Standards

## Scope

- Applies to project-level instruction rewrites.
- Frozen scope for this program: `skills/vercel-*`.

## Section Contract

1. `## Execution`
2. `## Guardrails`
3. `## Output`
4. `## Reference` (optional, uncapped)

## Budget Targets

- `Execution` <= 250 words
- `Guardrails` <= 150 words
- `Output` <= 120 words

If over budget: reduce now or record owner/date in execution tracker.

## Writing Style

- Telegraphic imperative bullets.
- Use concrete verbs (`Read`, `Verify`, `Dispatch`, `Route`, `Escalate`).
- Keep rationale in `Reference` only.

## Structure Over Prose

Prefer enforceable structure over reminder text:
- Required fields/checklists/schemas first
- Narrative reminders second

## Canonical Rule Homes

- Routing rules -> `skills/coordination/SKILL.md`
- Per-agent execution -> `agents/<name>/skills.md`
- Stage contracts/context injection -> `workflows/multi-agent-pipeline.md`
- Project-wide guardrails -> `project-knowledge/governance/constitution.md`
- Human escalation policy -> `project-knowledge/governance/escalation-policy.md`

## Dependency Gates

- `SMF.1` gates `SMF.3`, `SMF.4`
- `SMF.2` gates `SMF.6`

## HUMANS.md Naming Convention

For rewrite rollouts:
- `HUMANS.md` = human-readable explanatory version for users/reviewers.
- `SKILL.md` = execution-optimized version for AI/LLM runtime behavior.
