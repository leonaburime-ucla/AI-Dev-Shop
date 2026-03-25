# Templates

This directory contains the foundational document templates used by the AI Dev Shop multi-agent pipeline. Agents use these templates to structure their output, ensuring consistency, enforceability, and smooth handoffs between pipeline stages.

Provider note:
- the active upstream planning provider is resolved from `framework/spec-providers/active-provider.md`
- the files in `framework/templates/` currently serve as the validated Speckit compatibility surface
- non-Speckit providers should resolve their planning contract from `framework/spec-providers/<provider>/provider.md` before assuming any file in this directory is canonical for that run

## Subdirectories

- **`spec-system/`**: Contains the strict-mode 9-file spec package templates. This is the modern, multi-file approach to specification (replaces the legacy single-file `spec-template.md`).
- **`bootstrap/`**: Contains initialization templates intended to be copied into a new project's workspace (e.g., the base constitution template) rather than used directly in the pipeline.
- **`self-validation/`**: Stack-specific runtime validation templates for downstream repos that need app boot, log inspection, and critical-path checks before handoff.

## Active Templates

- **`adr-template.md`**: Used by the Architect Agent to record Architecture Decision Records (ADRs). Includes forced sections for constitution compliance and complexity justification.
- **`context-offload-template.md`**: Used when large logs, traces, or raw outputs should be saved to a durable file instead of staying inline in chat or handoffs.
- **`evaluator-contract-template.md`**: Used when a long-running build needs an explicit generator/evaluator contract before coding starts.
- **`evaluator-report-template.md`**: Used when a retained evaluator run should record scope check, findings, blocking outcome, and next action for the generator.
- **`handoff-template.md`**: The mandatory contract format used by every agent at the end of their execution. It ensures the next agent in the pipeline receives the correct input hashes, context, and risk warnings.
- **`load-bearing-harness-audit-template.md`**: Used for retained maintenance audits that test whether older harness components are still needed on current models and hosts.
- **`red-team-template.md`**: Used by the Red-Team Agent to output vulnerability, ambiguity, and logic-flaw findings against a proposed spec.
- **`research-template.md`**: Used by the Architect Agent when evaluating multiple potential solutions or external libraries before committing to an ADR.
- **`system-blueprint-template.md`**: Used by the System Blueprint Agent during macro-level planning to map out component domains before detailed feature specs are written.
- **`tasks-template.md`**: Used by the Coordinator to break down an approved ADR and spec into parallelizable implementation tasks for the TDD and Programmer agents.
- **`tdd-coverage-triage-template.md`**: Used during the test gap-fill loop to categorize missing coverage and assign priority to unhandled edge cases.
- **`test-certification-template.md`**: Used by the TDD Agent to prove that tests have been written against the active spec hash, certifying readiness for the Programmer Agent to begin implementation.
- **`self-validation/*.md`**: Used for downstream runtime smoke-validation loops by stack (generic web app, Node API, Python service, Supabase).
