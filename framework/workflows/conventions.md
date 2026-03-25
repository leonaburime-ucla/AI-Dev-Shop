---
name: conventions
version: 1.2.0
last_updated: 2026-03-24
description: Output root, spec folder structure, and reports folder structure for all pipeline artifacts.
---

# Conventions

## Output Root

`<AI_DEV_SHOP_ROOT>` means the path to this toolkit folder (usually `AI-Dev-Shop-speckit/`).
Resolve the active planning provider from `<AI_DEV_SHOP_ROOT>/framework/spec-providers/active-provider.md` before assuming planning filenames or folder structure.
Provider-native planning artifacts are written to the **user-specified location** or native provider folders — the Spec Agent asks before writing when the location is not already known. Pipeline artifacts retained by AI Dev Shop core (ADR, research, tasks, test-certification, red-team findings, pipeline state) are written under `<AI_DEV_SHOP_ROOT>/framework/reports/pipeline/<NNN>-<feature-name>/`. Reports (analysis, test runs, code review, security, observer) live in `<AI_DEV_SHOP_ROOT>/framework/reports/` subfolders.
For long-running or resumable work, use a `progress-ledger.md` in the appropriate reports folder per `<AI_DEV_SHOP_ROOT>/harness-engineering/session-continuity.md`.
For large raw outputs, logs, or traces, use offload files per `<AI_DEV_SHOP_ROOT>/harness-engineering/context-offloading.md`.
For runtime-changing work that needs app-level validation before handoff, use a self-validation report per `<AI_DEV_SHOP_ROOT>/harness-engineering/self-validation.md`.
For work that requires an independent evaluator loop, use retained evaluator artifacts per `<AI_DEV_SHOP_ROOT>/harness-engineering/evaluation-loops.md`.
Use `<AI_DEV_SHOP_ROOT>/.local-artifacts/` for ignored local-only scratch artifacts such as exploratory consensus runs, raw peer stdout/stderr captures, temporary prompts, and host-specific smoke-test baselines that are not meant to ship with the repo.
Promote artifacts from `.local-artifacts/` into `framework/reports/` only when the user explicitly wants them retained as reusable project evidence.

**Writable under `<AI_DEV_SHOP_ROOT>`:** `framework/reports/`, `project-knowledge/`, `.local-artifacts/`
**Read-only during normal feature work under `<AI_DEV_SHOP_ROOT>`:** `agents/`, `skills/`, `framework/spec-providers/`, `framework/templates/`, `framework/workflows/`, `framework/slash-commands/` — toolkit source files. If the user explicitly asks to maintain or upgrade the toolkit itself, treat that as framework maintainer work and allow edits in these directories.

---

## Artifact Intent Policy

Before writing any new artifact, classify it into one of these buckets:

1. **Pipeline-required**
   - Examples: ADRs, `tasks.md`, `test-certification.md`, red-team findings, `.pipeline-state.md`, required codebase-analysis outputs
   - Behavior: save automatically to `framework/reports/` in the canonical path defined by the workflow
2. **Optional retained**
   - Examples: exploratory research summaries, consensus reports, architecture comparisons, reusable context packets, host compatibility baselines
   - Behavior: if the user has not already said to save it, ask whether to retain it in `framework/reports/`, keep it `local only`, or return it `inline only`
3. **Local scratch / raw evidence**
   - Examples: temporary prompts, raw stdout/stderr captures, ad hoc smoke tests, one-off logs, intermediate notes
   - Behavior: save to `.local-artifacts/` by default unless the user explicitly wants it promoted into `framework/reports/`

Rule of thumb:
- `framework/reports/` is for canonical retained artifacts the project may rely on later
- `.local-artifacts/` is for personal iteration output and disposable session evidence
- Do not ask permission before writing pipeline-required artifacts that the framework depends on

---

## Planning Surface Convention

Planning artifacts live at the provider-defined location. The exact file set comes from the active provider profile.

Required provider-recorded paths:
- `spec_provider`
- `spec_entrypoint_path`
- `spec_readiness_artifact`

Optional but recommended:
- `spec_support_paths`
- `provider_native_root`

### Default Speckit Example

```
<user-specified>/<NNN>-<feature-name>/
  feature.spec.md          (canonical spec — use framework/templates/spec-system/feature.spec.md)
  api.spec.md              (typed API contracts — if applicable)
  state.spec.md            (state shapes and transitions — if applicable)
  orchestrator.spec.md     (orchestrator output model — if applicable)
  ui.spec.md               (UI component contracts — if applicable)
  errors.spec.md           (error code registry — if applicable)
  behavior.spec.md         (deterministic behavior rules — if applicable)
  traceability.spec.md     (REQ-to-function-to-test matrix)
  spec-manifest.md         (lists actual filenames, omitted files, and naming choice)
  spec-dod.md              (DoD checklist — must pass before Architect dispatch)
```

## Pipeline Artifact Folder Convention

All pipeline artifacts for a feature live under `<AI_DEV_SHOP_ROOT>/framework/reports/pipeline/`:

```
<AI_DEV_SHOP_ROOT>/framework/reports/pipeline/<NNN>-<feature-name>/
  .pipeline-state.md       (Coordinator state — created at spec time, updated every stage)
  progress-ledger.md       (human/agent-readable resume ledger for long-running work)
  evaluator-contract-<slug>.md   (required when evaluator_mode is required for this feature run)
  evaluator-report-<slug>-<YYYY-MM-DD-HHmm>.md   (retained evaluator findings when kept as evidence)
  offloads/                (optional raw logs, traces, JSON blobs, large diffs for this feature)
  adr.md                   (architecture decision record)
  research.md              (if produced by Architect)
  tasks.md                 (generated by Coordinator after ADR approval)
  test-certification.md    (generated by TDD Agent)
  red-team-findings.md     (generated by Red-Team Agent — audit trail)
```

`<NNN>` is a zero-padded three-digit FEAT number (001, 002, ...). `<feature-name>` is 2–4 words, lowercase-hyphenated. Example: `framework/reports/pipeline/003-csv-invoice-export/`. Scan existing `framework/reports/pipeline/` folders for the next available number — never reuse. The pipeline state should record the provider, the provider-native spec entrypoint, and the readiness artifact for the run. Existing `spec_path` fields remain valid compatibility fields for the default Speckit provider.

---

## Local Scratch Artifact Convention

Use `.local-artifacts/` for local-only, ignored outputs that help the current session but are not canonical repo artifacts.

```text
<AI_DEV_SHOP_ROOT>/.local-artifacts/
  swarm-consensus/
    prompts/
    context/
    runs/
    offloads/
    smoke-tests/
  external-audit/
    packets/
    runs/
    offloads/
```

**Rules:**
- `.local-artifacts/` is ignored by git and safe for personal iteration outputs.
- Use it by default for ad hoc consensus runs, temporary context packets, raw CLI captures, and smoke-test artifacts.
- If a debate, context packet, or smoke-test result becomes worth keeping for future project use, copy or rewrite the final retained artifact into `framework/reports/`.
- Optional reports outside swarm consensus follow the same rule: local by default unless the user explicitly retains them.

---

## Reports Folder Convention

All agent reports live under a single centralized folder. This is the single source of truth for retained artifacts outside of spec files. The subdirectory structure is pre-created in the repo — agents can write directly without creating directories.

```
<AI_DEV_SHOP_ROOT>/framework/reports/
  pipeline/
    <NNN>-<feature-name>/    (per-feature — see Pipeline Artifact Folder Convention above)
  codebase-analysis/
    ANALYSIS-<id>-<YYYY-MM-DD>.md     (CodeBase Analyzer — findings report)
    MIGRATION-<id>-<YYYY-MM-DD>.md    (CodeBase Analyzer — migration plan, if requested)
  test-runs/
    TESTRUN-<feature-id>-<YYYY-MM-DD-HHmm>.md  (TestRunner — one file per run, never overwritten)
  security/
    SEC-<feature-id>-<YYYY-MM-DD>.md  (Security Agent — threat findings)
  code-review/
    CR-<feature-id>-<YYYY-MM-DD>.md   (Code Review Agent — findings)
  observer/
    timeline-CYCLE-<NNN>.md           (Observer — per-cycle timeline log)
    pattern-report-<YYYY-WNN>.md      (Observer — weekly pattern report)
  swarm-consensus/
    smoke-tests/
      <timestamp>-cli-smoke-test.md   (user-approved retained host capability baseline)
    context/
      CTX-<slug>-<YYYY-MM-DD>.md      (user-approved shared packet used by all consensus participants)
    runs/
      <timestamp>-consensus-report.md (user-approved templated consensus report)
  external-audit/
    packets/
      <timestamp>-audit-packet.md     (optional retained packet summarizing the work given to the external auditor)
    runs/
      <timestamp>-external-audit-report.md  (user-approved external audit report with Coordinator synthesis)
  continuity/
    <workstream>/progress-ledger.md   (non-feature resumable work such as toolkit maintenance)
    <workstream>/evaluator-contract-<slug>.md   (non-feature retained evaluator contract)
    <workstream>/evaluator-report-<slug>-<YYYY-MM-DD-HHmm>.md   (non-feature retained evaluator report)
  offloads/
    <workstream>/<timestamp>-<slug>.md  (large logs, diffs, traces, JSON blobs)
  self-validation/
    SV-<feature-or-workstream>-<YYYY-MM-DD-HHmm>.md  (runtime validation report)
  maintenance/
    harness-maintenance.md            (generated cleanup/health report)
    harness-load-bearing-<YYYY-MM-DD>.md  (retained load-bearing harness audit)
```

**Rules:**
- `framework/reports/` is for retained project artifacts, not disposable session scratch
- All agents write retained reports here — do not scatter canonical report files elsewhere
- Test run reports are timestamped and never overwritten — each run is a separate audit artifact
- The Programmer reads test state by running tests fresh, not by reading reports — reports are audit trail only
- Provider-native planning artifacts live outside `framework/reports/` unless the provider profile explicitly says otherwise
- Pipeline artifacts (adr.md, tasks.md, test-certification.md, red-team-findings.md) live in `framework/reports/pipeline/<NNN>-<feature-name>/`, not scattered elsewhere
