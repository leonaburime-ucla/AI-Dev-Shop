# Harness Validators

These validators are the first mechanical enforcement layer for this repo.

## Hard Validators

- `validate_path_references.py`
  - checks that repo-local markdown path references point to real files or directories
- `validate_registry_integrity.py`
  - checks that `skills-registry.md` entries point to real files
  - fails when canonical skill files exist on disk but are not registered
  - allows explicit exclusions only through `framework/routing/skills-registry-exceptions.md`
- `validate_evaluator_artifacts.py`
  - checks retained evaluator contracts and evaluator reports for required fields and sections
  - fails when a `progress-ledger.md` marks `evaluator_mode: required` but no retained evaluator contract is recorded
- `validate_load_bearing_audits.py`
  - checks retained `project-knowledge/reports/maintenance/harness-load-bearing-*.md` reports for required sections and decision labels
- `validate_debate_routing_guard.py`
  - checks that debate requests default to Swarm Consensus with external peer LLMs
  - fails when the guard against silent platform-subagent fallback is removed from root, Coordinator, slash-command, or Swarm Consensus docs
- `validate_swarm_model_identity_guard.py`
  - checks that Swarm Consensus preflight shows peer model identity first
  - fails when CLI version strings can be presented as model names or model versions
- `validate_eval_suite.py`
  - validates seeded eval suite metadata and saved run results
  - checks coverage-matrix cells, seed-catalog taxonomy values, benchmark-vs-regression suite rules, run-manifest model provenance, and per-run seed completeness
  - intended for targeted use on `.local-artifacts/agent-evals/<suite-id>/` rather than repo-wide `run-all.sh`
## Advisory Audit

- `doc_garden_audit.py`
  - reports repo-health signals that maintainers should review regularly
  - does not fail the run by itself
- `doc_staleness_audit.py`
  - checks a narrow watchlist of high-risk docs against concrete source-of-truth targets and review cadence
  - advisory only; intended to catch silent routing/workflow drift early
- `generate_maintenance_report.py`
  - refreshes `project-knowledge/reports/maintenance/harness-maintenance.md` from current repo state
  - intended for scheduled maintenance workflows and manual maintainer passes
- `probe_host_capabilities.sh`
  - checks version-sensitive host capabilities against the local environment when a reliable probe exists
  - prints `enabled`, `unavailable`, or `unverified` instead of relying on stale memory or docs alone
  - intended for explicit audits, troubleshooting, or filtered host checks rather than mandatory startup
- `resolve_subagent_mode.sh`
  - resolves whether the current run should default to `subagent-assisted` or `single-agent` mode
  - emits startup-friendly copy that includes the token-cost tradeoff and user toggles
  - probes only the current host's `subagent_spawning` status so startup stays cheap

## Run Everything

```bash
bash harness-engineering/validators/run-all.sh
```

## Probe Current Host Capabilities

```bash
bash harness-engineering/validators/probe_host_capabilities.sh --host <detected-host>
```

Check whether live browser automation is enabled on the current host:

```bash
bash harness-engineering/validators/probe_host_capabilities.sh --host <detected-host> --capability browser_automation
```

Check whether live Supabase verification is enabled on the current host:

```bash
bash harness-engineering/validators/probe_host_capabilities.sh --host <detected-host> --capability supabase_mcp
```

Resolve startup mode for the current host:

```bash
bash harness-engineering/validators/resolve_subagent_mode.sh --host <detected-host>
```

Validate a Speckit package before planning:

```bash
python3 framework/spec-providers/speckit/validators/validate_spec_package.py <spec-folder>
```

Provider-local validator:

- `framework/spec-providers/speckit/validators/validate_spec_package.py`
  - validates the strict Speckit compatibility package
  - checks required files, unresolved clarification markers, manifest integrity, traceability seeding, and DoD completion
  - intended as a targeted pre-handoff validator before `/plan`, not as a repo-wide `run-all.sh` check

Validate a seeded eval suite before using it as benchmark evidence:

```bash
python3 harness-engineering/validators/validate_eval_suite.py .local-artifacts/agent-evals/<suite-id> --require-run-results --min-runs 3
```

Score a validated suite and generate the aggregate metrics report:

```bash
python3 harness-engineering/quality/scripts/score_eval_suite.py .local-artifacts/agent-evals/<suite-id>
```

Score with attention-budget regression detection against a baseline:

```bash
python3 harness-engineering/quality/scripts/score_eval_suite.py .local-artifacts/agent-evals/<suite-id> \
  --baseline-results <path-to-previous-run-results.tsv>
```

Validate a targeted regression pack that intentionally reruns only previously
missed or partial seeds:

```bash
python3 harness-engineering/validators/validate_eval_suite.py .local-artifacts/agent-evals/<suite-id> --suite-kind targeted_regression --require-run-results --min-runs 3
```

## Error Format

Hard validators use agent-repair-friendly messages:

- `VIOLATION`: what is broken
- `FIX`: the smallest acceptable repair path
