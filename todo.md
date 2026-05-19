# AI Dev Shop (speckit edition) — Todo

Paradigms and improvements to research, document, and wire into the pipeline.
All items are documentation/agent-instruction work — no code required unless noted.

Items marked **[PARTIAL]** have foundational work already in this repo.

---

## Quick Status Snapshot

- AGENTS.md Map Reduction: **DONE / MONITORED**
- Observer Agent Operational Cadence: **DONE / MONITORED**
- Harness Audit Follow-Ons (all 10 items): **DONE**
- Git Branching and PR Strategy: **DONE**
- Multi-LLM Consensus Modes and Guardrails: **OPEN / PARTIAL** (consensus + preflight exists; strict model/version normalization still open)
- Agent Eval Depth: **OPEN / PARTIAL** (framework + taxonomy done; need to regenerate Architect/CR seeds at staff+ complexity)
- Protocol Split: MCP + A2A: **OPEN** (MCP practical now; A2A defer)
- Spec-Kit Command Contract Parity: **OPEN / PARTIAL** (command templates exist; frontmatter contracts still missing)
- System Design Skill Coverage: **OPEN / PARTIAL** (root skill exists; depth topics pending)

---

## De-Noise and Effectiveness

### AGENTS.md Map Reduction **[DONE / MONITORED]**
**What it is:** Shrink `AGENTS.md` into a tighter runtime map so the root instruction surface routes agents instead of re-explaining the whole framework.
**Current state:** Detailed startup/invocation/checkpoint content now lives in `framework/operations/pipeline-quickstart.md`, and the full agent roster now lives in `framework/routing/agent-index.md`. `AGENTS.md` remains the runtime map and startup contract and is back under the safer size target.
**What to add next:**
- Keep startup/mode/routing semantics at the root and move deeper operating detail into linked canonical docs.
- Remove repeated explanations that already live in `agents/`, `framework/workflows/`, `skills/`, or `harness-engineering/`.
- Re-run the doc-garden audit after the reduction and treat the root-file line count as a tracked harness metric.

### Context De-Noise Hardening
**What it is:** Reduce instruction noise and improve execution reliability by moving guardrails out of prose and into enforceable structure.
**Current state:** **Framework complete** in `maintainers/skill-md-format/` (standards, gates, tracker, failure matrix, overlays).
**Scope guardrail:** Current rollout covers `skills/vercel-*` and imported `skills/superpowers-*`; expand further only with explicit human approval.
**What to add next:**
- Skill transformation rollout: rewrite skills in phases using the new format (`Execution` / `Guardrails` / `Output` / `Reference`).
- Source preservation: keep existing long-form or imported source skills as canonical references while overlays/new versions are validated.
- Naming convention for rollout: preserve source docs as `ORIGINAL.md`; keep `SKILL.md` as AI/LLM execution-optimized; allow an optional root `README.md` for layout or usage notes; use `references/` for examples, active support docs, and preserved support-source files.
- Comparison workflow: for each rewritten skill, keep side-by-side diff notes and acceptance checks before promotion.

**Note:** Skill-MD-Format framework is complete, but the transformation still needs to be applied across the `skills/` folder in controlled rollout phases.
**Note:** `agents/*/skills.md` should be transformed in a second phase after `skills/` rollout is validated.
**Rollout safety gates:**
- Keep old or imported source files as `ORIGINAL.md` while validating new execution-format `SKILL.md`.
- Require a side-by-side promotion checklist (non-negotiable gates, routing correctness, handoff compatibility) before replacement.
- Roll out by agent cluster with pilot validation before broad replacement.

---

## External OSS Intake

### Code Report Video Intake Queue
**Source video:** `https://www.youtube.com/watch?v=Xn-gtHDsaPY`
**What it is:** Curated list of outside open-source agent/tooling repos mentioned in a March 12, 2026 Code Report video that are worth evaluating for future adoption.
**Why it matters:** These projects may improve agent staffing, prompt evaluation, context management, UI quality, forecasting, and model control. They should be reviewed systematically instead of getting installed ad hoc.
**Current state:** `agency-agents` has already been downloaded for review. Several other repo names came from auto-transcript text and need exact repo confirmation before installation.
**What to add next:**
- Create a lightweight intake checklist for external repos: exact repo URL, license, maintenance status, install method, security risk, overlap with current toolkit, and likely integration point.
- Separate `adopt soon`, `learn from only`, and `skip` outcomes after review so the repo folder does not become a dumping ground.
- Capture findings in a dedicated external-repos evaluation doc once the review pass starts.

**Review queue:**
- `agency-agents`
  - Why it is useful: broad agent-role starter kit that can accelerate experimentation with specialist personas and startup-like multi-agent staffing patterns.
  - Likely value here: role ideas, agent templates, and prompt structure comparisons against this toolkit's current agent set.
- `archon` — `https://github.com/coleam00/archon`
  - Why it is useful: open-source harness/workflow engine for AI coding with YAML-defined workflows, validation gates, isolated git worktrees, and mixed deterministic + AI execution nodes.
  - Likely value here: compare its workflow engine, worktree isolation model, approval gates, artifact flow, and repo-local workflow definitions against AI Dev Shop's coordinator/pipeline design.
  - Review intent: `learn from only` for now. Revisit later to extract concrete ideas worth adopting or explicitly rejecting after a focused comparison pass.
- `squad`
  - Why it is useful: multi-agent team runtime with persistent in-repo agent state, routing, orchestration logs, skills, templates, and sample projects.
  - Likely value here: go through the repo's projects/samples/templates and extract anything useful for coordinator routing, persistent agent memory, context hygiene, observability, and team bootstrap patterns.
- `promptfoo` (transcript said "Prompt Fu")
  - Why it is useful: prompt testing and evaluation framework for model/prompt comparisons, regressions, and adversarial red-team checks.
  - Likely value here: could strengthen prompt, rubric, and red-team validation workflows for agent prompts and user-facing AI features.
- `Mirofish` / `Mirrorish` / `Micro Fish` (exact repo name to confirm from transcript)
  - Why it is useful: described as a multi-agent prediction engine that ingests trend/news data and simulates agent discussion around it.
  - Likely value here: idea source for trend analysis, market-sensing agents, or multi-agent forecasting patterns.
- `Impeccable` (exact repo name to confirm from transcript)
  - Why it is useful: frontend-design-oriented command/skill set focused on simplifying and improving AI-generated UI.
  - Likely value here: possible source material for VibeCoder, UX/UI Designer, or frontend quality skills, especially around simplification and visual polish.
- `Open Viking` (exact repo name to confirm from transcript)
  - Why it is useful: described as an AI-agent memory/context database organized around filesystem-based resources, skills, and tiered loading.
  - Likely value here: directly relevant to context hygiene, tiered loading, token reduction, and long-term memory organization for agents.
- `Heretic` (exact repo name and safety posture to confirm before any install)
  - Why it is useful: described as a tool for removing model guardrails via "obliteration".
  - Likely value here: mostly research value around model-control techniques; high safety/governance review required before touching it.
- `Nano Chat` / `nanochat` (exact repo name to confirm from transcript)
  - Why it is useful: end-to-end small-LLM training pipeline including tokenization, pretraining, fine-tuning, evaluation, and UI.
  - Likely value here: useful for learning the full LLM stack and evaluating whether a small controllable local model could support narrow internal tasks.

**Do not prioritize from this video:**
- `Recall AI`
  - Sponsor mention, not part of the open-source install queue.

---

## Pipeline Gaps

### Harness Audit Follow-Ons **[DONE]**
**Completed 2026-05-18/19.** All 10 items resolved. Key deliverables:
- `framework/contracts/` — computational controls, runtime validation, architecture fitness, enforcement, bootstrap
- `harness-engineering/sensors/` — dead-code, dependency-drift, coverage-quality
- `harness-engineering/quality/code-documentation-standards.md`
- `harness-engineering/quality/model-upgrade-program.md`
- `framework/workflows/git-strategy.md`
- `framework/templates/evaluator-contract-template.md` (strengthened with Evidence Surfaces + Fail Conditions)
- `harness-engineering/validators/validate_contracts.py`
- `harness-engineering/harness-evals/` — 3 suites, 20 seeds, structured JSON grading
- Items 9-10 closed (existing surfaces sufficient, terminology already correct)

### Specialized Harness Follow-Ons From Video **[OPEN]**
**Source video:** `https://www.youtube.com/watch?v=I2K81s0OQto`
**What it is:** Follow-up ideas from a harness-engineering video focused on specialized multi-stage business workflows, deterministic rails, subagents, observability, and checkpointed execution.
**Why it matters:** Most repo-level harness work is now in place, but these items push the framework further toward specialized downstream harnesses for compliance, legal, financial, and other long-running business processes.
**What to add:**
- Stage-output schema enforcement: add stricter machine-validated output contracts for multi-stage handoffs instead of relying only on markdown structure and prose rules.
- Model-tier routing policy: document when to use stronger orchestrator models versus cheaper narrower subagents, including cost/quality tradeoff guidance.
- Phase-checkpoint template for downstream harnesses: require each major phase to write resumable checkpoint artifacts so long-running workflows can restart from phase `N` instead of from scratch.
- Specialized non-code validation-loop templates: add downstream templates for things like clause-vs-playbook checks, fact-check loops, and rule-based business validation beyond software testing.
- Fixed-plan vs dynamic-plan design guidance: document when a workflow should stay on deterministic fixed rails versus when dynamic replanning is acceptable.
- Tool-approval patterns for risky actions: add stronger downstream guidance for actions that should always require explicit human approval before write/push/send/publish behavior.
- Observability and trace design for specialized harnesses: define what a downstream harness should log about phase timing, retries, subagent activity, and validation outcomes without bloating the main context.

### React Component Testing Policy
**What it is:** UI testing is often skipped by LLMs. Need a strict policy enforcing React component test creation.
**Current state:** Added to `harness-engineering/quality/react-component-testing-policy.md`.
**What to add:** Enforce the policy across TDD and Programmer routing. Update skill definition files and evaluation checklists.

### Debug Playbook
**What it is:** Agents need a structured debug loop (reproduce, isolate, instrument, hypothesize, fix) to prevent thrashing.
**Current state:** Added to `harness-engineering/quality/debug-playbook.md`.
**What to add:** Enforce trace requirements and escalation rules across Programmer and QA roles.

### Observer Agent Operational Cadence
**What it is:** The Observer role and output format are well-defined but its trigger is not. Currently it "runs alongside" the pipeline with no specified cadence — making it easy to never dispatch in practice.
**Current state:** **[PARTIAL]** Observer behavior is documented in multiple places (`framework/workflows/multi-agent-pipeline.md`, scorecard docs), but Coordinator dispatch trigger rules are still not explicit.
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

### Testability Anti-Pattern Reporting
**What it is:** Ensure code anti-patterns that make testing hard are consistently surfaced to humans during implementation and review.
**Current state:** Catalog added in quality docs; enforcement across rewrite/rollout flow still pending.
**What to add:**
- Use `harness-engineering/quality/testability-antipatterns.md` as the canonical catalog.
- Require anti-pattern findings to be reported in handoff summaries with location, impact, and remediation route.
- Treat repeated unresolved anti-patterns as escalation candidates instead of silently continuing.

### Programmer Ambient Fast-Feedback Testing
**What it is:** Give Programmer immediate test breakage feedback during implementation without turning TestRunner into a continuous heavy agent.
**Current state:** Concept agreed in review discussions; not implemented.
**What to add (policy/docs only for now):**
- Require Programmer to run a fast local watcher during implementation (unit tests, plus optional small changed-file integration subset).
- Do not stream raw watcher logs into agent context; use signal-based summaries only.
- Define stable-failure alert criteria explicitly: only alert after debounce (10-20s) and 2 consecutive failing runs.
- Add anti-noise rules: alert budget (max N per interval), changed-file scope filtering, and compact payloads only (test id, short error, first failing frame).
- Define recovery-state behavior explicitly: after first alert, suppress repeat alerts for that same failure until it returns green; alert again only on future green -> failing regression.
- Preserve TestRunner as the formal gate for full suites, coverage profile checks, spec-hash validation, and certification artifact generation.
- Document this split in `agents/programmer/skills.md` and coordination docs; defer any scripting/automation until a later phase.

---

## Consensus Orchestration

### Execution Topology Default: Strong Single-Agent Baseline First
**What it is:** Default the framework toward a strong single-agent baseline for most implementation work, and treat delegated specialist agents as an exception that must justify their added coordination cost.
**Why it matters:** Current research does **not** support assuming that same-model multi-agent workflows are better by default. In many comparisons, a strong single-agent baseline matches or beats homogeneous multi-agent setups once compute is normalized.
**Current state:** The toolkit supports delegated specialist routing, but the docs should reflect that this is not automatically the better path for quality, cost, or long-horizon work.
**Research-backed default to document:**
- Prefer one active agent/session with compact offloads, explicit review passes, and structured handoffs as the baseline.
- Do **not** treat role labels inside one shared context as true adversarial independence.
- Use delegated specialist agents only when there is a concrete reason:
  - true isolated context windows are available
  - model heterogeneity is available and useful
  - the task is long-horizon enough that keeping implementation traces out of the main context is materially helpful
  - independent review pressure is important enough to justify extra token and orchestration cost
**What to add:**
- Update routing docs so Coordinator defaults to the single-agent baseline unless an exception condition is met.
- Add explicit language that same-model multi-agent comparisons must beat the single-agent baseline, not just a weak one-pass baseline.
- Keep any future topology eval bounded to exception-testing, not as an open question about the default path.
**Likely files to inspect/update first:**
- `agents/coordinator/skills.md`
- `harness-engineering/runtime/subagent-usage-policy.md`
- `harness-engineering/runtime/context-offloading.md`
- `harness-engineering/quality/evaluation-loops.md`
**Done when:**
- The docs state a clear default: start single-agent, escalate to delegated specialists only when isolation, heterogeneity, or review independence is expected to add value.

### Multi-LLM Consensus Modes and Guardrails **[PARTIAL]**
**What it is:** `/consensus` and `skills/swarm-consensus/SKILL.md` exist, but they need stronger orchestration rules for architecture/data-modeling debates and reproducible runs with explicit mode control.
**Current state:** Core orchestration flow is implemented; this section now tracks only remaining gaps.
**Known issue:** Consensus runs can still misreport exact peer model/version identifiers in some environments; preflight/version capture needs stricter normalization and verification.
**What to add:**
- Normalize and verify peer model/version reporting across CLI outputs so preflight and reports always show accurate model IDs and versions.

---

## Interoperability

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

## Polish

### Spec-Kit Command Contract Parity **[PARTIAL]**
**What it is:** Command files (`.claude/commands/`) currently lack machine-readable frontmatter. Spec-kit's command format includes `handoffs:` and `scripts:` fields that enable automated contract validation — e.g., checking that `/plan` references an approved spec before executing.
**Current state:** Command files exist in `framework/slash-commands/` (including `spec`, `clarify`, `plan`, `tasks`, `implement`, `review`, `consensus`, `agent`). Frontmatter contracts are still not present.
**What to add:**
- Frontmatter schema for command files — `description`, `requires`, `handoffs`, `produces`, and optional `mode`
- Update all command files in `framework/slash-commands/` to include frontmatter
- Coordinator skills update — teach it to validate command preconditions against frontmatter `requires` fields before dispatch
**References:** github/spec-kit command format (`github-spec-kit/framework/templates/commands/specify.md`)

---

### System Design Skill Coverage Hardening **[PARTIAL]**
**What it is:** The new `skills/system-design/` package exists, but it is still stronger on high-level topology and generic distributed-systems framing than on correctness, operational sharp edges, and security-depth topics.
**Current state:** **[PARTIAL]** Root skill plus references are in place; coverage is good enough to start, but not yet comprehensive against the full recurring system-design checklist.
**What to add:**
- Add reference coverage for hot keys / hot rows
- Add reference coverage for precomputation
- Add reference coverage for batching
- Deepen async processing guidance
- Add explicit idempotency guidance
- Add explicit deduplication guidance
- Add transaction tradeoff guidance
- Add concurrency issue patterns and failure modes
- Add health check guidance
- Add graceful degradation patterns
- Deepen authn/authz treatment
- Deepen secrets-management treatment
- Deepen rate-limiting treatment
- Add abuse-detection coverage

---

## Agent Eval Depth

### Deep-Dive: Production-Level Complexity for Agent Evals **[PARTIAL]**
**What it is:** The current agent evals (Architect, Code Review) are shallow — they test process compliance and textbook bugs, not the production-level failures that LLMs actually struggle with. The Programmer evals are the exception and already have more depth.
**Why it matters:** Shallow evals give false confidence and don't surface agent skill gaps. The evals should tell you what skills to build next by revealing what classes of failure the agents cannot reason about.
**What was done:**
- Added a **Domain Complexity Taxonomy** to `eval-coverage-model.md` with five tiers: `textbook`, `production`, `staff`, `principal`, `distinguished`
- **80% of seeds must be staff/principal/distinguished** (85% for Architect/CR)
- Defined 14 complexity categories (concurrency composition, distributed state divergence, scale threshold collapse, retry amplification, data loss windows, security escalation chains, invariant erosion, observability blind spots, configuration interaction, temporal coupling, migration hazards, resource exhaustion leaks, consensus violations, type system escapes)
- Added a full **Engineering Concept Taxonomy** (~50 concept codes across 6 domains: Systems & Infrastructure, Data & Storage, Concurrency & Performance, Security & Trust, Correctness & Logic, Architecture & Design, Testing & Quality)
- Added **concept probing rules**: Architect must touch 15+ concepts, Code Review 20+, Programmer 25+
- Added **seed design criteria** to `function-quality-seeded-evals.md` with concrete examples at each tier (staff through distinguished)
- Updated `seed-catalog.tsv` schema with `domain_complexity`, `complexity_category`, and `engineering_concepts` columns
- Added per-concept and per-category catch rates as primary diagnostics
- Added **skill gap diagnostic reporting**: concepts with < 50% catch rate are confirmed gaps, reported with full context for human decision-making (no automatic skill creation)
- **Eval-driven development** available as optional human-initiated workflow: write seeds → verify failure → build skill → re-eval
- Minimum seed count for Architect/CR/Security: **72+ seeds**
**What still needs to happen:**
- Regenerate Architect eval seeds with emergent-tier defects (current 59 seeds are all textbook/production process compliance)
- Regenerate Code Review eval seeds with production and emergent defects (current 21 seeds are mostly textbook)
- Add `domain_complexity` and `complexity_category` columns to existing seed-catalog TSVs
- Update the scorer (`score_eval_suite.py`) to compute per-complexity-category catch rates
- Update the validator (`validate_eval_suite.py`) to enforce the depth floors
- Run the new suites and use the category-level miss data to prioritize new skills
**Likely files to inspect/update first:**
- `harness-engineering/agent-evals/architect-evals/benchmark-suite/seed-catalog.tsv`
- `harness-engineering/agent-evals/code-review-evals/benchmark-suite/seed-catalog.tsv`
- `harness-engineering/agent-evals/programmer-evals/benchmark-suite/seed-catalog.tsv`
- `harness-engineering/quality/scripts/score_eval_suite.py`
- `harness-engineering/validators/validate_eval_suite.py`
**Done when:**
- Architect and Code Review eval suites include emergent (Staff+) seeds that test genuinely dangerous, hard to solve, or hard to even see production failures
- Per-complexity-category catch rates are reported in eval summaries
- Category-level misses directly inform which skills to build next
- The eval creation protocol structurally prevents future suites from being all-textbook

---

## Notes

- None of these require Python or code — all are markdown documentation, agent instruction files, and schema definitions
- A2A: monitor but don't build to yet
- Items marked [PARTIAL] have a head start from the speckit integration already done in this repo
