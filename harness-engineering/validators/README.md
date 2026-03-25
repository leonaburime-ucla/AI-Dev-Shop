# Harness Validators

These validators are the first mechanical enforcement layer for this repo.

## Hard Validators

- `validate_path_references.py`
  - checks that repo-local markdown path references point to real files or directories
- `validate_registry_integrity.py`
  - checks that `skills-registry.md` entries point to real files
  - fails when canonical skill files exist on disk but are not registered
  - allows explicit exclusions only through `project-knowledge/routing/skills-registry-exceptions.md`
- `validate_evaluator_artifacts.py`
  - checks retained evaluator contracts and evaluator reports for required fields and sections
  - fails when a `progress-ledger.md` marks `evaluator_mode: required` but no retained evaluator contract is recorded
- `validate_load_bearing_audits.py`
  - checks retained `framework/reports/maintenance/harness-load-bearing-*.md` reports for required sections and decision labels

## Advisory Audit

- `doc_garden_audit.py`
  - reports repo-health signals that maintainers should review regularly
  - does not fail the run by itself
- `doc_staleness_audit.py`
  - checks a narrow watchlist of high-risk docs against concrete source-of-truth targets and review cadence
  - advisory only; intended to catch silent routing/workflow drift early
- `generate_maintenance_report.py`
  - refreshes `framework/reports/maintenance/harness-maintenance.md` from current repo state
  - intended for scheduled maintenance workflows and manual maintainer passes
- `probe_host_capabilities.sh`
  - checks version-sensitive host capabilities against the local environment when a reliable probe exists
  - prints `enabled`, `unavailable`, or `unverified` instead of relying on stale memory or docs alone
- `resolve_subagent_mode.sh`
  - resolves whether the current run should default to `subagent-assisted` or `single-agent` mode
  - emits startup-friendly copy that includes the token-cost tradeoff and user toggles

## Run Everything

```bash
bash harness-engineering/validators/run-all.sh
```

## Probe Current Host Capabilities

```bash
bash harness-engineering/validators/probe_host_capabilities.sh
```

Resolve startup mode for the current host:

```bash
bash harness-engineering/validators/resolve_subagent_mode.sh --host <detected-host>
```

## Error Format

Hard validators use agent-repair-friendly messages:

- `VIOLATION`: what is broken
- `FIX`: the smallest acceptable repair path
