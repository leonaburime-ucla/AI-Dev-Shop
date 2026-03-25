# Tasks: <feature-name>

> **tasks.md is always required.** The Coordinator generates it after every ADR approval. The TDD Agent is not dispatched until tasks.md exists. For simple features with a single task and no parallelism, use the minimal format at the bottom of this file instead of the full phased template.

- Spec: SPEC-<id> v<version> (hash: <sha256>)
- ADR: ADR-<id>
- Date: <ISO-8601 UTC>
- Author: Coordinator

## Format

`[ID] [P?] [Story ref] Description`

- **[P]**: Task can run in parallel — touches different files, no shared mutable state with other [P] tasks in the same phase
- **[Story ref]**: Maps to an acceptance criterion or invariant (e.g., AC-01, INV-01)
- Every task references exact file paths

---

## Phase 0 — Setup

Project initialization and tooling. No story dependencies.

- [ ] T001 [P] Create directory structure per ADR module boundaries
- [ ] T002 [P] Initialize project configuration files
- [ ] T003 [P] Configure linting, formatting, and CI hooks

---

## Phase 1 — Foundational

Core infrastructure that blocks all stories. **No story work begins until this phase is complete.**

- [ ] T004 Create base data models / entities — `src/...`
- [ ] T005 [P] Set up persistence layer per ADR — `src/...`
- [ ] T006 [P] Set up logging and error handling infrastructure — `src/...`
- [ ] T007 Configure environment and secrets management

**Checkpoint**: Foundation complete — story phases can now begin (in parallel if modules are independent per ADR).

---

## Phase 2 — [Story: AC-01] <story title> (P1)

**Goal**: <what this story delivers independently>
**Independent test**: <how to verify this story works in isolation without other stories>

- [ ] T008 [P] [AC-01] Write failing tests for <component> — `tests/...`
- [ ] T009 [P] [AC-01] Write failing tests for <component> — `tests/...`
- [ ] T010 [AC-01] Implement <model/entity> — `src/...`
- [ ] T011 [AC-01] Implement <service> — `src/...` (depends on T010)
- [ ] T012 [AC-01] Implement <interface/endpoint> — `src/...` (depends on T011)
- [ ] T013 [AC-01] Run tests to convergence

**Checkpoint**: AC-01 passing — story independently testable and complete.

---

## Phase 3 — [Story: AC-02] <story title> (P2)

**Goal**: <what this story delivers independently>
**Independent test**: <how to verify this story works in isolation>

- [ ] T014 [P] [AC-02] Write failing tests for <component> — `tests/...`
- [ ] T015 [AC-02] Implement <model/entity> — `src/...`
- [ ] T016 [AC-02] Implement <service> — `src/...` (depends on T015)
- [ ] T017 [AC-02] Integrate with Phase 2 components if needed
- [ ] T018 [AC-02] Run tests to convergence

**Checkpoint**: AC-02 passing — story independently testable and complete.

---

## Phase N — Polish

Cross-cutting improvements after all required stories pass.

- [ ] TXXX [P] Documentation updates
- [ ] TXXX [P] Additional unit tests for pure logic
- [ ] TXXX Performance instrumentation
- [ ] TXXX Security hardening pass

---

## Parallelization Rules

- Tasks marked [P] in the same phase can be dispatched simultaneously
- Modules must have no shared mutable state during parallel execution
- No Programmer instance writes to a file another instance reads
- If a shared utility needs changes, serialize — do not parallelize writes to shared code

## Execution Strategies

**Sequential (single agent):** Phase 0 → Phase 1 checkpoint → Phase 2 → Phase 3 → Phase N

**Parallel (multiple Programmer instances):** Phase 0 → Phase 1 checkpoint → Phase 2 + Phase 3 simultaneously (only if ADR defines independent modules) → TestRunner aggregates → Phase N

---

## Minimal Format (simple features — single task, no parallelism)

Use this instead of the full template when the feature has one implementation task with no phases required.

```markdown
# Tasks: <feature-name>

- Spec: SPEC-<id> v<version> (hash: <sha256>)
- ADR: ADR-<id>
- Date: <ISO-8601 UTC>
- Author: Coordinator

## Tasks

- [ ] T001 [AC-01, AC-02] Write failing tests — `tests/...`
- [ ] T002 [AC-01, AC-02] Implement <feature> — `src/...` (depends on T001)
- [ ] T003 Run tests to convergence

**Checkpoint**: Human reviews test results before Code Review dispatch.
```
