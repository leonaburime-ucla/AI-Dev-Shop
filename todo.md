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
- React Component Testing Policy: **DONE** (enforced via TDD routing)
- Execution Topology Default: **REMOVED** (toolkit already implements justified exception pattern)
- Multi-LLM Consensus Modes and Guardrails: **OPEN / PARTIAL** (consensus + preflight exists; strict model/version normalization still open)
- Agent Eval Depth: **OPEN / PARTIAL** (framework + taxonomy done; need to regenerate Architect/CR seeds at staff+ complexity)
- Protocol Split: MCP + A2A: **OPEN** (MCP practical now; A2A defer)
- Spec-Kit Command Contract Parity: **OPEN / PARTIAL** (command templates exist; frontmatter contracts still missing)
- System Design Skill Coverage: **DONE** (all 14 depth topics in `operational-depth-patterns.md`)
- Temporal Durable Workflow Skill: **OPEN** (dedicated durable workflow guidance still needed)
- Garry Tan gstack Intake: **OPEN / PARTIAL** (design/iOS/release domain skills extracted; skill testing and remaining stripping/adaptation still pending)

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

### Garry Tan `gstack` Intake and Decomposition **[OPEN / PARTIAL]**
**Source repo:** `https://github.com/garrytan/gstack`
**Local clone:** `/Users/la/Desktop/Multi-Agent Swarm Foundation/other-repos-to-learn-from/gstack`
**Current checkout inspected:** `cab774cc` on `main`
**Review intent:** Learn from and selectively adapt. Do not vendor gstack wholesale, install its runtime assumptions, or copy generated skill preambles into AI Dev Shop.
**What it is:** Garry Tan's open-source AI engineering workflow stack: a large skill pack plus browser daemon, QA/review/ship workflows, setup scripts for multiple agent hosts, memory/gbrain sync, and test/eval infrastructure.
**Why it matters:** It overlaps with AI Dev Shop's goal of turning an LLM coding session into a structured software team, but it takes a different product shape: skill-first, Claude Code oriented, strong browser tooling, generated `SKILL.md` files, and many practical workflow commands.
**Completed first extraction:**
- `skills/gstack-design/` plus `/gstack-design` slash command.
- `skills/gstack-ios/` plus `/gstack-ios` slash command.
- `skills/gstack-release/` plus `/gstack-release` slash command.
- `framework/routing/skills-registry.md` entries for all three, marked manual/slash-invoked and not wired into the default pipeline.
- Peer-reviewed through `/cowork` with Claude Opus 4.6 and Gemini 3.1 Pro Preview. Both approved with no blockers or should-fix items; post-implementation audit also approved.

**Do not redo as standalone gstack-domain skills unless new evidence changes the decision:**
- `gstack-design`
- `gstack-ios`
- `gstack-release`

**Follow-up: test the new skills before promotion:**
- Run `/gstack-design consultation`, `/gstack-design shotgun`, `/gstack-design html`, and `/gstack-design review` on small sample tasks. Confirm each mode reads only one reference and produces useful output.
- Run `/gstack-ios qa`, `/gstack-ios fix`, `/gstack-ios design-review`, `/gstack-ios clean`, and `/gstack-ios sync` against either a real iOS project or a fixture. Confirm unavailable device/simulator paths fail gracefully.
- Run `/gstack-release ship`, `/gstack-release setup-deploy`, `/gstack-release landing-report`, `/gstack-release canary`, and `/gstack-release land-and-deploy` on a safe fixture or dry-run repo. Confirm push/merge/deploy actions stop for explicit approval.
- Add lightweight validation checks for these skills: frontmatter, reference existence, one-reference routing language, no banned runtime assumptions outside `upstream-notes.md`, and destructive-action approval language.
- Decide after testing whether any of these graduate from `0.1.0` manual/slash-invoked skills to default pipeline integration.

**Remaining gstack stripping/adaptation targets:**
- Skill taxonomy and workflow shape: compare `/office-hours`, `/autoplan`, `/plan-*`, `/review`, `/qa`, `/ship`, `/cso`, `/learn`, and `/context-*` against AI Dev Shop's Coordinator pipeline and agents.
- Browser daemon architecture: study `ARCHITECTURE.md`, `browse/src/`, `BROWSER.md`, and browser tests for persistent Chromium, refs, logs, screenshots, cookies, auth, and tunnel security.
- Skill generation system: study `SKILL.md.tmpl`, per-skill templates, `scripts/gen-skill-docs.ts`, and resolver modules under `scripts/resolvers/` for token reduction, generated docs, and host overlays.
- Host integration: study `setup`, `hosts/`, `docs/ADDING_A_HOST.md`, and Codex/OpenCode/Cursor/Kiro adapters for cross-host install and command naming patterns.
- Safety and scoping: inspect `/careful`, `/freeze`, `/guard`, prompt-injection defenses, path validation, token registry, dual-listener tunnel design, and security tests.
- Memory and continuity: inspect `/learn`, `/context-save`, `/context-restore`, gbrain docs/scripts, timeline/review/question logs, and project slug/state path conventions.
- QA/review/release loop: release has a first extraction; continue inspecting `/review`, `/qa`, `/qa-only`, `/benchmark`, and tests for ideas that could strengthen AI Dev Shop's post-code stages without duplicating the new `gstack-release` skill.
- Evaluation and regression infrastructure: inspect `package.json` scripts, `test/`, `browse/test/`, skill evals, free/eval test splits, parity/size checks, and slop scanning.

**Stripping rule for future adaptations:**
- Keep portable workflow ideas, mode maps, safety gates, validation checks, and useful operator UX.
- Strip generated preambles, telemetry/config hooks, `~/.gstack` state assumptions, gbrain wiring, hardcoded local binaries, Claude-only AskUserQuestion plumbing, and daemon/runtime dependencies unless deliberately reimplemented as AI Dev Shop-native tooling.

**Questions to answer during review:**
- Which gstack ideas are superior to our current framework and should be adapted?
- Which ideas are redundant because AI Dev Shop already has a stronger pipeline equivalent?
- Which ideas are too Claude-Code-specific or too operationally heavy for this repo?
- Where does gstack use generated artifacts or executable tests to enforce things we currently enforce only by prose?
- What would a small, low-risk adaptation look like before any larger port?
**Suggested review order:**
1. Read or refresh `README.md`, `ARCHITECTURE.md`, `AGENTS.md`, `CLAUDE.md`, `SKILL.md.tmpl`, and `package.json`.
2. Build a command/skill inventory from all root skill folders and summarize their purpose, inputs, outputs, and state writes.
3. Trace the browser daemon call path from CLI to server to Chromium using `browse/src/cli.ts`, `browse/src/server.ts`, `browse/src/browser-manager.ts`, and `browse/src/snapshot.ts`.
4. Trace generated-skill plumbing through `scripts/gen-skill-docs.ts` and `scripts/resolvers/`.
5. Compare remaining gstack workflows against AI Dev Shop pipeline stages and mark each idea as `adopt`, `adapt`, `already-covered`, or `skip`.
6. Produce a retained report in the project knowledge area with concrete recommendations, file references, risks, completed adaptations, and next implementation candidates.
**Done when:**
- A decomposition report exists with architecture map, skill inventory, safety model notes, and testing/eval summary.
- The report includes a direct comparison table against AI Dev Shop stages.
- The three new domain skills are tested on sample tasks and either promoted, revised, or explicitly kept experimental.
- At least 5 remaining concrete ideas are classified as `adopt/adapt/already-covered/skip`, with rationale.
- Any future adaptation has a small first task and a clear no-vendor/no-drift policy.

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

### Graphify `--agent-cache` RFC **[OPEN]**
**What it is:** Add `--agent-cache` flag to graphify that produces a greppable JSONL of chunk-level summaries with namespace inheritance and line pointers — precomputed cache so agents skip the grep/read/assess/repeat loop. Debate consensus (3/3): no vector DB, no BM25 for MVP, no community rollups — just chunked summaries + grep. See `ADS-project-knowledge/.local-artifacts/swarm-consensus/runs/20260609T-agent-cache-debate-report.md` for full spec. PR branch exists on fork: `leonaburime-ucla/graphify` (`docs/node-summaries-rfc`); upstream PR #1166 covers file-level summaries; this extends to chunk-level.

### Temporal Durable Workflow Skill **[OPEN]**
**What it is:** Add a dedicated skill for Temporal-style durable workflow systems and related durable orchestration patterns.
**Why it matters:** Existing skills cover queues, async jobs, outbox, saga, retries, idempotency, and orchestration, but they do not provide focused guidance for when a workflow engine is the right abstraction, how to model durable workflow state, how to version workflows, or how to test/resume long-running executions.
**What to add:**
- Create a durable workflow skill covering Temporal-style workflows, cloud state machines, durable functions, activity idempotency, workflow IDs, timers, signals, cancellation, compensation, replay/versioning, observability, and worker failure recovery.
- Include decision guidance for queue vs job worker vs event bus vs durable workflow engine.
- Add test guidance for retries, timeout paths, crash/resume behavior, compensation, duplicate activity execution, and in-flight workflow version changes.
- Add routing guidance for which agents should load it: likely Software Architect, Programmer, TDD, QA/E2E, TestRunner, DevOps, and Code Review when durable workflow requirements are present.
**Done when:**
- A new skill exists under `skills/` with concise execution guidance and references.
- `framework/routing/skills-registry.md` maps the skill to the right agents conditionally.
- Relevant agent `skills.md` files mention the skill only as conditional context.
- A small fixture/eval or checklist validates that agents distinguish simple async jobs from durable workflows.

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

### Claude Audit Follow-Ups: `audit-work` + `specs_as_built` Patch Set **[OPEN]**
**Source:** Claude external audit on 2026-05-25, raw result at `ADS-project-knowledge/.local-artifacts/external-audit/offloads/20260525T040204Z-needed-audit/claude/claude-audit.result.md`.
**Audit outcome:** No blockers or high-risk fixes. Claude marked both findings as medium and non-blocking.
**What to add:**
- `harness-engineering/validators/validate_contracts.py`: reject angle-bracket template placeholders in live host declarations. `field_has_content()` should treat values like `<HOST_PROJECT_ROOT>` and `<ADS_PROJECT_KNOWLEDGE_ROOT>` as unfilled placeholders, matching the placeholder behavior in `validate_specs_as_built_freshness.py`.
- `harness-engineering/validators/validate_specs_as_built_freshness.py`: validate `status` against the allowed enum: `generated`, `hybrid`, `stale`, `rewriting`. Emit a clear warning such as `INVALID_STATUS_VALUE` when metadata uses an unknown status.
**Done when:**
- Targeted validator tests or fixtures prove placeholder host declarations are rejected.
- Targeted validator tests or fixtures prove invalid specs-as-built status values are reported clearly.
- `python3 harness-engineering/validators/validate_contracts.py`, `python3 harness-engineering/validators/validate_specs_as_built_freshness.py`, and `bash harness-engineering/validators/run-all.sh` pass.

### State-of-the-Art Harness Engineering Gaps From 2026 Video Review **[OPEN]**
**Source:** User-provided transcript of "Rethinking AI Agents: The Rise of Harness Engineering"; gap list consolidated from Coordinator, Claude, and Gemini review passes.
**What it is:** Advanced harness concepts that go beyond the current repo's strong NLH-style pipeline, contracts, state files, validators, evaluator loops, and load-bearing audit doctrine.
**Why it matters:** The repo already matches much of the video's baseline advice. These items target the next maturity layer: trace-driven optimization, measurable pruning, cross-model transfer, programmatic safety, and cost-aware orchestration.
**Current state:** **[PARTIAL]** Many foundations exist in `harness-engineering/`, `framework/workflows/`, `framework/contracts/`, and `skills/swarm-consensus/`, but most of these gaps are policy/manual today rather than automated, benchmark-backed harness behavior.
**Eval requirement:** Every item below needs an explicit evaluation path before it is treated as implemented. Add seeded evals, ablation tasks, adversarial fixtures, or validator regression cases that can show quality, safety, cost, latency, or transferability deltas before and after the harness change.
**What to add:**
- **Meta-Harness trace-driven optimizer:** Add a workflow where failed raw traces are mined by a proposer that suggests harness edits, produces a patch branch or retained proposal, runs benchmark/eval packs, and records accept/reject evidence. Keep human or Coordinator approval before landing harness changes.
- **Raw trace preservation for optimization:** Strengthen `harness-engineering/runtime/context-offloading.md` and trace docs so optimization runs preserve raw execution traces, tool outputs, stderr, prompts, and failure artifacts. Summaries are allowed for chat, but must not replace raw traces as optimizer input when raw evidence exists.
- **Acceptance-gated narrowing-first attempt loop:** Add a runtime policy that starts with the narrowest plausible context/tool surface, accepts only evidence-backed progress, and broadens scope/tools/delegation only after explicit failure signals. This should upgrade flat retry budgets into "stay narrow until the evidence justifies widening."
- **Cross-model harness transfer testing:** Extend `harness-engineering/quality/model-upgrade-program.md` so a harness improvement proven on one model is tested against other available models, including cheaper models, and reported as a transferable harness asset when it improves multiple model families.
- **NLH representation-quality ablations:** Add guidance and evals for testing whether rewriting the same harness logic in clearer natural-language harness form improves results. Treat representation shape, wording, layer boundaries, and file structure as measurable performance drivers.
- **Verifier and multi-candidate harm warnings:** Update load-bearing audit guidance to explicitly test whether added verifiers, broad evaluator gates, or multi-candidate search reduce quality, latency, or cost. Do not assume more verification is always better.
- **Programmatic safety DSL / action-veto layer:** Move high-risk markdown-only rules toward machine-enforced policy where feasible: agent permission manifests, command/path validators, destructive-command deny rules, write-scope leases, secret-read blocking, and tests that prove unsafe actions are vetoed before execution.
- **Shared harness artifact and skill vulnerability scanning:** Extend `skills-inbox` and registry validation with explicit checks for prompt-injection text, dangerous tool instructions, hidden network/write behavior, ambiguous authority claims, and vulnerable community-contributed skills before adoption.
- **Cost/token-aware harness selection:** Add run-level budget capture and selection guidance so the Coordinator can choose between simple, evaluator, multi-agent, or consensus paths based on expected value, quality risk, latency, token cost, and user budget.
- **NLH three-layer separation:** Formalize the current implicit split into swappable layers: backend/tools, runtime charter/policy, and task-specific agent logic. Use this to enable cleaner ablations: swap one layer while holding the others fixed.
- **Trace mining and observability dashboard:** Build on `framework/workflows/trace-schema.md` with an aggregator that reports failure rate by stage, retry clusters, token/cost trends, slow stages, stale dispatches, and recurring harness-rule violations.
- **Harness-model co-evolution watch item:** Track as a research frontier rather than immediate implementation: whether harness strategies should inform model fine-tuning or model selection, and whether model behavior changes should feed back into harness pruning.
**Evaluation work to add alongside the gaps:**
- Create a dedicated harness-gap eval suite under `harness-engineering/harness-evals/` or `harness-engineering/agent-evals/` for these state-of-the-art gaps.
- For each new harness rule, define at least one positive seed that should pass, one negative/adversarial seed that should be blocked or caught, and one regression seed from a prior real failure when available.
- For optimization and pruning work, require before/after ablation runs that record quality first, then token count, wall-clock latency, tool-call count, and failure recovery.
- For cross-model transfer work, run the same seed pack across at least two model families or tiers and report whether the harness change transfers, regresses, or is model-specific.
- For programmatic safety work, include executable validator tests that prove unsafe commands, out-of-scope writes, secret reads, and prompt-injection-shaped artifacts are rejected.
- For trace-driven work, keep raw trace fixtures as eval inputs so the evaluator can compare raw-trace optimization against summary-only optimization.
**Likely files to inspect/update first:**
- `harness-engineering/runtime/context-offloading.md`
- `harness-engineering/runtime/tripwires.md`
- `framework/workflows/job-lifecycle.md`
- `framework/workflows/trace-schema.md`
- `harness-engineering/quality/load-bearing-harness-audit.md`
- `harness-engineering/quality/model-upgrade-program.md`
- `harness-engineering/quality/evaluation-loops.md`
- `harness-engineering/harness-evals/`
- `harness-engineering/agent-evals/`
- `harness-engineering/quality/scripts/score_eval_suite.py`
- `harness-engineering/validators/validate_eval_suite.py`
- `harness-engineering/skills-inbox/skills-librarian-policy.md`
- `framework/governance/tool-permission-policy.md`
- `harness-engineering/validators/`
**Done when:**
- At least one retained meta-harness proposal is generated from raw failure traces and accepted or rejected with benchmark evidence.
- Raw trace retention is a hard rule for optimization runs.
- Retry behavior has an explicit narrowing-first gate before broadening context/tools/delegation.
- Harness changes can be compared across at least two model families or model tiers.
- Load-bearing audits explicitly evaluate verifier/search overhead as potentially harmful.
- High-risk agent actions have at least one machine-enforced veto path instead of markdown-only instruction.
- External skill ingestion includes vulnerability/prompt-injection scanning before adoption.
- Run summaries include cost/token/latency data sufficient to compare harness variants.
- Each added gap has at least one retained eval, ablation report, or validator regression test proving the harness change works and does not create an obvious regression.

### Specialized Harness Follow-Ons From Video **[OPEN]**
**Source video:** `https://www.youtube.com/watch?v=I2K81s0OQto`
**What it is:** Follow-up ideas from a harness-engineering video focused on specialized multi-stage business workflows, deterministic rails, subagents, observability, and checkpointed execution.
**Why it matters:** Most repo-level harness work is now in place, but these items push the framework further toward specialized downstream harnesses for compliance, legal, financial, and other long-running business processes.
**What to add:**
- ~~Stage-output schema enforcement:~~ **DONE** — `harness-engineering/quality/stage-output-schema.md` (machine-validated output contracts with required fields, validation modes, failure behavior, schema versioning, trace integration).
- ~~Model-tier routing policy:~~ **DONE** — `framework/routing/model-routing.md` (tier recommendations per agent role with cost/quality guidance).
- ~~Phase-checkpoint template for downstream harnesses:~~ **DONE** — `harness-engineering/quality/phase-checkpoint-template.md` (resumable checkpoint artifacts with staleness, invalidation, sensitive-state handling).
- Specialized non-code validation-loop templates: add downstream templates for things like clause-vs-playbook checks, fact-check loops, and rule-based business validation beyond software testing.
- Fixed-plan vs dynamic-plan design guidance: document when a workflow should stay on deterministic fixed rails versus when dynamic replanning is acceptable.
- Tool-approval patterns for risky actions: add stronger downstream guidance for actions that should always require explicit human approval before write/push/send/publish behavior.
- ~~Observability and trace design for specialized harnesses:~~ **DONE** — `framework/workflows/trace-schema.md` + `skills/observability-implementation/SKILL.md`.

### React Component Testing Policy **[DONE]**
**Completed.** Policy at `harness-engineering/quality/react-component-testing-policy.md` is enforced through TDD agent routing (`agents/tdd/skills.md` loads it directly).

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

### Programmer Ambient Fast-Feedback Testing **[DONE]**
**Completed.** Policy at `harness-engineering/quality/programmer-fast-feedback.md`. Defines watcher scope, signal-only payloads (40-line max, 120-char errors), debounce (10s), stable-failure alerts (2 consecutive), alert budget (3/15min), suppression state machine, stale-watcher resets, and clear TestRunner boundary.
**Remaining:** Wire into `agents/programmer/skills.md` as conditional awareness and update coordination docs.

---

## Consensus Orchestration

### Multi-LLM Consensus Modes and Guardrails **[PARTIAL]**
**What it is:** `/consensus` and `skills/swarm-consensus/SKILL.md` exist, but they need stronger orchestration rules for architecture/data-modeling debates and reproducible runs with explicit mode control.
**Current state:** Core orchestration flow is implemented; this section now tracks only remaining gaps.
**Known issue:** Consensus runs can still misreport exact peer model/version identifiers in some environments; preflight/version capture needs stricter normalization and verification.
**What to add:**
- Normalize and verify peer model/version reporting across CLI outputs so preflight and reports always show accurate model IDs and versions.
- i think we should have in /cowork /debate and /audit have heartbeats to make sure something is fine and maybe extend the
  times to let the other LLMs finish.

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

### System Design Skill Coverage Hardening **[DONE]**
**Completed.** All 14 depth topics added in `skills/system-design/references/operational-depth-patterns.md`: hot keys/rows, precomputation, batching, async depth (backpressure/DLQ/ordering/exactly-once), idempotency, deduplication, transaction tradeoffs (saga/outbox/compensation), concurrency failure modes (7 patterns), health checks (liveness/readiness/cascading), graceful degradation (circuit breaker/load shedding/bulkhead), authn/authz depth (token lifecycle/RBAC vs ABAC/zero-trust), secrets management (rotation/envelope encryption/injection), rate limiting depth (4 algorithms/distributed/per-tenant), abuse detection (anomaly signals/progressive enforcement/reputation). SKILL.md load strategy updated to reference the new file.

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

### Agent Eval Skill Coverage Mapper **[OPEN]**
**Source:** 2026-05-31 `/debate` on whether skill-specific evals are needed in addition to `agent-evals`.
**What it is:** Add an `agent-evals`-native mapper that shows which eval seeds test which skills, which skills should activate or stay silent, and whether agents actually used them during runs. Do not create a separate `skills-evals/` fixture hierarchy yet; keep canonical benchmark fixtures under the owning `harness-engineering/agent-evals/<agent>-evals/` suites.
**Why it matters:** A skill can help one target behavior while harming the agent through context overload, false positives, over-activation, verbosity, scope creep, or priority inversion. Agent evals should prove target lift without collateral damage.
**Current state:** **[PARTIAL]** `seed-catalog.tsv` already has `skill_source`; `validate_eval_suite.py` already recognizes optional `expected_conditional_skills` and `expected_non_activations`; `run-results.tsv` can carry `observed_conditional_skills`; `score_eval_suite.py` already computes activation recall and false-positive activation rate when those fields exist. This needs to be documented, generalized, and surfaced as a first-class map.
**Design status:** **[PROPOSED]** This is not settled doctrine. Debate the schema and protocol again before implementation, canary it on one skill and one agent suite first, and expect revisions based on what the canary proves. The mapper, ablation variants, metrics, and thresholds all have room for improvement before broad rollout.
**What to add:**
- Add `harness-engineering/agent-evals/skill-coverage-map.tsv` as a generated or validator-checked index over all benchmark suite `seed-catalog.tsv` files.
- Minimum map columns: `skill_slug`, `skill_path`, `agent`, `suite_path`, `eval_name`, `seed_id`, `expectation` (`required` / `forbidden` / `optional` / `neutral`), `test_role` (`target_behavior` / `negative_control` / `regression` / `harm_probe`), and `harm_probe` (`none` / `false_positive` / `overload` / `misrouting` / `verbosity` / `scope_creep` / `priority_inversion`).
- Standardize optional seed catalog columns across suites: `expected_conditional_skills` and `expected_non_activations`.
- Standardize optional run result columns: `observed_conditional_skills` and `skill_activation_notes`.
- Add `harness-engineering/agent-evals/skill-ablation-runs.tsv` for with-skill / without-skill comparison runs. Minimum columns: `run_id`, `skill_slug`, `variant` (`normal` / `skill_removed` / `skill_forced` / `skill_minimized`), `agent`, `suite_path`, `eval_name`, `seed_ids`, `model_id`, `target_delta`, `false_positive_delta`, `severity_accuracy_delta`, `activation_recall`, `activation_false_positive_rate`, `context_cost_delta`, and `decision`.
- Generalize the hardcoded conditional skill slug list in `validate_eval_suite.py` and `score_eval_suite.py` so skill slugs come from `framework/routing/skills-registry.md` or a derived agent-evals skill registry.
- Update scoring reports to show per-skill target lift, activation recall, activation false-positive rate, false-positive delta on negative controls, severity accuracy delta, cross-dimension regression, and context-cost delta when available.
**Targeted ablation protocol:**
- Use one-factor-at-a-time skill ablations by default to avoid combinatorial explosion. Do not test every skill x agent x seed x skill-combination unless prior evidence shows a conflict or overlap.
- For each candidate skill, pick one owning agent and three small seed groups: target seeds where the skill should help, forbidden/negative-control seeds where the skill should stay silent, and unrelated control seeds that detect context-window harm.
- Run matched variants: `normal`, `skill_removed`, and, when useful, `skill_minimized`. Use `skill_forced` only to test activation logic, not as the default proof of usefulness.
- Record context harm explicitly: prompt/context size, output length, latency, excessive checklist behavior, unrelated seed misses, false positives, and priority inversion.
- Escalate to pairwise skill-combination tests only when single-skill ablations suggest two skills overlap, conflict, or compensate for one another.
**Pass/fail model:**
- A skill passes when it improves or preserves mapped target-seed performance without increasing false positives, severity mistakes, unrelated seed misses, or context cost beyond the accepted threshold.
- A skill is redundant when `skill_removed` produces no meaningful target regression and no material collateral change.
- A skill fails or needs revision when target lift is outweighed by collateral damage: higher false positives, forbidden activation, degraded unrelated dimensions, excessive output bloat, latency/token cost, context-window pressure, or repeated priority inversion.
- Treat the core metric as `target lift - collateral damage`, not raw with-skill score alone.
**Likely files to inspect/update first:**
- `harness-engineering/agent-evals/README.md`
- `harness-engineering/agent-evals/*/benchmark-suite/seed-catalog.tsv`
- `harness-engineering/agent-evals/*/benchmark-suite/run-results.tsv`
- `harness-engineering/quality/scripts/score_eval_suite.py`
- `harness-engineering/validators/validate_eval_suite.py`
- `framework/routing/skills-registry.md`
**Done when:**
- A retained design debate or review records the chosen schema, rejected alternatives, and canary scope before implementation starts.
- A canary run on one skill and one agent suite proves the mapper and ablation workflow are practical before broader suite rollout.
- `skill-coverage-map.tsv` can answer which seeds test each skill across agent suites.
- Validator rejects unknown skill slugs and contradictory `required` vs `forbidden` expectations.
- Scorer reports activation recall and false-positive activation rate per skill across real run results.
- At least one high-risk shared skill and one conditional skill have retained normal vs removed/minimized ablation evidence.
- The docs state that standalone `skills-evals/` fixtures are deferred unless imported/community skills, cross-agent conflicts, or noisy ablations prove they are needed.

### Advanced Frontend Architecture Eval **[OPEN]**
**What it is:** An agent eval suite for the `advanced-frontend-architecture` skill — verifying that agents correctly apply the scoring framework, select appropriate depth levels, produce well-reasoned traces, and don't hallucinate architecture tradeoffs.
**Why it matters:** The skill uses a 14-dimension scoring matrix with leveled depth selectors (Senior→Staff→Principal→Distinguished). Without evals, there's no way to measure whether agents produce actionable reasoning traces vs generic tech-blog summaries, or whether depth escalation triggers fire correctly.
**What to build:**
- Seed catalog targeting staff+ complexity across different architecture decision scenarios
- Seeds should cover known failure modes:
  - Scoring all dimensions equally instead of weighting by context
  - Recommending micro-frontends for small teams (anti-pattern blindness)
  - Staying at Senior depth when multi-team/migration context demands Staff+
  - Hallucinating performance characteristics of architectures
  - Recommending SSR/hybrid for pure internal dashboards (mismatched rendering strategy)
  - Missing migration path reasoning for non-greenfield decisions
  - Producing score tables without evidence-backed argument chains
  - Failing to identify reversal triggers or follow-up decisions
  - Confusing internal component patterns (MVC/MVVM) with deployment architectures
  - Applying Distinguished-depth reasoning when Senior suffices (over-engineering noise)
  - Scoring BFF/GraphQL as a competing macro architecture instead of a complementary data layer
  - Failing to compose stacks (scoring SSR and Modular Mono separately instead of as one candidate like "SSR + Modular Mono + BFF")
  - Not marking N/A for internal-pattern dimensions (Delivery/Cost/Resilience when evaluating MVC vs FSD)
  - Over-escalating to Distinguished for routine org-wide decisions that are Principal-level (no actual platform bet)
- Grading rubric should check: correct candidate selection, appropriate depth escalation, dimension weighting rationale, evidence-backed scoring, complete reasoning trace structure, actionable recommendation with reversal triggers
- Minimum 24 seeds across rendering decisions, team-scaling decisions, migration decisions, and pattern-selection decisions
**Likely location:**
- `harness-engineering/agent-evals/frontend-architecture-evals/benchmark-suite/`
**Done when:**
- Seeds exist at staff+ complexity covering the major failure modes
- Scorer can evaluate reasoning traces against SKILL.md methodology and trace format
- Running the suite reveals which dimensions/depth-levels agents handle poorly
- At least 2 negative controls (reasonable architecture choices that should NOT be flagged as wrong)

### Memory-Regression Skill Evals **[OPEN]**
**What it is:** An agent eval suite for the memory-regression skill — verifying that agents correctly apply bounded-growth testing, select the right adapter, avoid known antipatterns, and produce working test scaffolds.
**Why it matters:** The skill has 8 platform adapters with platform-specific gotchas, a universal measurement pattern, and gating promotion criteria. Without evals, there's no way to measure whether agents actually follow the methodology or fall into documented antipatterns.
**What to build:**
- Seed catalog targeting staff+ complexity across platforms (not just browser/Node)
- Seeds should cover the known failure modes:
  - Unsigned subtraction without safe cast (Go uint64, Rust usize)
  - Measuring before GC / not forcing cleanup
  - Using wrong GC API (Thread.activeCount vs ThreadMXBean, RSS vs heapUsed)
  - Asserting on absolute values instead of growth delta
  - Not draining HTTP response bodies (Go, Node)
  - Testing with production heap size (hides leaks)
  - Copy-pasting adapter snippets without adaptation (wrong framework, missing setup)
  - Confusing diagnostic-only vs gate-ready tests
  - Setting arbitrary budgets without empirical calibration
  - Missing non-heap resources (FDs, GPU, direct buffers) when present in workload
  - Incorrectly promoting a high-variance test to blocking gate
- Grading rubric should check: correct adapter selection for platform, proper bounded-growth pattern (warmup→baseline→stress→cleanup→measure→assert), no antipattern violations, actionable failure output, correct GC/cleanup strategy for platform
- Minimum 24 seeds across browser, Node, Go, Python, JVM, mobile, and GPU/native
**Likely location:**
- `harness-engineering/agent-evals/memory-regression-evals/benchmark-suite/`
**Done when:**
- Seeds exist at staff+ complexity covering major failure modes per platform
- Scorer can evaluate test scaffolds against SKILL.md methodology and adapter correctness
- Running the suite reveals which platforms/patterns agents struggle with most
- At least 2 negative controls (correct but suspicious patterns that should NOT be flagged)

### AGENTS.md Hot/Cold Split **[OPEN]**
**What it is:** Split `AGENTS.md` (223 lines, loaded every turn) into a hot file (~100 lines, always-active rules) and a cold bootstrap file (read once on first turn). Third file: move the 24-line Reference Docs path catalog to `framework/operations/reference-index.md` — it's not startup-only (needed mid-session for lookups) but not always-active (not needed every turn), so it's an on-demand lookup index, not hot or cold.
**Why it matters:** ~7k tokens wasted per turn on startup/install/reference content that's irrelevant after turn 1. Shorter instruction surface may improve instruction compliance.
**What to do:**
- Verify actual model versions of peer CLIs before any audit work
- Build parity evals first (must-have: first-turn startup, peer dispatch skip, mid-session routing, resume after compression, hot-file-only sufficiency)
- Run evals against current single-file as baseline
- Implement the split
- Run evals against split files, compare
- Only ship if all must-have scenarios pass and token savings are confirmed
**Risks:** cold file not read on first turn, context compression losing startup state, mode-switch regression. Mitigated by idempotent bootstrap contract.
**Done when:**
- Eval suite exists and passes against baseline
- Split implemented and eval suite still passes
- Token savings measured quantitatively

### Fixing Programmer Evals **[OPEN]**
**Source:** Opus 4.6 eval run on 2026-05-29. Scored 95.9% (71/74 CAUGHT, 3 MISSED, 0 PARTIAL). Run exposed structural weaknesses in the eval design rather than meaningful agent skill gaps.
**What it is:** The programmer eval suite has design issues that inflate scores and fail to test actual programmer skills (code production, test iteration, design decisions under ambiguity).
**Why it matters:** A 95.9% score looks strong, but the eval is testing code review ability, not programmer ability. It also lacks negative controls, so false-positive rates are unmeasured.
**What to fix:**

1. **Reduce repetitive template seeds.** ~30 of the 74 seeds follow the same pattern across all 9 evals: "SRP violation," "non-injectable clock/dependency," "tests don't cover X," "scores overstated." Once the model recognizes the checklist template, it can mechanically hit all of them. Replace repetitive slots with domain-specific seeds unique to each fixture.

2. **Add negative controls.** The CR evals have 14 NC seeds testing false-positive restraint; the programmer evals have zero. The agent can flag everything aggressively with no penalty. Add 1-2 NCs per eval (correct-but-unusual patterns that should NOT be flagged as issues).

3. **Make it actually test programmer skills.** The current rubric is "did you identify the issue" — identical to the CR eval's scoring. A real programmer eval should require: producing working code, running tests, iterating when tests fail, making design tradeoff decisions. Add execution-based scoring: does the fix compile, do tests pass, is the fix correct?

4. **Reduce spec-guided bug hunting.** The brief often tells you exactly where to look (e.g., "deduplicate same userId + templateId" directly points to the dedup key). Harder evals would have vaguer requirements requiring the agent to infer what's wrong from operational behavior or domain knowledge, not from AC wording.

5. **Add large-noise fixtures.** All evals are 100-300 lines with 7-9 planted bugs (~1 bug per 20-40 lines). Real code has one subtle bug per thousands of lines. Add 2-3 evals with 800-1500 lines, distractor modules, harmless suspicious code, and only 3-5 real seeded issues to test signal-to-noise discrimination.

6. **Resolve mixed seed ownership.** SEED-1D and SEED-1I are explicitly marked "Expected owner: Code Review" not "Programmer." Either remove them from the Programmer eval scoring or reclassify them as cross-cutting seeds with adjusted expectations.

7. **Add difficulty tiering.** The CR evals have Easy/Medium/Hard with domain complexity (textbook → principal). The programmer evals are all roughly "medium" with no tiering. Add difficulty levels and ensure at least 30% of seeds are Hard (requiring deep domain reasoning, not just pattern recognition).

8. **Differentiate evals 6-9 from 1-5.** Evals 6-9 use `SEED-CL-XX` (checklist) format and test function-quality checklist items rather than domain correctness. The trick seeds are the only ones with real programmer-level challenge. Either unify the format and difficulty profile, or explicitly split into "domain correctness" and "code quality checklist" sub-suites with separate scoring.

**Done when:**
- At least 10 negative control seeds exist across the suite
- At least 3 evals include execution-based scoring (fix must pass tests)
- Repetitive template seeds (SRP, non-injectable clock, tests-missing, scores-overstated) reduced to max 2 instances each across the full suite
- At least 2 large-noise fixtures (800+ lines) exist
- Difficulty tiering is applied to all seeds with min 30% Hard
- A strong agent that scores 95%+ on the current suite scores measurably lower on the redesigned version

### Code Review Hard-Mode Benchmark Extension **[OPEN]**
**Source:** User-provided external AI run summary after the upgraded Code Review suite produced a `100%` detection rate with `0` false positives. The external reviewer judged the suite internally consistent and production-realistic, but noted that top Code Review agents may now recognize repeated fixture patterns.
**What it is:** Add a harder extension layer for Code Review evals that tests signal-to-noise, vague requirements, and non-repetitive production traps rather than explicit-spec treasure hunting.
**Why it matters:** The current Code Review suite is strong as a staff+ explicit-spec review benchmark, but a 100% run means it may not separate the best Code Review agents. The repeated "missing tests" and "observability dimensions missing" seeds can inflate scores once a model learns the template.
**Current state:** Code Review benchmark metadata validates with `75` seeds and staff+ depth floors satisfied, but the suite still has `0 benchmark_full` runs and should be treated as pilot until scored repeatedly.
**What to add:**
- **Blind / weak-spec evals:** Add fixtures with vague business goals, operational constraints, and partial handoffs so the reviewer must infer invariants instead of matching explicit AC wording.
- **Large-noise fixtures:** Add 2-3 Code Review evals with roughly 800-1500 lines, distractor modules, harmless suspicious code, and only 5-7 real seeded issues.
- **Reduce repeated patterns:** Do not include one observability seed and one missing-test seed in every eval. Replace several with config rollout, compatibility, data-modeling, operational cost, incident recovery, and rollback traps.
- **Stricter scoring for soft seeds:** For missing-test and observability seeds, require the exact missing causal case and exact fields for `CAUGHT`; otherwise score as `PARTIAL`.
- **Embedded negative controls:** Place correct-but-suspicious patterns near real defects so agents must discriminate locally, not just avoid false positives globally.
- **Less direct project briefs:** Keep specs realistic, but avoid AC phrasing that names the exact invariant to inspect, such as "idempotent before side effects." Prefer operational/business requirements that imply the invariant.
**Done when:**
- A hard-mode Code Review extension exists with weak-spec and large-noise fixtures.
- The extension has less repetitive seed shape than the current benchmark.
- At least one strong agent that scores near-perfect on the current suite misses or partially catches meaningful hard-mode seeds.
- Scoring reports separate explicit-spec benchmark performance from hard-mode adversarial review performance.

---

## Reverse-Spec Eval Suite **[OPEN]**

### What it is
An agent eval suite for the reverse-spec skill — verifying that the extraction pipeline produces correct, complete, and consistent specifications from existing codebases.

### Why it matters
The reverse-spec skill is now production-grade (v2.0.0) with a complex DAG of 5 bounded passes, confidence hierarchies, characterization tests, data migration profiling, and adversarial verification. Without evals, there's no way to measure whether agents executing this pipeline actually follow the methodology or produce correct output.

### What to build
- Seed catalog targeting staff+ complexity (real brownfield extraction challenges, not toy examples)
- Seeds should cover the known failure modes the skill was designed to prevent:
  - Confidence inflation (marking `inferred` as `confirmed`)
  - Hallucinating absence (`verified_none` without proof)
  - Missing failure matrices for state-changing endpoints
  - Zombie feature flags extracted as live requirements
  - Polymorphic column data mapped 1:1 without implicit schema extraction
  - Silent drops extracted as live webhook contracts
  - Soft-delete leakage (unfiltered reads)
  - Tenant scoping assumed from helper existence without query verification
  - Async job wire-format confusion (domain objects vs primitive IDs)
  - Convention-based requirements without batch-approval grouping
  - Characterization tests with unmasked nondeterministic fields
  - Data migration target mapping produced before Architect (premature Stage 2)
  - Normalization stripping rewrite-critical metadata fields
  - Missing `[CONTRACT VS IMPLEMENTATION]` marker when observed ≠ normative
- Grading rubric should check structural compliance (correct REQ format, risk tags, confidence labels, criticality assignment) and behavioral correctness (right confidence level for evidence type, right criticality for domain)
- Minimum 24 seeds across all 5 passes + synthesis

### Likely location
- `harness-engineering/agent-evals/reverse-spec-evals/benchmark-suite/`

### Done when
- Seeds exist at staff+ complexity covering the major failure modes
- Scorer can evaluate pass artifacts against the SKILL.md methodology
- Running the suite reveals which extraction phases agents struggle with most

---

## Governance Deep Dive **[OPEN]**

### ADR Governance Bloat Audit
**What it is:** Evaluate whether the governance ADR registry, comply-or-explain model, and $adr skill add genuine enforcement value or just ceremonial overhead.
**Why it matters:** Added 2026-06-03 based on a 3-model debate recommending ADRs + focused skills. But governance layers can easily become "process for process's sake" — rules that no one reads, exceptions that never trigger re-evaluation, or skills that load context without changing outcomes.
**What to evaluate:**
- After 3-5 governance ADRs are written: do agents actually invoke the $adr skill during implementation? Does the JIT lookup change their behavior, or do they just comply anyway from the existing pipeline ADR?
- Is the exception ledger tracking real deviations, or is it always empty (meaning rules are too broad or too obvious)?
- Does the 3-in-90-day re-evaluation trigger ever fire? If not, is the threshold wrong or are the ADRs just correct?
- Is there measurable context cost? Compare token usage on tasks with/without governance ADR loading.
- Could the same enforcement be achieved by linter rules alone without the document layer?
**Audit criteria:**
- If no governance ADR has been referenced by an agent in 30 days of active pipeline use → the registry is dead weight
- If no exceptions are recorded after 10+ features → rules are either too obvious or too broad
- If the $adr skill loads but agents never deviate or escalate → the skill is ceremony
**Integration tests to run after first real ADRs exist:**
- Does `architecture-fitness.md` conflict with or duplicate governance ADRs? Clarify division of responsibility if they compete.
- Does `escalation-policy.md` need a formal governance ADR trigger, or does the skill's inline "escalate to Coordinator" instruction suffice?
- Do agents correctly read ADR-INDEX.md, match scope globs, and load only ACCEPTED ADRs?
- Does the exception ledger actually get written to, and does the 3-in-90-day trigger fire when it should?
- Does the Architect promotion step fire on cross-cutting decisions and skip on feature-scoped ones?
**Done when:**
- A retained audit report exists with evidence-based keep/prune/revise decisions for the governance layer
- Any unused governance ADRs are either deprecated or the enforcement mechanism is strengthened

### Focused Loop Skills ($ui-loop, $test) **[OPEN]**
**What it is:** Specialized operating modes for the generic commit→push→feedback loop. $ui-loop iterates fast in browser and reconciles after. $test runs focused test suites based on coverage and file changes.
**Source:** 2026-06-03 debate consensus (3/3 agreement).
**What to add:** Design and implement both skills, wire into Programmer agent as conditional skills.

### Enforcement Harness (git hooks + CI) **[PARTIAL]**
**What it is:** Git hooks and CI checks running identical enforcement rules. "If you can't measure it, you can't enforce it."
**Source:** 2026-06-03 debate consensus (3/3 agreement).
**Current state:** Profiled runner (`run-all.sh --profile precommit|ci|governance`) implemented. Opt-in hooks installer exists. Pre-commit profile runs fast validators.
**What's still needed:**
- Refactor validators to accept `ADS_WORKSPACE_ROOT` env var so governance scenarios can call real validators against fixture workspaces (not just pattern assertions)
- Once validators are workspace-aware, upgrade governance scenarios from tautological assertions to subprocess invocations of real validator logic
- Add architecture linting (module import boundaries), governance ADR scope-glob syntax validation
- CI workflow file (GitHub Actions) that calls `run-all.sh --profile ci`

### Governance Workflow Scenarios (BDD-lite) **[PARTIAL]**
**What it is:** 5-10 executable tests covering pipeline governance invariants: approval gates hold after resume, routing doesn't dispatch past blocks, artifact handoffs are complete.
**Source:** 2026-06-03 debate consensus (2/3 + 1 agrees on need). Plain Pytest with readable scenario names — no Gherkin.
**Current state:** 19 governance scenarios in `harness-engineering/governance-scenarios/` covering spec gates, ADR governance, and artifact integrity. All pass in 0.12s. Tests currently assert governance patterns directly (not via real validators).
**What's still needed:**
- Upgrade to real validator invocation once validators support workspace targeting
- Add scenarios for: pipeline-state transition gates, security sign-off gate, Red-Team blocking, Implementation Outline readiness gate

### Spec Preamble Strengthening **[OPEN]**
**What it is:** Add a structured "Problem / Why / User Journey" section to the spec template to absorb PRD value without a parallel document type.
**Source:** 2026-06-03 debate consensus (3/3 reject standalone PRDs, agree on strengthening spec preamble).

---

## Notes

- None of these require Python or code — all are markdown documentation, agent instruction files, and schema definitions
- A2A: monitor but don't build to yet
- Items marked [PARTIAL] have a head start from the speckit integration already done in this repo
