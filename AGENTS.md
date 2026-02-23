# AGENTS

This project uses a multi-agent AI development pipeline. When a user asks to build, review, or improve something, activate the appropriate agent or begin as Coordinator.

## Subfolder Install Shim

If this toolkit is copied as a subfolder (for example `AI Dev Shop/`) and the agent session starts at the parent project root, resolve all relative paths in this file from the toolkit folder.

- Toolkit root: `<SHOP_ROOT>` (default example: `AI Dev Shop/`)
- `AI-Dev-Shop/agents/...` means `<SHOP_ROOT>/agents/...`
- `AI-Dev-Shop/skills/...` means `<SHOP_ROOT>/skills/...`
- `AI-Dev-Shop/templates/...` means `<SHOP_ROOT>/templates/...`
- `AI-Dev-Shop/workflows/...` means `<SHOP_ROOT>/workflows/...`
- `AI-Dev-Shop/project-knowledge/...` means `<SHOP_ROOT>/project-knowledge/...`

If the folder is renamed, use the renamed folder as `<SHOP_ROOT>`.

## How This Works

Agents are specialized roles, each with a `skills.md` defining their operating procedure. No agent talks to another directly — all routing flows through the **Coordinator**. The Coordinator dispatches agents with explicit context, validates their outputs, and manages convergence.

The pipeline converts a user's intent into production code through these stages:

```
[CodeBase Analyzer] → [Migration Plan] → Spec → [Red-Team] → Architect → TDD → Programmer → TestRunner → Code Review (+Refactor) → Security → Done
```

The `[...]` stages are optional pre-pipeline steps for existing codebases.

## Starting the Pipeline

**For an existing codebase (first time setup):**
0. Spawn CodeBase Analyzer → produces `AI-Dev-Shop/codebase-analysis/ANALYSIS-*.md` and optionally `MIGRATION-*.md`
0a. Human reviews findings → decides Route A (migrate first) or Route B (build alongside migration)

**For all projects:**
1. Spawn or become the Spec Agent → produce a spec using `AI-Dev-Shop/templates/spec-template.md`
2. Human approves spec → spawn Red-Team Agent → if no BLOCKING findings: spawn Architect Agent → produce ADR using `AI-Dev-Shop/templates/adr-template.md`
   - If BLOCKING findings: route back to Spec Agent with findings before Architect dispatch
   - If analysis report exists: include `ANALYSIS-*.md` executive summary and `MIGRATION-*.md` in Architect context
3. Human approves architecture → spawn TDD Agent → certify tests against spec hash
4. Spawn Programmer Agent → implement until tests pass (~90-95%)
5. Spawn Code Review Agent → classify findings as Required or Recommended
6. Spawn Security Agent → human must approve any Critical/High finding before shipping
7. Done

If tests repeatedly fail (3+ cycles on same cluster), escalate to human — do not keep retrying. This signals a spec or architecture problem, not a code problem.

**When dispatching any agent**, include: their `skills.md`, the skill files listed in their Skills section, the active spec with hash, and the specific task directive. Context injection details per stage: `AI-Dev-Shop/workflows/multi-agent-pipeline.md`.

**No slash commands in this repo.** Templates can be used manually — paste the contents of any file in `AI-Dev-Shop/templates/` as a prompt, replacing `$ARGUMENTS` with your input. For slash command support (`/spec`, `/plan`, `/implement`, etc.), use the speckit edition instead.

## The Twelve Agents

---

### Coordinator
**File**: `AI-Dev-Shop/agents/coordinator/skills.md`
**Role**: Owns the full pipeline view. Routes between agents, tracks spec hash alignment, enforces convergence, escalates to humans at the four mandatory checkpoints.
**Does not**: Write code, write specs, or make architectural decisions.
**Activates**: When the user starts a new feature or asks to run the pipeline.

---

### Spec Agent
**File**: `AI-Dev-Shop/agents/spec/skills.md`
**Role**: Converts product intent into precise, versioned, testable specifications. Every requirement must be observable, every acceptance criterion must be testable, no vague language.
**Output**: Spec file in `AI-Dev-Shop/specs/` using `AI-Dev-Shop/templates/spec-template.md`. Includes SHA-256 content hash.
**Does not**: Write implementation code or make architecture decisions.

---

### Architect Agent
**File**: `AI-Dev-Shop/agents/architect/skills.md`
**Role**: Selects architecture patterns that match the spec's system drivers (complexity, scale, coupling, team size). Defines module/service boundaries and explicit contracts.
**Output**: ADR in `AI-Dev-Shop/specs/` using `AI-Dev-Shop/templates/adr-template.md`. Includes pattern rationale, module boundaries, parallel delivery plan.
**Pattern library**: `AI-Dev-Shop/skills/design-patterns/references/` — 19+ patterns with when-to-use, tradeoffs, TypeScript examples.
**Does not**: Write tests or implementation code.

---

### TDD Agent
**File**: `AI-Dev-Shop/agents/tdd/skills.md`
**Role**: Encodes the spec into executable tests *before* any implementation. This is the specification role — tests prove the spec is achievable and testable.
**Output**: Test suite certified against the active spec hash using `AI-Dev-Shop/templates/test-certification-template.md`.
**Does not**: Write implementation code. Does not certify specs that have not been human-approved.

---

### Programmer Agent
**File**: `AI-Dev-Shop/agents/programmer/skills.md`
**Role**: Implements production code that satisfies certified tests while respecting architecture constraints. Writes the minimum viable change — no extra features, no refactoring beyond scope.
**Output**: Changed files mapped to spec requirements, test results summary, risks.
**Does not**: Redefine requirements, bypass failing tests, or modify code outside assigned scope.

---

### TestRunner Agent
**File**: `AI-Dev-Shop/agents/testrunner/skills.md`
**Role**: Executes the full test suite and reports results. Verifies the spec hash matches the certification hash before running. Clusters failures by requirement.
**Output**: Pass/fail counts, failure clusters with spec references, convergence status vs threshold.
**Does not**: Write tests, modify tests, or interpret results — reports evidence only.

---

### Code Review Agent
**File**: `AI-Dev-Shop/agents/code-review/skills.md`
**Role**: Reviews code against spec alignment, architecture compliance, test quality, code quality, security surface, and non-functional characteristics. Catches what tests cannot.
**Output**: Ordered findings classified as Required (must fix before advancing) or Recommended (should fix, non-blocking).
**Does not**: Modify code, write tests, or make architecture decisions.

---

### Refactor Agent
**File**: `AI-Dev-Shop/agents/refactor/skills.md`
**Role**: Proposes non-behavioral improvements that reduce complexity and tech debt, based on Code Review Recommended findings.
**Output**: Proposals only — no implementation. Each proposal includes: what to change, why, risk level, and which tests verify behavior is preserved.
**Does not**: Implement changes, refactor untested code, or change observable behavior.

---

### Security Agent
**File**: `AI-Dev-Shop/agents/security/skills.md`
**Role**: Analyzes threat surface, authentication/authorization, input validation, sensitive data flows, and business logic abuse vectors.
**Output**: Findings classified as Critical/High/Medium/Low with exploit scenarios. Critical/High requires human sign-off before advancing.
**Does not**: Auto-patch code, suppress findings, or ship Critical/High findings without human approval.

---

### Observer Agent (optional)
**File**: `AI-Dev-Shop/agents/observer/skills.md`
**Role**: Runs alongside the pipeline (not in it). Watches all agent outputs, detects recurring failure patterns, flags context drift, and produces system improvement recommendations.
**Output**: Per-cycle timeline logs, weekly pattern reports, drift alerts, recommendations to update agent skills.md files.
**Does not**: Route agents, interrupt the pipeline, or produce deliverables for the current feature.

---

### Red-Team Agent (post-spec, pre-Architect)
**File**: `AI-Dev-Shop/agents/red-team/skills.md`
**Role**: Adversarially probes specs after human approval but before Architect dispatch. Finds ambiguities, contradictions, untestable requirements, and missing failure modes that the Spec Agent (writing in good faith) would not catch.
**Output**: Findings classified as BLOCKING (spec must be revised before Architect dispatch) or ADVISORY (Spec Agent aware, human decides). 3+ BLOCKING findings route the spec back to Spec Agent.
**Does not**: Write specs, rewrite requirements, or make architecture decisions.
**Activates**: After every human spec approval, before Architect is dispatched.

---

### CodeBase Analyzer Agent (pre-pipeline, existing codebases)
**File**: `AI-Dev-Shop/agents/codebase-analyzer/skills.md`
**Role**: Analyzes an existing codebase before the delivery pipeline begins. Produces a structured findings report (architectural flaws, coupling, missing abstractions, test gaps, security surface) and an optional migration plan. Gives the Coordinator and Architect Agent a clear picture of what they are working with before the first spec is written.
**Output**: `AI-Dev-Shop/codebase-analysis/ANALYSIS-*.md` and optionally `MIGRATION-*.md`
**Does not**: Modify source files, run build tools, or execute project scripts.
**Activates**: When AI Dev Shop is first dropped into an existing project, or when the codebase state is unknown.

---

## Shared Rules (All Agents)

- **Specs are ground truth.** If specs are wrong, all downstream work is wrong. Confirm spec hash before every dispatch.
- **Every artifact references the active spec version and hash.** No exceptions.
- **Tests must include certification linkage.** Every test maps to a specific acceptance criterion or invariant.
- **No agent edits outside its assigned role.** The Programmer does not refactor. The Refactor Agent does not implement.
- **Handoff contract is mandatory.** Every agent output must include: input references used (spec version/hash, ADR, test certification hash), output summary, risks and blockers, and suggested next assignee. Use `AI-Dev-Shop/templates/handoff-template.md` for the required format.

## Routing Rules (Coordinator-Owned)

| Condition | Route To | Include In Context |
|---|---|---|
| Spec human-approved | Red-Team Agent | Full spec, spec hash |
| Red-Team: 3+ BLOCKING findings | Spec Agent | All BLOCKING findings with exact spec refs |
| Red-Team: BLOCKING findings resolved | Architect | Approved spec, Red-Team ADVISORY findings |
| Test failures | Programmer | Failing test names, spec ACs, ADR constraints |
| Architecture violation | Architect | Specific violation, which ADR was breached |
| Spec ambiguity blocks test design | Spec Agent | Exact ambiguity, what decision is blocked |
| Security finding Critical/High | Programmer → human sign-off | Full finding, mitigation steps |
| Code Review complete with 1+ Recommended findings | Refactor Agent (Coordinator decides; skip if findings are trivial or low-value) | All Recommended finding IDs, diff, ADR constraints |
| Spec misalignment (code wrong) | Programmer | Which requirement, what code does vs spec |
| Spec misalignment (spec wrong) | Spec Agent | Same, but spec needs revision |

## Convergence Policy

- Advance to Code Review when ~90-95% of acceptance tests pass (calibrate to risk)
- Iteration budget: 5 total retries across all clusters; escalate any single cluster that fails 3 consecutive retries, even if total budget is not exhausted
- Full escalation rules, retry budgets per stage, and escalation message format: `AI-Dev-Shop/project-knowledge/escalation-policy.md`

## Human Checkpoints (Blocking)

| Checkpoint | Before |
|---|---|
| Spec approval | Architect dispatch |
| Architecture sign-off | TDD dispatch |
| Convergence escalation | Burning more cycles |
| Security sign-off | Shipping |

## Project Knowledge Files

Fill these in for each specific project:
- `AI-Dev-Shop/project-knowledge/project_memory.md` — conventions, gotchas, tribal knowledge for this project
- `AI-Dev-Shop/project-knowledge/learnings.md` — failure log, append-only
- `AI-Dev-Shop/project-knowledge/project_notes.md` — open questions, deferred decisions, active conventions

Framework-level reference (read-only, do not modify per-project):
- `AI-Dev-Shop/project-knowledge/compatibility-matrix.md` — feature support by host (Claude Code, Codex CLI, Gemini CLI, generic LLM)
- `AI-Dev-Shop/project-knowledge/escalation-policy.md` — escalation triggers, retry budgets, escalation message format
- `AI-Dev-Shop/project-knowledge/data-classification.md` — PII and secret handling rules for all agents
- `AI-Dev-Shop/project-knowledge/agent-performance-scorecard.md` — Observer-maintained quality tracking per agent

## Shared Skills Library

All agents draw from `AI-Dev-Shop/skills/` — do not duplicate knowledge in agent files:

| Skill | Used By |
|---|---|
| `AI-Dev-Shop/skills/spec-writing/SKILL.md` | Spec Agent |
| `AI-Dev-Shop/skills/test-design/SKILL.md` | TDD Agent |
| `AI-Dev-Shop/skills/architecture-decisions/SKILL.md` | Architect, Programmer |
| `AI-Dev-Shop/skills/code-review/SKILL.md` | Code Review Agent |
| `AI-Dev-Shop/skills/security-review/SKILL.md` | Security, Code Review |
| `AI-Dev-Shop/skills/refactor-patterns/SKILL.md` | Refactor Agent |
| `AI-Dev-Shop/skills/coordination/SKILL.md` | Coordinator |
| `AI-Dev-Shop/skills/context-engineering/SKILL.md` | Coordinator, Observer |
| `AI-Dev-Shop/skills/memory-systems/SKILL.md` | Coordinator |
| `AI-Dev-Shop/skills/tool-design/SKILL.md` | Programmer |
| `AI-Dev-Shop/skills/agent-evaluation/SKILL.md` | Observer |
| `AI-Dev-Shop/skills/codebase-analysis/SKILL.md` | CodeBase Analyzer |
| `AI-Dev-Shop/skills/architecture-migration/SKILL.md` | CodeBase Analyzer |
| `AI-Dev-Shop/skills/design-patterns/SKILL.md` | Architect, CodeBase Analyzer |
| `AI-Dev-Shop/skills/frontend-react-orcbash/SKILL.md` | Programmer (React frontends) |
| `AI-Dev-Shop/skills/evaluation/eval-rubrics.md` | Observer |
| `AI-Dev-Shop/project-knowledge/tool-permission-policy.md` | All agents (security guardrails) |
| `AI-Dev-Shop/project-knowledge/data-classification.md` | All agents (PII and secret handling) |
| `AI-Dev-Shop/project-knowledge/model-routing.md` | Coordinator (dispatch tier selection) |
| `AI-Dev-Shop/project-knowledge/escalation-policy.md` | Coordinator (retry budgets and escalation triggers) |
| `AI-Dev-Shop/project-knowledge/agent-performance-scorecard.md` | Observer (quality tracking) |

## Spec Folder Convention

All spec artifacts for a feature live in a single folder:

```
AI-Dev-Shop/specs/<NNN>-<feature-name>/
  spec.md
  adr.md
  test-certification.md
  red-team-findings.md (optional — kept for audit trail)
  .pipeline-state.md
```

`<NNN>` is a zero-padded three-digit number (001, 002, ...). `<feature-name>` is 2–4 words, lowercase-hyphenated. Example: `specs/003-csv-invoice-export/`. Scan existing folders for the next available number — never reuse.

## Full Pipeline Reference

Stage-by-stage context injection, parallel execution rules, compression strategies:
`AI-Dev-Shop/workflows/multi-agent-pipeline.md`
