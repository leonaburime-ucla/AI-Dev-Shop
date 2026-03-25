# Harness Engineering

This folder is the repo-local system of record for harness engineering work in AI Dev Shop.

Harness engineering means building the scaffolding around agents so they can work reliably: knowledge maps, validators, guardrails, eval loops, cleanup cadences, and feedback systems.

This first rollout is intentionally pragmatic. It does not try to rewrite the framework in one pass. It adds local references, executable validators, a quality baseline, and an active rollout plan.

## Design Principles

- Map, not manual: keep root instructions short and push detail into linked sources of truth.
- Repository-local knowledge: if the agent cannot discover it in-repo, it is operationally invisible.
- Mechanical enforcement first: convert important markdown rules into checks that fail loudly with fix guidance.
- Progressive disclosure: give agents only the context they need for the current task.
- Closed-loop improvement: recurring failures should become guardrails, benchmarks, or skill updates.
- Continuous garbage collection: keep drift small and frequent instead of waiting for a large cleanup event.

## Folder Layout

```text
harness-engineering/
  README.md
  capability-verification.md
  ci-enforcement.md
  context-firewalls.md
  context-offloading.md
  doc-staleness-policy.md
  doc-staleness-watchlist.md
  failure-promotion-policy.md
  observer-cadence.md
  registry-integrity-policy.md
  self-validation.md
  session-continuity.md
  tripwires.md
  quality-score.md
  subagent-usage-policy.md
  tech-debt-tracker.md
  plans/
    active/
    completed/
  references/
  validators/
```

## What Is Implemented Now

- Local reference notes distilled from primary-source harness guidance
- A harness rollout plan and debt tracker
- An initial quality score baseline for this repo
- Executable validators for path references and skills-registry integrity
- A doc-garden audit script for advisory health signals
- Local reference notes for OpenAI, Anthropic, LangChain, and Vercel harness patterns
- An explicit Observer/doc-garden cadence for toolkit maintenance
- Seed benchmark fixtures for the golden-sample pre-implementation stages
- A failure-promotion rule for turning repeated mistakes into durable harness artifacts
- CI enforcement guidance plus a GitHub Actions workflow that runs the validator entrypoint
- A durable progress-ledger pattern for resumable long-running work
- Deterministic pre-completion and loop-detection tripwires
- A hard-fail policy for shared-skills registry coverage plus an intentional-exclusion escape hatch
- A capability-verification policy plus a local host probe for version-sensitive runtime features
- A subagent-usage policy plus runtime mode resolution for automatic helper-agent defaulting
- A file-trigger routing table and context-firewall rules for cleaner discovery dispatch
- A file-backed context-offloading rule for long logs, traces, and retry evidence
- Stack-specific self-validation templates for downstream runtime checks
- A maintenance-report generator plus scheduled cleanup workflow support
- A narrow doc-staleness watchlist plus advisory audit for high-risk source-of-truth docs

## How To Use

Run the full first-pass harness checks:

```bash
bash harness-engineering/validators/run-all.sh
```

Inspect capability status on the current host:

```bash
bash harness-engineering/validators/probe_host_capabilities.sh
```

Resolve automatic subagent mode for the current host:

```bash
bash harness-engineering/validators/resolve_subagent_mode.sh --host <detected-host>
```

Run the validators individually:

```bash
python3 harness-engineering/validators/validate_path_references.py
python3 harness-engineering/validators/validate_registry_integrity.py
python3 harness-engineering/validators/doc_garden_audit.py
```

## Current Boundaries

- These validators currently check repository knowledge integrity, not application runtime behavior.
- Self-validation templates live here, but the project-specific repo that uses this toolkit must still define the actual boot commands, health checks, critical-path assertions, and any richer static-analysis/runtime enforcement it wants. The bounded retry and optional sidecar-diagnosis rules live in `harness-engineering/self-validation.md`; the host project supplies the concrete commands those rules execute.
- Enterprise shift-left harnesses remain in `skills/enterprise-spec/`; this folder is the broader repo-level harness layer.
- `AGENTS.md` reduction is intentionally tracked separately in `todo.md` so the harness layer can stabilize first.

## Primary Source References

- OpenAI: `references/openai-harness-engineering.md`
- OpenAI: `references/openai-practical-guide.md`
- Anthropic: `references/anthropic-effective-harnesses.md`
- Anthropic: `references/anthropic-guardrails.md`
- LangChain: `references/langchain-anatomy-agent-harness.md`
- LangChain: `references/langchain-improving-deep-agents.md`
- Vercel: `references/vercel-ai-engineering-company.md`
