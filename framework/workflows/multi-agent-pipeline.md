# Multi-Agent Pipeline

---

## Path Convention

All project-owned pipeline artifacts are written under `<ADS_PROJECT_KNOWLEDGE_ROOT>` — the sibling `ADS-project-knowledge/` folder next to the toolkit by default. `<AI_DEV_SHOP_ROOT>` remains the toolkit source tree.

- Provider-native planning artifacts → user-specified location or provider-native folders (Spec Agent asks before writing when needed; active provider and entrypoint paths recorded in pipeline state)
- Pipeline artifacts (ADR, research, tasks, red-team findings, test certification, pipeline state) → `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/pipeline/<NNN>-<feature-name>/`
- Reports (analysis, test runs, code review, security) → `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/` subfolders
- Local scratch, raw captures, exploratory prompts, and disposable session evidence → `<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/`
- Live project memory → `<ADS_PROJECT_KNOWLEDGE_ROOT>/memory/`
- Live constitution → `<ADS_PROJECT_KNOWLEDGE_ROOT>/governance/constitution.md`
- **Read-only toolkit source:** `agents/`, `skills/`, `framework/spec-providers/`, `framework/templates/`, `framework/workflows/`, `framework/slash-commands/`, and the toolkit-local `project-knowledge/` reference tree

Artifact-intent rule:
- pipeline-required artifacts save directly to `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/`
- optional retained reports ask before becoming canonical
- session-only scratch defaults to `<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/`

---

## Full Path (Existing Codebase)

```
[CodeBase Analyzer] → [System Blueprint] → Spec → [Red-Team] → Architect → [Database] → TDD → Programmer → [QA/E2E] → TestRunner → Code Review → [Refactor] → Security → [DevOps] → [Docs] → Done
```

- CodeBase Analyzer optionally produces a Migration Plan artifact — not a separate agent step
- `[...]` stages are optional but strongly recommended when dropping AI Dev Shop into a project with existing code

## Ideal Path (Greenfield)

```
[System Blueprint] → Spec → [Red-Team] → Architect → [Database] → TDD → Programmer → [QA/E2E] → TestRunner → Code Review → [Refactor] → Security → [DevOps] → [Docs] → Done
```

- Coordinator generates `tasks.md` from the approved ADR before TDD dispatch — not an agent step
- `[Observer]` is passive across all stages when enabled

Each stage is blocked until the Coordinator validates the previous stage's handoff contract. By default, routing flows through the Coordinator with bounded cross-agent consultation enabled; if consultation mode is disabled, the Coordinator uses strict single-agent routing with no consultations.

---

## Pre-Pipeline: Existing Codebase Analysis

Run this before the first Spec when working with an existing codebase.

### When to Run

- First time AI Dev Shop is dropped into an existing project
- Codebase has significant existing code that may conflict with new feature work
- Architecture of the existing code is unknown or suspected to be problematic

### CodeBase Analyzer Dispatch

For existing codebases, this is the default first step on the first pass unless a fresh analysis already covers the requested area.

Include in context:
- Path to codebase root (or specific modules to analyze)
- Desired output: analysis only, or analysis + migration plan
- Any known constraints (modules to skip, priority areas)

### Using the Output

The CodeBase Analyzer writes reports to `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/codebase-analysis/`. Two ways to use them:

**Route A — Migration first, then build:**
1. Review `MIGRATION-*.md` with human
2. Execute migration phases using Programmer Agent (each phase = a mini pipeline run)
3. Once codebase reaches target architecture, begin normal delivery pipeline for new features

**Route B — Build alongside migration:**
1. Pass `ANALYSIS-*.md` summary to Architect Agent as context for first ADR
2. Architect selects patterns that acknowledge current state and plan toward target
3. New features are built clean; migration phases run in parallel as separate pipeline runs

Route B is faster to first feature delivery. Route A is safer for large legacy codebases.

### Architect Agent Context When Analysis Exists

When a codebase analysis report exists, include in Architect dispatch:
- `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/codebase-analysis/ANALYSIS-<id>.md` executive summary
- `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/codebase-analysis/MIGRATION-<id>.md` (if generated)
- Flag: "Existing code has [Critical/High] findings — ADR must acknowledge migration path"

---

## Stage-by-Stage Context Injection

What the Coordinator must include in each agent dispatch. Include only what is listed. Extra context degrades attention quality.

### Context Shedding Rule (required)

After `system-blueprint.md` and the active spec package are approved, do not keep injecting raw `vibe` artifacts into downstream implementation stages.

- Allowed downstream context: approved `system-blueprint.md`, active spec package, ADR, tasks, and current-stage artifacts.
- Optional: a short 3-5 bullet intent summary derived from vibe output (if needed), not the full raw vibe transcript.
- Purpose: reduce context drift and avoid conflicting stale tech hints in implementation stages.

### System Blueprint Agent (conditional pre-spec stage)
- Product vision / idea statement (from user or VibeCoder output)
- Known constraints and NFRs
- Existing architecture context (if extending an existing system)
- `<AI_DEV_SHOP_ROOT>/skills/system-blueprint/SKILL.md`
- `<AI_DEV_SHOP_ROOT>/framework/templates/system-blueprint-template.md`

Output:
- `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/pipeline/<NNN>-<feature-name>/system-blueprint.md`
- Spec decomposition recommendation (which spec packages to create next and in what order)
- Mandatory `Core/Foundation` package at `P0` to block parallel domain slices until shared shell/primitives are merged
- `Critical User Journeys (Cross-Domain)` list for QA/E2E planning after slice convergence
- Dependency-aware sequencing (`Depends on`) so only dependency-disjoint slices run in parallel

### Spec Agent
- `framework/spec-providers/active-provider.md`
- `framework/spec-providers/<active-provider>/provider.md`
- Product intent from human (verbatim)
- `system-blueprint.md` (if produced) for domain boundaries and decomposition guidance
- `<ADS_PROJECT_KNOWLEDGE_ROOT>/governance/constitution.md` (for constitution compliance check and [NEEDS CLARIFICATION] detection)
- `<AI_DEV_SHOP_ROOT>/skills/api-design/SKILL.md` when the feature introduces or changes API style, pagination/filtering policy, error/lifecycle policy, webhook/event shape, or SDK-facing integration behavior
- Relevant entries from `<ADS_PROJECT_KNOWLEDGE_ROOT>/memory/project_memory.md` (domain conventions)
- Last 3 entries from `<ADS_PROJECT_KNOWLEDGE_ROOT>/memory/learnings.md` (recent failure patterns)
- Existing FEAT folders in `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/pipeline/` (to avoid ID collisions, detect overlap, assign next FEAT number)

The Spec Agent must record in `pipeline-state.md`:
- `spec_provider`
- `spec_entrypoint_path`
- `spec_readiness_artifact`

For the default Speckit provider, the existing `spec_path` convention remains valid as a compatibility field.

**Integration contracts:** If the spec depends on another feature's API, data schema, or event contract, the Spec Agent must include an `## Integration Contracts` section in the spec listing:
- Which features this spec depends on (by SPEC-ID)
- The exact interface boundary: endpoint signatures, data shapes, or event names
- Which ACs require the integration to be live

The Coordinator records these dependencies in `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/pipeline/<NNN>-<feature-name>/pipeline-state.md`. When all referenced features reach Done, the Coordinator may trigger an optional Integration Verification run against the combined system.

### Red-Team Agent (runs after Spec approval, before Architect dispatch)
- Active provider-defined planning surface (full content + hash) — must have zero unresolved clarification blockers
- `<ADS_PROJECT_KNOWLEDGE_ROOT>/governance/constitution.md` (for Constitution pre-flight)
- `<AI_DEV_SHOP_ROOT>/agents/red-team/skills.md`

**Routing after Red-Team output:**
- 3+ BLOCKING findings → route to Spec Agent with findings; do not dispatch Architect
- Any CONSTITUTION-FLAG findings → escalate to human before proceeding
- ADVISORY findings only → dispatch Architect, include advisory list in context
- No findings → dispatch Architect normally

### Planning Surface Gate (Coordinator check before Architect dispatch)

Coordinator cannot dispatch Architect until ALL of the following pass:

- Active provider is resolved from `pipeline-state.md`
- Provider-defined `spec_entrypoint_path` exists and matches the recorded hash anchor
- Provider-defined `spec_readiness_artifact` exists and passes its gate
- Zero unresolved clarification blockers remain in the provider-defined planning surface
- No banned vague language violations
- Traceability or equivalent planning coverage has no known gaps
- Implementation-readiness gate passed

For the default Speckit provider, apply the compatibility gate defined in `<AI_DEV_SHOP_ROOT>/framework/spec-providers/speckit/compatibility.md`.

Reference: `<AI_DEV_SHOP_ROOT>/project-knowledge/quality/spec-definition-of-done.md`

### Architect Agent
- `framework/spec-providers/active-provider.md`
- `framework/spec-providers/<active-provider>/provider.md`
- Active provider-defined spec entrypoint (full content + hash) — must be human-approved, zero unresolved clarification blockers
- For Speckit: apply the Architect read set from `<AI_DEV_SHOP_ROOT>/framework/spec-providers/speckit/compatibility.md` before ADR work begins
- Red-Team findings from `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/pipeline/<NNN>-<feature-name>/red-team-findings.md` (all ADVISORY and CONSTITUTION-FLAG findings; BLOCKING findings mean spec is not yet ready for Architect)
- `<ADS_PROJECT_KNOWLEDGE_ROOT>/governance/constitution.md` (for Step 0 constitution check)
- Current system boundaries (existing ADRs in `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/pipeline/`)
- Non-functional constraints from spec
- `<AI_DEV_SHOP_ROOT>/skills/architecture-decisions/SKILL.md`
- `<AI_DEV_SHOP_ROOT>/skills/api-design/SKILL.md` when the feature exposes or changes an API surface, webhook/event contract, lifecycle policy, or SDK-facing integration boundary
- Relevant `<AI_DEV_SHOP_ROOT>/skills/design-patterns/references/` files (Coordinator selects based on system drivers in spec)
- `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/codebase-analysis/ANALYSIS-<id>-<date>.md` executive summary (if produced — treat findings as informed estimates, not guarantees)
- `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/codebase-analysis/MIGRATION-<id>-<date>.md` (if produced — treat as draft recommendation; validate or refine in ADR)

**Architect outputs (in order):**
1. `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/pipeline/<NNN>-<feature-name>/research.md` (if spec has technology choices) — using `<AI_DEV_SHOP_ROOT>/framework/templates/research-template.md`
2. `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/pipeline/<NNN>-<feature-name>/adr.md` — using `<AI_DEV_SHOP_ROOT>/framework/templates/adr-template.md` (includes Constitution Check, Research Summary, Complexity Justification, and API interface decision with rejected alternatives when API design is in scope)

### Database Agent (optional — dispatched alongside or immediately after Architect when spec involves data modeling)

When the spec involves data modeling or database operations:
- Coordinator dispatches Database Agent alongside Architect, or immediately after ADR is approved
- Database Agent produces:
  - Schema design
  - Entity relationships
  - Migration plan
  - Index recommendations
- If platform = Supabase: Database Agent dispatches to Supabase Sub-Agent for platform-specific implementation
- Schema decisions must be reflected in the ADR before TDD is dispatched

### Coordinator: tasks.md Generation (after ADR human approval, before TDD dispatch)

Coordinator generates `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/pipeline/<NNN>-<feature-name>/tasks.md` using `<AI_DEV_SHOP_ROOT>/framework/templates/tasks-template.md`:
- Phases and story order derived from the ADR's parallel delivery plan and AC priorities (P1 first)
- `[P]` markers based on independent module boundaries **and** system-blueprint dependency constraints (`Depends on`)
- Do not mark tasks parallel when one task depends on another domain's API/event/schema contract or table ownership boundary
- Checkpoint annotation after Phase 1 and after each story phase
- TDD Agent is dispatched only after tasks.md is produced

### TDD Agent
- Active provider-defined planning surface (full content + hash) — **must be human-approved**
- `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/pipeline/<NNN>-<feature-name>/tasks.md` — generated by Coordinator after ADR approval; defines scope and parallelization for this TDD run
- ADR for the module being tested (`<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/pipeline/<NNN>-<feature-name>/adr.md`)
- `<AI_DEV_SHOP_ROOT>/skills/test-design/SKILL.md`
- Relevant entries from `<ADS_PROJECT_KNOWLEDGE_ROOT>/memory/project_memory.md` for the domain
- `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/codebase-analysis/TESTABILITY-<id>-<date>.md` (if produced — consume characterization test targets and seam candidates before writing tests for migrated modules)

### Pattern Priming (runs between TDD dispatch and first Programmer dispatch)

Before Programmer begins production implementation, run `<AI_DEV_SHOP_ROOT>/skills/pattern-priming/SKILL.md`.
The confirmed seed example becomes the reference for similar code in the session.
Repeat pattern priming when the task shifts to a materially different layer or concern.

### Programmer Agent
- Active provider-defined planning surface (hash must match TDD certification hash)
- Certified test names and which ACs they cover
- ADR for the module (architecture constraints)
- Relevant `<ADS_PROJECT_KNOWLEDGE_ROOT>/memory/project_memory.md` entries
- Handoff output from TDD Agent (summary only, not full session)
- Confirmed pattern-priming reference (from Pattern Priming step above)
- `progress-ledger.md` when resuming long-running work or when programmer retry count is 2+
- Self-validation harness template when runtime startup, API, UI, auth, migration, or integration behavior is in scope

If broad discovery is required before implementation, use a read-only discovery pass first and pass only structured findings into the Programmer context.

Programmer handoff must include an `Architecture Audit` section:
- `PASS` = no known architectural violations found
- `WARNING` = likely architectural violations remain; Coordinator surfaces them to the human and asks whether to route back to Programmer or continue downstream
- `BLOCKER` = ADR ambiguity or a hard architectural constraint prevents safe continuation; Coordinator pauses routing and escalates
- `Pre-Completion Checklist` = explicit proof that the claimed fix or completion was re-verified against the active task/spec
- `Loop Alert` = required when a loop-detection tripwire fired before handoff
- `Self-Validation` = required when runtime-changing work needed app-level validation before handoff; include status `PASS`, `PARTIAL`, or `BLOCKER`, report path, attempts used, paths checked, any bounded diagnosis pass used, and any offloaded evidence

### TestRunner Agent
- Test suite location
- Spec hash certified by TDD Agent (to validate drift)
- Previous cycle's failure clusters (to detect regressions)
- Self-validation report path when one was produced during implementation
- Coverage tool (from `tasks.md` constraints section; if absent, use project default)
- Active coverage profile for lines/branches/functions/statements by suite (from `tasks.md` constraints):
  - defaults: unit `98/98/98/98`, integration `90/90/90/90`, e2e `80/80/80/80`
  - if user provides custom minimums, those override defaults
- Per-file coverage baseline (from `tasks.md` constraints section if present, used to flag regressions on touched files)

Passing suites should be summarized briefly. Failing suites should include exact output or an offload path if the raw output is large.

### Code Review Agent
- Full diff of changed files
- Active provider-defined planning surface (for alignment check)
- ADR for the module (for architecture compliance check)
- `<AI_DEV_SHOP_ROOT>/skills/code-review/SKILL.md`
- `<AI_DEV_SHOP_ROOT>/skills/security-review/SKILL.md` (for surface flagging)
- `<AI_DEV_SHOP_ROOT>/skills/api-design/SKILL.md` when the diff changes API style, pagination/filtering policy, error model, lifecycle policy, webhook semantics, or SDK-facing ergonomics
- Previous Code Review findings (to detect recurrence)

### Refactor Agent
- Specific Code Review findings classified as Recommended
- Affected file contents
- ADR constraints (to verify refactors stay within architecture)
- `<AI_DEV_SHOP_ROOT>/skills/refactor-patterns/SKILL.md`

### Security Agent
- Full diff of changed files
- Active provider-defined planning surface (for business logic abuse vector analysis)
- List of changed auth/payment/data paths (Coordinator identifies these from the diff)
- `<AI_DEV_SHOP_ROOT>/skills/security-review/SKILL.md`

### QA/E2E Agent (runs after Programmer)
- Active provider-defined planning surface (full content + hash)
- `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/pipeline/<NNN>-<feature-name>/system-blueprint.md` (if produced; prioritize `Critical User Journeys (Cross-Domain)`)
- `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/pipeline/<NNN>-<feature-name>/adr.md`
- `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/pipeline/<NNN>-<feature-name>/test-certification.md`
- `<AI_DEV_SHOP_ROOT>/skills/e2e-test-architecture/SKILL.md`
- Coordinator directive specifying which ACs require E2E coverage

### DevOps Agent (runs after Security, before Docs)
- `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/pipeline/<NNN>-<feature-name>/adr.md`
- `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/security/SEC-<feature-id>-<YYYY-MM-DD>.md`
- Active provider-defined NFR section or equivalent planning constraint surface
- `<AI_DEV_SHOP_ROOT>/skills/devops-delivery/SKILL.md`
- `<AI_DEV_SHOP_ROOT>/skills/infrastructure-as-code/SKILL.md`
- Coordinator directive specifying scope (new infra / CI update / runbook only / full)

### Docs Agent (runs after DevOps, before Done)
- Active provider-defined planning surface, plus any explicit API contract artifact if present
- `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/pipeline/<NNN>-<feature-name>/adr.md`
- `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/security/SEC-<feature-id>-<YYYY-MM-DD>.md`
- Existing `CHANGELOG.md`
- `<AI_DEV_SHOP_ROOT>/skills/api-design/SKILL.md` when documenting API style decisions, lifecycle policy, webhook/event contracts, or integration ergonomics
- `<AI_DEV_SHOP_ROOT>/skills/api-contracts/SKILL.md`
- Coordinator directive specifying doc deliverables required

### Observer Agent (runs alongside, not in sequence)
- All agent outputs from the current cycle (summaries, not full sessions)
- Previous Observer reports (for trend analysis)
- `<ADS_PROJECT_KNOWLEDGE_ROOT>/memory/learnings.md` (to cross-reference new patterns against known ones)
- `<AI_DEV_SHOP_ROOT>/harness-engineering/observer-cadence.md` (for cadence triggers, doc-garden workflow, and benchmark refresh rules)
- `<AI_DEV_SHOP_ROOT>/harness-engineering/failure-promotion-policy.md` (for mandatory promotion when failure classes recur)

**Minimum Observer cadence:**
- after every 3rd completed feature
- immediately after any convergence escalation
- before merge for toolkit-maintenance changes touching `AGENTS.md`, `agents/`, `skills/`, `framework/spec-providers/`, `framework/workflows/`, `framework/templates/`, `framework/slash-commands/`, or `harness-engineering/`
- weekly while framework-maintenance work is active

**Toolkit-maintenance pass requirements:**
- run `bash harness-engineering/validators/run-all.sh`
- capture the doc-garden audit output in the Observer report
- review benchmark impact when instructions or routing docs changed
- recommend a concrete harness artifact when a failure class reaches the promotion threshold

---

## Routing Rules (Coordinator-owned)

| Finding | Route To | Context to Include |
|---|---|---|
| Multi-domain or unclear boundaries before spec exists | System Blueprint Agent | Product intent, constraints, current architecture context |
| Spec human-approved | Red-Team Agent | Full spec, spec hash, constitution.md |
| Red-Team: 3+ BLOCKING | Spec Agent | All BLOCKING findings with exact spec refs |
| Red-Team: CONSTITUTION-FLAG | Human → Spec Agent | Flag details, relevant constitution article |
| Red-Team: ADVISORY only | Architect | Spec, spec hash, advisory list |
| Test failures | Programmer | Failing test names, spec ACs, ADR constraints |
| `[ARCHITECTURE_REVISION_REQUEST]` from downstream agent | Coordinator escalation flow | Blocking technical constraint, failed alternatives, impacted artifacts (spec/ADR/tasks/tests), requested revision scope |
| Coverage gaps (any type) | TDD Agent (triage first) | Coverage Gap List (High-priority first), current % vs threshold per file, spec hash, test certification record — TDD classifies each gap as spec-traceable (writes tests) or no-spec-mapping (flags to Coordinator for Refactor dispatch) |
| Coverage gaps — no spec mapping (flagged by TDD triage) | Refactor Agent | `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/pipeline/<NNN>-<feature-name>/coverage-triage-<YYYY-MM-DD>.md`, Coverage Gap List, uncovered files with line ranges, ADR constraints |
| Touched-file coverage regression | Coordinator routing triage first — uses TestRunner/TDD evidence plus diff metadata, then routes to TDD (tests deleted) or Programmer (implementation removed covered path) | Regressed files, previous vs current %, diff metadata, latest coverage evidence |
| Architecture violation | Architect | Specific violation, which ADR was breached |
| Spec ambiguity | Spec Agent | Exact ambiguity, what decision is blocked |
| Security finding (Critical/High) | Programmer | Full finding, mitigation steps; Security verifies after fix |
| Security finding (Medium/Low) | Log and continue | — |
| Refactor findings | Refactor Agent | Specific CR finding IDs marked Recommended |
| Refactor proposals accepted by human | Programmer (refactor scope) | Accepted proposals with file refs, ADR constraints — no new TDD, no behavior changes, tests must stay green |
| All integration-contract dependencies Done | Integration Verification (optional) | Integration contracts from each dependent spec, combined test suite |
| Spec misalignment in code | Programmer or Spec Agent | Which requirement, what code does vs what spec says |

---

## Convergence Policy

- **Threshold**: ~90-95% acceptance tests passing before advancing to Code Review (calibrate to risk: payment systems may require 100%)
- **Iteration budget**: 5 total retries across all clusters; escalate any single failing cluster after 3 retries — see `<AI_DEV_SHOP_ROOT>/project-knowledge/governance/escalation-policy.md`

---

## Human Checkpoints (Blocking)

| Checkpoint | Trigger | What Human Decides |
|---|---|---|
| Spec approval | Before Architect dispatch — requires zero unresolved clarification blockers | Is this planning surface complete and correct? |
| Architecture sign-off | Before tasks.md generation and TDD dispatch — requires clean Constitution Check | Is this ADR acceptable? Are all constitution exceptions justified? |
| Convergence escalation | When iteration budget exhausted | Is the spec wrong? Is this a fundamental constraint? |
| Security sign-off | Before merge/deploy | Accept, mitigate, or reject Critical/High findings |
| Refactor review | After Refactor Agent delivers proposals | Accept or reject each proposal; accepted proposals are dispatched to Programmer |

---

## Done State

A feature reaches **Done** when all of the following are true:
1. All three human checkpoints cleared: spec approval, architecture sign-off, security sign-off
2. All tests pass against the certified spec hash
3. All Critical/High security findings are resolved, or accepted with documented rationale in `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/pipeline/<NNN>-<feature-name>/pipeline-state.md`
4. Coverage report is attached to the final TestRunner artifact; hard gates pass per metric using the active profile (defaults: unit lines/branches/functions/statements >= 98%, integration lines/branches/functions/statements >= 90%, e2e lines/branches/functions/statements >= 80%); all High-priority gaps are resolved or explicitly accepted with risk rationale; no uncovered lines remain in changed/high-priority runtime paths without documented technical justification.

The Coordinator issues a **merge-ready summary** to the human:
```
MERGE-READY — <SPEC-ID> v<version>

Spec:     <SPEC-ID> v<version> (hash: <hash>)
Tests:    <N> passing, certified against hash <hash>
ADR:      <path>
Approvals: spec ✓  architecture ✓  security ✓
Security: <"all resolved" | list of accepted-with-rationale findings>
```

The human decides whether to merge. The pipeline does not merge automatically.

---

## Parallel Execution

When the Architect defines independent modules (natural in Vertical Slice, Modular Monolith, Microservices):

1. Coordinator identifies non-overlapping test clusters per module
2. Dispatches separate Programmer instances per module simultaneously
3. Each instance works against its own isolated test set
4. TestRunner aggregates all outputs before routing forward
5. Code Review receives the full combined diff — not individual slices
6. Security receives the combined diff

Parallel rules:
- Respect the system-blueprint dependency graph: slices linked by `Depends on` must be serialized; only dependency-disjoint slices run in parallel
- If a slice depends on another domain's table ownership (FK dependency), sequence it to a later wave after the owner slice merges
- Modules must have no shared mutable state
- No Programmer instance writes to a file another instance reads
- If a shared utility needs changes, serialize — do not parallelize changes to shared code

---

## Context Compression at Scale

For long-running projects where pipeline histories grow large:

- **Cycle summaries only**: Pass the Coordinator's cycle summary to the next cycle, not the full agent output logs
- **Observation masking**: Replace verbose TestRunner output (`Full test output: 2,400 lines`) with a structured summary (`47 passing, 3 failing: [AC-03, INV-01, EC-02]`)
- **Selective memory injection**: Load only the 5 most recent learnings.md entries plus any entries matching the current module's domain terms
- **Projection forward**: If a decision was made in cycle 1 and is still active, reference the ADR — do not re-include the original Architect reasoning in cycle 5 dispatches

---

## Pipeline State Tracking

The Coordinator maintains a state record per run:

```
Pipeline Run: RUN-007
Spec: SPEC-001 v1.2 (hash: abc123)
Human-approved: 2026-02-21T10:00:00Z

Stage status:
  Spec:         DONE  (2026-02-21T10:00:00Z)
  Architect:    DONE  (ADR-003, 2026-02-21T10:30:00Z)
  TDD:          DONE  (47 tests certified against hash abc123)
  Programmer:   IN PROGRESS (cycle 2, 44/47 passing)
  TestRunner:   —
  Code Review:  —
  Security:     —

Active failure clusters:
  AC-03 (Invoice zero-quantity edge case): 2/5 cycle budget
  EC-02 (Idempotency): 1/5 cycle budget

Risk level: Medium
Convergence: 93.6% (threshold: 95%)
```

---

## Escalation Format

When escalating to human, the Coordinator must include:

1. **What is stuck**: Exact test names, spec references, or finding IDs
2. **Full failure history**: Each cycle's attempt and why it didn't resolve it
3. **The decision needed**: Is the spec wrong? Is this a fundamental constraint? Is the architecture unsuitable?
4. **Impact of each option**: If we fix the spec this way, what downstream tests need to be rewritten?
