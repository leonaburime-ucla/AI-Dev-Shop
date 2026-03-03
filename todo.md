# AI Dev Shop (speckit edition) — Todo

Paradigms and improvements to research, document, and wire into the pipeline.
All items are documentation/agent-instruction work — no code required unless noted.

Items marked **[PARTIAL]** have foundational work already in this repo.

---

## Quick Status Snapshot

- Observer Agent Operational Cadence: **OPEN / PARTIAL** (Observer docs exist; explicit dispatch cadence still missing)
- Git Branching and PR Strategy: **OPEN**
- Multi-LLM Consensus Modes and Guardrails: **OPEN / PARTIAL** (consensus + preflight exists; strict model/version normalization still open)
- Protocol Split: MCP + A2A: **OPEN**
- Spec-Kit Command Contract Parity: **OPEN / PARTIAL** (command templates exist; frontmatter contracts still missing)

---

## Priority 0 — De-Noise and Effectiveness

### Context De-Noise Hardening
**What it is:** Reduce instruction noise and improve execution reliability by moving guardrails out of prose and into enforceable structure.
**Current state:** **Framework complete** in `project-knowledge/skill-md-format/` (standards, gates, tracker, failure matrix, overlays).
**Scope guardrail:** `skills/vercel-*` remains frozen unless explicitly re-scoped by human.
**What to add next:**
- Skill transformation rollout: rewrite skills in phases using the new format (`Execution` / `Guardrails` / `Output` / `Reference`).
- Human-reference preservation: keep existing long-form skills as canonical human-readable references while overlays/new versions are validated.
- Naming convention for rollout: preserve legacy long-form docs as `HUMANS.md` with a top note that it is human-readable; keep `SKILL.md` as AI/LLM execution-optimized.
- Comparison workflow: for each rewritten skill, keep side-by-side diff notes and acceptance checks before promotion.

**Note:** Skill-MD-Format framework is complete, but the transformation still needs to be applied across the `skills/` folder in controlled rollout phases.
**Note:** `agents/*/skills.md` should be transformed in a second phase after `skills/` rollout is validated.
**Rollout safety gates:**
- Keep old long-form files as `HUMANS.md` while validating new execution-format `SKILL.md`.
- Require a side-by-side promotion checklist (non-negotiable gates, routing correctness, handoff compatibility) before replacement.
- Roll out by agent cluster with pilot validation before broad replacement.

---

## Priority 1 — Pipeline Gaps

### Observer Agent Operational Cadence
**What it is:** The Observer role and output format are well-defined but its trigger is not. Currently it "runs alongside" the pipeline with no specified cadence — making it easy to never dispatch in practice.
**Current state:** **[PARTIAL]** Observer behavior is documented in multiple places (`workflows/multi-agent-pipeline.md`, scorecard docs), but Coordinator dispatch trigger rules are still not explicit.
**What to add:**
- Define trigger conditions in `agents/coordinator/skills.md`: dispatch Observer after every 3rd feature completion, after any convergence escalation, and on explicit Coordinator request
- Define what "weekly pattern report" means: manual trigger via slash command or Coordinator initiates after N features
- Add Observer dispatch to the Coordinator's post-Done workflow

### Git Branching and PR Strategy
**What it is:** The pipeline produces merge-ready code but says nothing about git workflow — feature branches, PR naming, review process, or merge strategy. The human is left to figure this out.
**Current state:** Still valid gap (no canonical branching/PR policy in coordinator workflow docs).
**What to add:**
- Recommended branch naming convention per feature: `feature/<SPEC-ID>-<feature-name>`
- PR description template that references spec hash, ADR path, and security sign-off status
- Coordinator guidance: when to create a branch (at TDD dispatch), when to signal PR-ready (at Done State)
- Note on merge strategy trade-offs (squash vs merge commit vs rebase) relative to spec traceability

---

## Priority 2 — Consensus Orchestration

### Multi-LLM Consensus Modes and Guardrails **[PARTIAL]**
**What it is:** `/consensus` and `skills/swarm-consensus/SKILL.md` exist, but they need stronger orchestration rules for architecture/data-modeling debates and reproducible runs with explicit mode control.
**Current state:** Core orchestration flow is implemented; this section now tracks only remaining gaps.
**Known issue:** Consensus runs can still misreport exact peer model/version identifiers in some environments; preflight/version capture needs stricter normalization and verification.
**What to add:**
- Normalize and verify peer model/version reporting across CLI outputs so preflight and reports always show accurate model IDs and versions.

---

## Priority 3 — Interoperability

### Protocol Split: MCP + A2A
**What it is:** Two distinct integration patterns for extending the pipeline.
- **MCP (Model Context Protocol):** Tool and resource provisioning standard. Already the de-facto standard for connecting agents to external tools/data.
- **A2A (Agent-to-Agent, Google):** Protocol for agent-to-agent collaboration across systems/orgs. Still early — limited adoption as of early 2026.
**Why it matters:** MCP hardening is practical now. A2A is worth tracking but not worth building to yet.
**What to add:**
- `interop/` docs folder
- MCP integration guide — how to add MCP tools to each agent role, what permissions each role needs, security surface
- External Agent Gateway role definition — a lightweight broker agent that validates incoming A2A requests before they touch the pipeline
- A2A watch notes — revisit when adoption signal is clearer
**Defer:** Full A2A implementation until protocol stabilizes

---

## Priority 5 — Polish

### Spec-Kit Command Contract Parity **[PARTIAL]**
**What it is:** Command files (`.claude/commands/`) currently lack machine-readable frontmatter. Spec-kit's command format includes `handoffs:` and `scripts:` fields that enable automated contract validation — e.g., checking that `/plan` references an approved spec before executing.
**Current state:** Command files exist in `templates/commands/` (including `spec`, `clarify`, `plan`, `tasks`, `implement`, `review`, `consensus`, `agent`). Frontmatter contracts are still not present.
**What to add:**
- Frontmatter schema for command files — `description`, `requires`, `handoffs`, `produces`, and optional `mode`
- Update all command files in `templates/commands/` to include frontmatter
- Coordinator skills update — teach it to validate command preconditions against frontmatter `requires` fields before dispatch
**References:** github/spec-kit command format (`github-spec-kit/templates/commands/specify.md`)

---

## Notes

- None of these require Python or code — all are markdown documentation, agent instruction files, and schema definitions
- A2A: monitor but don't build to yet
- Items marked [PARTIAL] have a head start from the speckit integration already done in this repo
