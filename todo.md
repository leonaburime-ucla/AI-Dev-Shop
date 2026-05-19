# AI Dev Shop (speckit edition) — Todo

Paradigms and improvements to research, document, and wire into the pipeline.
All items are documentation/agent-instruction work — no code required unless noted.

Items marked **[PARTIAL]** have foundational work already in this repo.

---

## Quick Status Snapshot

- AGENTS.md Map Reduction: **DONE / MONITORED** (root map was slimmed to the safer range and detail moved into local quickstart/index docs; keep watching for re-expansion)
- Observer Agent Operational Cadence: **DONE / MONITORED** (cadence is now explicit in Observer, Coordinator, and workflow docs; keep it aligned as the pipeline evolves)
- Harness Audit Follow-Ons (Executable Controls / Runtime Validation / Drift): **PARTIAL** (Critical items 1-4 done; High items 5-7 open)
- Git Branching and PR Strategy: **OPEN**
- Multi-LLM Consensus Modes and Guardrails: **OPEN / PARTIAL** (consensus + preflight exists; strict model/version normalization still open)
- Protocol Split: MCP + A2A: **OPEN**
- Spec-Kit Command Contract Parity: **OPEN / PARTIAL** (command templates exist; frontmatter contracts still missing)

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

### Harness Audit Follow-Ons (Claude Opus 4.6 + Gemini 3.1 + Coordinator) **[OPEN]**
**What it is:** Consolidated follow-on work from the harness review comparing the current framework against the Fowler / ThoughtWorks framing plus the Medium summary of OpenAI / Anthropic / ThoughtWorks harness patterns, then pressure-testing the proposed backlog with Claude Opus 4.6 and Gemini 3.1.
**Current state:** The framework is already strong on routing, resumability, durable project state, evaluator-loop concepts, observer-driven maintenance, and harness self-governance. The review found the biggest gaps in executable quality controls: computational checks, runtime / behavior validation, architecture-fitness verification, continuous drift sensing, and explicit code-documentation expectations.
**Audit decisions already made:**
- Keep `ADS-project-knowledge/` as the single shared writable project workspace for team use; do **not** split it into a separate memory root unless a later operational need justifies it.
- Treat `ADS-project-knowledge/memory/` as the memory layer inside that workspace; terminology cleanup for the root remains optional / last.
- Merge the earlier "architecture fitness" and "rebalance validator strategy" ideas into one workstream so product-facing validation becomes concrete instead of abstract.
- Keep the model-upgrade / harness-validity audit idea, but only after the core executable contracts exist; do not prioritize it ahead of the core validation surfaces.
- Keep the machine-readable feature-state question as a bounded investigation only; do not let it become open-ended design work.
**Severity legend:**
- `Critical` — foundational harness gaps that should shape the next round of framework changes
- `High` — important follow-ons once the critical contract layer exists
- `Medium` — useful, but should wait until the core contract surfaces are stable
- `Optional` — clarity/polish work, not a structural blocker
**Implementation note for future sessions:** This section is intentionally detailed enough to serve as the source brief for a fresh session. Before implementing any item below, re-read the referenced docs, confirm whether newer harness work has partially addressed the gap, and then update this todo item rather than recreating the rationale from memory.

**What still looks missing or underpowered after reading both (Loiane Groner 2026-04-14 + Birgitta Bockeler / Martin Fowler 2026-04-02):**
- **A first-class sensor paradigm is still missing.** The framework has validators, Observer checks, capability probes, and evaluator loops, but not a canonical sensor catalog that names each sensor's class (`computational` / `inferential`), timing (`pre-commit` / `PR` / `continuous` / `runtime`), owner, artifact output, and action-on-fail. Today the sensors exist implicitly; the articles argue for making that control surface explicit.
- **Harnessability / ambient affordances are not yet a first-class assessment surface.** The framework has CodeBase Analyzer and System Blueprint stages, but it does not yet explicitly score or classify how governable a host repo is for agent work: typedness, module-boundary clarity, testability, topology simplicity, and other properties that determine which sensors are even possible.
- **Topology-level harness templates are still thin.** Current templates are mostly stack-specific runtime validation templates. The articles point toward reusable harness bundles for common application shapes or topologies (for example CRUD API, async worker, event-driven service, full-stack web app), not just per-language smoke-check templates.
- **Do not reopen already-captured gaps as if they were new.** Computational controls, runtime validation, architecture-fitness checks, continuous drift sensing, and machine-readable state questions are already covered in the numbered workstreams below. Reusable templates / CI gating and default retry / escalation behavior are also mostly present and should not be reclassified as greenfield design gaps unless a concrete failure shows the current implementation is insufficient.

#### 1-4. `Critical` — DONE
**Completed 2026-05-18/19.** All four critical items shipped:
- Computational controls contract → `framework/contracts/computational-controls.md`
- Runtime validation contract → `framework/contracts/runtime-validation.md`
- Architecture fitness contract → `framework/contracts/architecture-fitness.md`
- Enforcement + bootstrap → `framework/contracts/enforcement.md` + `framework/templates/bootstrap/contracts-bootstrap.md`
- Pipeline integration → contract checkpoint added to `multi-agent-pipeline.md`
- Validator → `harness-engineering/validators/validate_contracts.py`
- Harness evals → `harness-engineering/harness-evals/contract-enforcement/` (8 seeds, 16/16 passed against Gemini 3.1 + Codex 5.5)
- Audited by Gemini + Codex with corrections applied

#### 5. `High` — Add continuous drift sensors, but keep phase 1 intentionally narrow
**Why:** The original drift-sensor idea was too broad. The harness needs recurring codebase-health sensing, but the first phase should focus on a small set of actionable signals rather than turning into a full platform-engineering observability roadmap.
**Phase 1 scope only:**
- dead-code detection
- dependency / security drift
- coverage-quality analysis
**Later candidates (not phase 1 unless explicitly promoted):**
- runtime SLO review
- log anomaly review
- broader observability quality signals
**Likely files to inspect/update first:**
- `agents/observer/skills.md`
- `harness-engineering/quality/README.md`
- `harness-engineering/quality/failure-promotion-policy.md`
- `harness-engineering/maintenance/observer-cadence.md`
- `framework/workflows/multi-agent-pipeline.md`
- `project-knowledge-template/reports/maintenance/README.md`
**Important implementation note:** This workstream should define who consumes the signals, where artifacts live, and how they route into maintenance / refactor / escalation. Do not add recurring sensors with no ownership path.
**Done when:**
- The harness has a small, named set of recurring drift sensors with clear outputs and owners.
- Observer / maintenance flows know how to ingest and act on those findings.

#### 6. `High` — Add explicit code-documentation standards and enforcement
**Why:** The framework is strong on external workflow documentation, but the actual code documentation expectations are still under-specified. This needs to become part of the maintainability harness, not a matter of taste.
**What this workstream must define:**
- What must be documented:
  - public interfaces
  - complex orchestration paths
  - non-obvious invariants
  - side effects
  - important constraints
- What should **not** be over-documented:
  - obvious leaf logic
  - noise comments
  - comments that only restate the code
- How enforcement works:
  - code review expectations
  - any doc-lint / doc-coverage checks available by stack
  - handoff expectations for changed public APIs
**Likely files to inspect/update first:**
- `agents/programmer/skills.md`
- `agents/code-review/skills.md`
- `agents/docs/skills.md`
- `framework/templates/handoff-template.md`
- any code-style or documentation-reference skills already used by Programmer / Code Review
**Important implementation note:** The standard should improve maintainability and agent reliability, not create comment bloat. Keep the "what not to document" guardrail explicit.
**Done when:**
- The framework has one clear "enough documentation" rule.
- Programmer, Code Review, and Docs stages all enforce the same expectation.

#### 7. `High` — Make the evaluator contract the concrete sprint/build contract
**Why:** The backlog should stop leaving this as an abstract "determine whether" question. The intent is to resolve whether `evaluator-contract-<slug>.md` is already the builder/judge agreement artifact and, if so, strengthen it enough that future sessions do not recreate the debate.
**What this workstream must do:**
- Time-box the decision instead of letting it linger.
- If `evaluator-contract-<slug>.md` is the right artifact, strengthen it so it explicitly carries:
  - scope
  - non-goals
  - evidence surfaces
  - completion criteria
  - fail conditions
  - required artifacts
- If it is **not** the right artifact, document why and define the replacement contract clearly.
**Likely files to inspect/update first:**
- `harness-engineering/quality/evaluation-loops.md`
- `framework/templates/evaluator-contract-template.md`
- `framework/templates/evaluator-report-template.md`
- `framework/workflows/conventions.md`
- any agent docs that already talk about evaluator-mode work
**Done when:**
- Evaluator-mode work has one unmistakable pre-build contract artifact.
- A fresh session can tell from the docs exactly how builder/judge scope is supposed to be agreed before implementation starts.

#### 8. `Medium` — Add a formal model-upgrade / harness-validity eval program
**Why:** Model improvements can make older harness rules stale, but harness simplification needs evidence instead of intuition. This remains important, but it should land only after the core executable contracts exist; otherwise the framework is auditing a weak baseline.
**What this workstream must define:**
- eval triggers:
  - new major model family adopted or actively evaluated
  - meaningful model version jump within a family
  - host/runtime change that affects tool access, orchestration, context, or cost
  - repeated logged evidence that a harness step feels redundant or is routinely skipped / overridden
- pinned model baselines:
  - every retained run records exact provider model IDs, model labels, host/runtime, and execution mode in the run manifest
  - aliases such as `opus` are not enough for retained model-upgrade evidence
- benchmark packs for revalidation:
  - select representative seeds from the existing Architect, Programmer, and Code Review eval suites
  - include positive controls, negative controls, false-positive restraint, planning, implementation, review, runtime, and adversarial behavior where available
- ablation modes:
  - single-component ablation for planner/spec expansion, sprint decomposition, evaluator loops, context reset / compaction behavior, file-backed handoffs, per-slice QA, and helper-agent decomposition
  - whole-layer or multi-component ablation as the evidence-based way to detect discontinuous model capability jumps
- retained report fields:
  - benchmark tasks and seed count
  - baseline model / harness variant
  - upgrade model / harness variant
  - quality delta first
  - latency delta
  - cost delta
  - error-recovery / resumability delta when relevant
  - `essential` / `conditional` / `stale` decision
  - follow-through docs or deprecation PR required
**Likely files to inspect/update first:**
- `harness-engineering/quality/load-bearing-harness-audit.md`
- `framework/templates/load-bearing-harness-audit-template.md`
- `harness-engineering/quality/evaluation-loops.md`
- `harness-engineering/agent-evals/README.md`
- `harness-engineering/agent-evals/architect-evals/benchmark-suite/controls.md`
- `harness-engineering/agent-evals/code-review-evals/benchmark-suite/controls.md`
- `harness-engineering/agent-evals/programmer-evals/benchmark-suite/controls.md`
- `harness-engineering/quality/scripts/score_eval_suite.py`
- `harness-engineering/validators/validate_eval_suite.py`
- `harness-engineering/quality/README.md`
- `project-knowledge-template/reports/maintenance/README.md`
**Important implementation note:** Define the program now, but do not build a concrete ablation runner until items 1-4 are stable enough to provide trustworthy baselines. If a whole-layer ablation shows broad stale signals, escalate to architecture review before removing default harness structure.
**Done when:**
- Model and host upgrades can classify harness components as `essential`, `conditional`, or `stale` from retained eval evidence.
- Stale harness rules are retired only with a retained load-bearing audit report and follow-through changes to source-of-truth docs.

#### 9. `Medium` — Run a bounded investigation on whether a machine-readable feature-state tracker is needed
**Why:** This should remain a bounded spike, not open-ended design work. The question is whether long autonomous runs actually need a single machine-friendly progress surface beyond `tasks.md`, `pipeline-state.md`, `progress-ledger.md`, and report artifacts.
**What this investigation must answer:**
- What concrete failure mode the current state surfaces do **not** solve well.
- Whether a single tracker materially improves autonomous progression or resumability.
- Whether the existing trio is already sufficient if used consistently.
**Likely files to inspect/update first:**
- `framework/workflows/pipeline-state-format.md`
- `harness-engineering/runtime/session-continuity.md`
- `framework/workflows/multi-agent-pipeline.md`
- `framework/templates/tasks-template.md`
- any existing feature / state artifacts in `project-knowledge-template/reports/pipeline/`
**Decision rule:** Either propose a specific artifact with a real owner and purpose, or explicitly close the item by saying the current state surfaces are sufficient.
**Done when:**
- The framework either adopts a machine-readable feature/progress surface or records a deliberate reason not to.

#### 10. `Optional` — Clarify `ADS-project-knowledge/` terminology without splitting it
**Why:** This is clarity work, not a structural blocker. For team usage, the current single workspace root remains the preferred shape.
**What this workstream must do:**
- Clarify consistently that:
  - `ADS-project-knowledge/` is the writable project harness workspace
  - `ADS-project-knowledge/memory/` is the memory layer inside it
- Avoid language that implies the whole root is "memory"
- Do **not** split the root into separate workspace and memory roots unless a later operational need clearly justifies it
**Likely files to inspect/update first:**
- `AGENTS.md`
- `project-knowledge-template/README.md`
- `framework/workflows/conventions.md`
- `framework/memory/README.md`
- `project-knowledge-template/memory/README.md`
**Done when:**
- The docs stop implying that the entire root is memory.
- The existing team-friendly single-workspace shape remains intact.

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
