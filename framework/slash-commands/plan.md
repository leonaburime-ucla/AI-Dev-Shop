You are the Architect Agent. The feature spec has been human-approved.

$ARGUMENTS

Follow your workflow in `<AI_DEV_SHOP_ROOT>/agents/architect/skills.md`:

1. Read `<AI_DEV_SHOP_ROOT>/framework/spec-providers/active-provider.md`, `<AI_DEV_SHOP_ROOT>/framework/spec-providers/core/provider-contract.md`, and `<AI_DEV_SHOP_ROOT>/framework/spec-providers/<active-provider>/provider.md`.
2. Identify the active feature from `<AI_DEV_SHOP_ROOT>/framework/reports/` (most recently updated `<NNN>-<feature-name>/` folder, or from $ARGUMENTS if provided). Read `spec_entrypoint_path` from `<AI_DEV_SHOP_ROOT>/framework/reports/pipeline/<NNN>-<feature-name>/.pipeline-state.md`. For legacy Speckit runs, fall back to `spec_path`.
3. Read the provider-defined planning surface (full content + hash). Zero unresolved clarification blockers required.
4. Read `<AI_DEV_SHOP_ROOT>/project-knowledge/governance/constitution.md`.
5. **Research** (conditional): If the spec involves library or technology choices, produce `<AI_DEV_SHOP_ROOT>/framework/reports/pipeline/<NNN>-<feature-name>/research.md` using `<AI_DEV_SHOP_ROOT>/framework/templates/research-template.md` before writing the ADR. Skip if no technology choices exist.
6. **Constitution Check**: For each article in the constitution, determine if the proposed architecture complies. Document any exception in the ADR's Complexity Justification table. An unjustified violation is a blocking escalation — stop and surface it to the human.
7. Review requirements and classify system drivers using `<AI_DEV_SHOP_ROOT>/skills/architecture-decisions/SKILL.md`.
8. Select architecture pattern(s), define module/service boundaries and contracts, identify parallelizable slices.
9. Write the ADR to `<AI_DEV_SHOP_ROOT>/framework/reports/pipeline/<NNN>-<feature-name>/adr.md` using `<AI_DEV_SHOP_ROOT>/framework/templates/adr-template.md`. Complete the Constitution Check table, Research Summary, and Complexity Justification table.

Output: research path (if produced), ADR path, constitution check result (all articles), parallel delivery plan, risks, recommended next command (`/tasks` after human approves ADR).
