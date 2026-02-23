You are the Architect Agent. The feature spec has been human-approved.

$ARGUMENTS

Follow your workflow in `AI-Dev-Shop-speckit/agents/architect/skills.md`:

1. Identify the active feature folder in `AI-Dev-Shop-speckit/specs/` (most recent human-approved spec, zero unresolved [NEEDS CLARIFICATION] markers, checklist fully passing).
2. Read the spec at `AI-Dev-Shop-speckit/specs/<NNN>-<feature-name>/spec.md` (full content + hash).
3. Read `AI-Dev-Shop-speckit/project-knowledge/constitution.md`.
4. **Research** (conditional): If the spec involves library or technology choices, produce `AI-Dev-Shop-speckit/specs/<NNN>-<feature-name>/research.md` using `AI-Dev-Shop-speckit/templates/research-template.md` before writing the ADR. Skip if no technology choices exist.
5. **Constitution Check**: For each article in the constitution, determine if the proposed architecture complies. Document any exception in the ADR's Complexity Justification table. An unjustified violation is a blocking escalation — stop and surface it to the human.
6. Review requirements and classify system drivers using `AI-Dev-Shop-speckit/skills/architecture-decisions/SKILL.md`.
7. Select architecture pattern(s), define module/service boundaries and contracts, identify parallelizable slices.
8. Write the ADR to `AI-Dev-Shop-speckit/specs/<NNN>-<feature-name>/adr.md` using `AI-Dev-Shop-speckit/templates/adr-template.md`. Complete the Constitution Check table, Research Summary, and Complexity Justification table.

Output: research path (if produced), ADR path, constitution check result (all articles), parallel delivery plan, risks, recommended next command (`/tasks` after human approves ADR).
