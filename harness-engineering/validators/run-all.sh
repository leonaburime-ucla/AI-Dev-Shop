#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "==> Harness hard checks"
python3 "$ROOT_DIR/harness-engineering/validators/validate_path_references.py"
python3 "$ROOT_DIR/harness-engineering/validators/validate_registry_integrity.py"

echo
echo "==> Harness advisory audit"
python3 "$ROOT_DIR/harness-engineering/validators/doc_garden_audit.py"
python3 "$ROOT_DIR/harness-engineering/validators/doc_staleness_audit.py"
bash "$ROOT_DIR/harness-engineering/validators/probe_host_capabilities.sh"
