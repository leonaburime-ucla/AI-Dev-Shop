# Multi-Agent Pipeline

## Full Path (Existing Codebase)

```
[CodeBase Analyzer] → [Architecture Migration Plan] → Spec → [Red-Team] → Architect → TDD → Programmer → TestRunner → Code Review (+Refactor) → Security → Done
```

The `[...]` stages are optional but strongly recommended when dropping AI Dev Shop into a project with existing code.

## Ideal Path (Greenfield)

```
Spec → [Red-Team] → Architect → TDD → Programmer → TestRunner → Code Review (+Refactor) → Security → Done
```

Each stage is blocked until the Coordinator validates the previous stage's handoff contract. No agent talks directly to another — all routing flows through the Coordinator.

---

## Pre-Pipeline: Existing Codebase Analysis

Run this before the first Spec when working with an existing codebase.

### When to Run

- First time AI Dev Shop is dropped into an existing project
- Codebase has significant existing code that may conflict with new feature work
- Architecture of the existing code is unknown or suspected to be problematic

### CodeBase Analyzer Dispatch

Include in context:
- Path to codebase root (or specific modules to analyze)
- Desired output: analysis only, or analysis + migration plan
- Any known constraints (modules to skip, priority areas)

### Using the Output

The CodeBase Analyzer writes reports to `AI-Dev-Shop/codebase-analysis/`. Two ways to use them:

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
- `AI-Dev-Shop/codebase-analysis/ANALYSIS-<id>.md` executive summary
- `AI-Dev-Shop/codebase-analysis/MIGRATION-<id>.md` (if generated)
- Flag: "Existing code has [Critical/High] findings — ADR must acknowledge migration path"

---

## Stage-by-Stage Context Injection

What the Coordinator must include in each agent dispatch. Include only what is listed. Extra context degrades attention quality.

### Spec Agent
- Product intent from human (verbatim)
- Relevant entries from `AI-Dev-Shop/project-knowledge/project_memory.md` (domain conventions)
- Last 3 entries from `AI-Dev-Shop/project-knowledge/learnings.md` (recent failure patterns)
- Existing specs in `AI-Dev-Shop/specs/` (to avoid ID collisions and detect overlap)

**Integration contracts:** If the spec depends on another feature's API, data schema, or event contract, the Spec Agent must include an `## Integration Contracts` section in the spec listing:
- Which features this spec depends on (by SPEC-ID)
- The exact interface boundary: endpoint signatures, data shapes, or event names
- Which ACs require the integration to be live

The Coordinator records these dependencies in `.pipeline-state.md`. When all referenced features reach Done, the Coordinator may trigger an optional Integration Verification run against the combined system.

### Red-Team Agent (runs after Spec approval, before Architect dispatch)
- Active spec (full content + hash)
- `AI-Dev-Shop/agents/red-team/skills.md`

**Routing after Red-Team output:**
- 3+ BLOCKING findings → route to Spec Agent with findings; do not dispatch Architect
- ADVISORY findings only → dispatch Architect, include advisory list in context
- No findings → dispatch Architect normally

### Architect Agent
- Active spec file (full content + hash)
- Red-Team advisory findings (if any)
- Current system boundaries (existing ADRs in `AI-Dev-Shop/specs/`)
- Non-functional constraints from spec
- `AI-Dev-Shop/skills/architecture-decisions/SKILL.md`
- Relevant `AI-Dev-Shop/skills/design-patterns/references/` files (Coordinator selects based on system drivers in spec)

### TDD Agent
- Active spec (full content + hash) — **must be human-approved**
- ADR for the module being tested
- `AI-Dev-Shop/skills/test-design/SKILL.md`
- Relevant entries from `AI-Dev-Shop/project-knowledge/project_memory.md` for the domain

### Programmer Agent
- Active spec (hash must match TDD certification hash)
- Certified test names and which ACs they cover
- ADR for the module (architecture constraints)
- Relevant `AI-Dev-Shop/project-knowledge/project_memory.md` entries
- Handoff output from TDD Agent (summary only, not full session)

### TestRunner Agent
- Test suite location
- Spec hash certified by TDD Agent (to validate drift)
- Previous cycle's failure clusters (to detect regressions)

### Code Review Agent
- Full diff of changed files
- Active spec (for alignment check)
- ADR for the module (for architecture compliance check)
- `AI-Dev-Shop/skills/code-review/SKILL.md`
- `AI-Dev-Shop/skills/security-review/SKILL.md` (for surface flagging)
- Previous Code Review findings (to detect recurrence)

### Refactor Agent
- Specific Code Review findings classified as Recommended
- Affected file contents
- ADR constraints (to verify refactors stay within architecture)
- `AI-Dev-Shop/skills/refactor-patterns/SKILL.md`

### Security Agent
- Full diff of changed files
- Spec (for business logic abuse vector analysis)
- List of changed auth/payment/data paths (Coordinator identifies these from the diff)
- `AI-Dev-Shop/skills/security-review/SKILL.md`

### Observer Agent (runs alongside, not in sequence)
- All agent outputs from the current cycle (summaries, not full sessions)
- Previous Observer reports (for trend analysis)
- `AI-Dev-Shop/project-knowledge/learnings.md` (to cross-reference new patterns against known ones)

---

## Routing Rules (Coordinator-owned)

| Finding | Route To | Context to Include |
|---|---|---|
| Spec human-approved | Red-Team Agent | Full spec, spec hash |
| Red-Team: 3+ BLOCKING | Spec Agent | All BLOCKING findings with exact spec refs |
| Red-Team: ADVISORY only | Architect | Spec, spec hash, advisory list |
| Test failures | Programmer | Failing test names, spec ACs, ADR constraints |
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
- **Iteration budget**: 5 total retries across all clusters; escalate any single failing cluster after 3 retries — see `AI-Dev-Shop/project-knowledge/escalation-policy.md`

---

## Human Checkpoints (Blocking)

| Checkpoint | Trigger | What Human Decides |
|---|---|---|
| Spec approval | Before Architect dispatch | Is this spec complete and correct? |
| Architecture sign-off | Before TDD dispatch | Is this ADR acceptable? |
| Convergence escalation | When iteration budget exhausted | Is the spec wrong? Is this a fundamental constraint? |
| Security sign-off | Before merge/deploy | Accept, mitigate, or reject Critical/High findings |
| Refactor review | After Refactor Agent delivers proposals | Accept or reject each proposal; accepted proposals are dispatched to Programmer |

---

## Done State

A feature reaches **Done** when all of the following are true:
1. All three human checkpoints cleared: spec approval, architecture sign-off, security sign-off
2. All tests pass against the certified spec hash
3. All Critical/High security findings are resolved, or accepted with documented rationale in `.pipeline-state.md`

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
