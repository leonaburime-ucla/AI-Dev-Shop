You are the Coordinator dispatching a reverse-spec extraction workflow.

Task: $ARGUMENTS

---

## Purpose

Extract behavioral specifications from an existing codebase. This is the entry point for code-to-spec-to-rewrite workflows: an existing system becomes a language-agnostic spec that can be implemented in any target language.

## Before Doing Anything

1. Read `<AI_DEV_SHOP_ROOT>/skills/reverse-spec/SKILL.md` — methodology, confidence rules, guardrails, exit criteria
2. Read `<AI_DEV_SHOP_ROOT>/agents/codebase-analyzer/skills.md`
3. Read `<AI_DEV_SHOP_ROOT>/framework/spec-providers/active-provider.md`

The SKILL.md is authoritative for all extraction rules (confidence hierarchy, exit criteria, guardrails, scope thresholds). This coordinator defines workflow orchestration only.

## Arguments

- `[scope] [path] [options]`
- `scope` (optional):
  - `full` — extract the entire application (use bounded per-module runs for large codebases)
  - `module=<path>` — extract one module, service, or directory
  - `endpoint=<route-pattern>` — extract a specific endpoint or route group
  - Default: `full` if path is below the SKILL.md scope threshold; otherwise prompt for scope narrowing
- `path` — path to the codebase or module root to extract from
- `options` (optional):
  - `layers=<layer-ids>` — which extraction layers to include. Valid IDs defined in `references/extraction-layers.md`: `api`, `domain`, `side-effect`, `data`, `database`, `access-control`, `transaction`, `concurrency`, `failure`, `integration`, `compliance`, `performance`, `observability`, `client-invalidation`, `cache`, `infrastructure`, `migration`, `security` (default: all)
  - `depth=<contracts-only|with-internals>` — `contracts-only` extracts external behavior; `with-internals` also documents internal function contracts for complex modules (default: `contracts-only`)
  - `target_lang=<python|go|java|etc>` — optional hint passed to Architect later (does NOT affect extraction — specs are always language-agnostic)

## Workflow

### Step 1: CodeBase Analyzer — Inventory

Dispatch the CodeBase Analyzer to produce a structural map of the target path:
- Entrypoint inventory (routes, jobs, CLI, events, WebSocket, admin endpoints, file import/export)
- External integrations (APIs called, webhooks sent/received, queue connections)
- Data stores (databases, caches, object storage, search indexes)
- Database-resident logic (triggers, stored procedures, views, cascades)
- Tech stack detection (language, framework, ORM, test framework)
- Module boundaries and dependency graph
- Test coverage assessment (which areas have tests, which don't)
- Scheduled tasks and cron jobs
- OS-level subprocess dependencies (media processors, PDF generators, system binaries)

**Output:** Structured inventory in `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/reverse-spec/<module-or-app>/inventory.md`

**Human checkpoint:** Confirm the inventory is correct and scope is bounded before proceeding to extraction.

### Step 2: Reverse-Spec Extraction

**IMPORTANT: Do NOT run all phases in a single pass.** The extraction phases run as a DAG of bounded passes to prevent context window degradation. Each pass produces intermediate artifacts that subsequent passes consume.

**Per-pass load strategy:** When dispatching each pass, load:
1. `<AI_DEV_SHOP_ROOT>/skills/reverse-spec/SKILL.md` (always — confidence rules, guardrails, exit criteria)
2. `<AI_DEV_SHOP_ROOT>/skills/reverse-spec/references/extraction-layers.md` (always — output schema)
3. The pass-specific reference file (see below)
4. Any additional references triggered by that pass (see below)

---

**Pass 1 — Core Logic (code-centric):**

Load: `references/pass-1-core-logic.md` + `references/characterization-tests.md` (for Phase 1b)

- Phase 0: Inventory (confirm entrypoint map)
- Phase 1: Test-First Extraction
- Phase 1b: Characterization Evidence Pack
- Phase 2: Code Extraction
- Phase 2b: Inline Documentation Extraction
- Phase 3: Convention Scanner
- Phase 3b: Numerical/String/Semantic Precision

→ Output: `artifact-1-core-logic.md` — entrypoint map, reachability graph, core behavioral requirements with confidence labels, characterization tests, precision contracts, environmental contracts

---

**Pass 2 — Data, Access, and Atomicity:**

Load: `references/pass-2-data-and-access.md` + `references/data-migration.md` (when schema/data store changes detected)

Reads: `artifact-1-core-logic.md`

- Phase 4: Database-Resident Behavior (ID format contracts, triggers, procs, constraints)
- Phase 5: Access-Control Matrix
- Phase 6: Transaction and Atomicity Contracts (cross-domain flagging, temporal invariants)
- Phase 6b: Concurrency and In-Memory State

→ Output: `artifact-2-data-access.md` — data contracts, ID format contracts, ACL matrix, transaction boundaries, concurrency contracts, temporal coupling inventory

---

**Pass 3 — Boundaries, Failures, and Compliance:**

Load: `references/pass-3-boundaries.md`

Reads: `artifact-1-core-logic.md`, `artifact-2-data-access.md`

- Phase 7: Failure Matrix (protocol-level exactness, dynamic return types)
- Phase 8: Integration Boundary Extraction (async job semantics, third-party API versioning, client state invalidation)
- Phase 9: Privacy, Compliance, and Security Primitives
- Performance Envelopes (from runtime evidence)
- Observability Contracts

→ Output: `artifact-3-boundaries.md` — failure matrices, integration contracts, security primitives, compliance requirements, performance envelopes, observability contracts

---

**Pass 4 — External Systems, Consumers, and Human Workflows:**

Load: `references/pass-4-external.md`

Reads: `artifact-1-core-logic.md`, `artifact-2-data-access.md`, `artifact-3-boundaries.md`

- Phase 10: External Control Plane and Infrastructure (tool-gated)
- Consumer Inventory (all consumers of system outputs)
- Durable Links and Historical Outputs
- Human Workflows and Operational Procedures
- Customer-Specific Behavior
- Client-Side Implicit Contracts
- Frontend/Client Behavior (for full-stack rewrites)

→ Output: `artifact-4-external.md` — external contracts, consumer inventory, human workflows, client contracts, all `[HUMAN DATA REQUEST]` items

Note: Pass 4 may require sub-chunking for large systems with many external integrations.

---

**Pass 5 — Synthesis and Conflict Resolution:**

Load: `references/pass-5-synthesis.md`

Reads: ALL prior artifacts (`artifact-1` through `artifact-4`)

- Phase 11: Conflict Resolution and Gap Marking
- Merge all pass outputs into unified requirements
- Resolve amendments from later passes
- Adversarial verification (requirements without evidence, inferred marked confirmed, missing failure cases, implementation leaking into contracts)
- Produce coverage map, extraction manifest, review digest, and intentional-changes aggregation

→ Output:
  - `merged-requirements.md` — unified spec
  - `review-digest.md` — all human-attention items ordered by blocking severity
  - `extraction-manifest.md` — frozen source-of-truth header
  - `coverage-map.md` — per-entrypoint status
  - `consumer-inventory.md` — all known consumers
  - `intentional-changes.md` — aggregated non-preserve decisions
  - `characterization-tests/` — golden fixtures and contract tests

---

Each pass should be dispatched as a separate sub-agent call or bounded context. If entrypoints missed by the inventory are discovered during any pass, update the inventory and note the addition.

For large codebases (above the SKILL.md scope threshold): run per-module in priority order (max 30 requirements per chunk before human review). Produce a coverage map after each module.

**Output:** Raw extracted requirements in `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/reverse-spec/<module-or-app>/`

**Extraction rules** (summary — see SKILL.md for full detail):
- Follow the Confidence Hierarchy strictly (two hierarchies: external vs internal)
- Cite source evidence for every requirement
- Keep migration notes separate from behavioral contracts
- Flag `[NEEDS CLARIFICATION]` on any contradiction
- Do not invent behavior — only extract what evidence supports
- Apply unknown-vs-none discipline (never write "none" without investigation)

### Step 3: Spec Agent Normalization

Dispatch the Spec Agent to normalize extracted requirements into the active spec provider's format:

- Group requirements by feature/module boundary
- Apply the standard spec template (from the active provider)
- Preserve all traceability metadata that survives normalization (see SKILL.md Output Template Precedence and Normalization Safety rules)
- Carry forward all `[NEEDS CLARIFICATION]` markers as blockers

**Output:** Standard spec package in the active provider's format at the normal spec location.

**Human checkpoint (blocking):** Review the normalized spec using `review-digest.md` as the review surface. Verify:
- Accuracy: does each requirement match your understanding of the system?
- Completeness: are there behaviors you know exist that aren't captured?
- Overspecification: are any implementation details leaking into requirements?
- Intentional changes: review `intentional-changes.md` — are all fix/remove decisions correct?
- Clarifications: resolve any `[NEEDS CLARIFICATION]` markers
- Coverage: does `coverage-map.md` meet the exit criteria threshold?

Do NOT proceed past this checkpoint without human approval. Extracted specs become the rewrite contract — errors here propagate into the entire target implementation.

### Step 4: Pipeline Continues

After human approval, the spec enters the normal pipeline:
- Architect designs the target architecture (using `target_lang` hint if provided)
- TDD writes tests from the behavioral specs (characterization tests provide the parity oracle)
- Programmer implements in the target language

The `target_lang` option is passed to the Architect at this stage — it was deliberately kept out of extraction to prevent source-language bias in the spec.

## What This Command Does NOT Do

- Does not write code or implementation
- Does not choose the target architecture (that's the Architect's job)
- Does not require a target language to run (extraction is language-agnostic)
- Does not replace CodeBase Analyzer (it uses its output as input)
- Does not replace the Spec Agent (it feeds into it)
- Does not skip the human checkpoint (extracted specs are too important to auto-approve)
- Does not verify rewrite parity (that happens post-implementation using characterization tests)
