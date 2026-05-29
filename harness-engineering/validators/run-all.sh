#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "==> Harness hard checks"
python3 "$ROOT_DIR/harness-engineering/validators/validate_eval_suite_regressions.py"
python3 "$ROOT_DIR/harness-engineering/validators/validate_contracts.py"
python3 "$ROOT_DIR/harness-engineering/validators/validate_path_references.py"
python3 "$ROOT_DIR/harness-engineering/validators/validate_registry_integrity.py"
python3 "$ROOT_DIR/harness-engineering/validators/validate_evaluator_artifacts.py"
python3 "$ROOT_DIR/harness-engineering/validators/validate_load_bearing_audits.py"
python3 "$ROOT_DIR/harness-engineering/validators/validate_debate_routing_guard.py"
python3 "$ROOT_DIR/harness-engineering/validators/validate_swarm_model_identity_guard.py"
python3 "$ROOT_DIR/harness-engineering/validators/validate_specs_as_built_freshness.py"

echo
echo "==> Harness advisory audit"
python3 "$ROOT_DIR/harness-engineering/validators/doc_garden_audit.py"
python3 "$ROOT_DIR/harness-engineering/validators/doc_staleness_audit.py"
bash "$ROOT_DIR/harness-engineering/validators/probe_host_capabilities.sh"
