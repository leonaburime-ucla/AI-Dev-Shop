#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HOST_ARG=""
JSON_OUTPUT=""
MD_OUTPUT=""

usage() {
  cat <<'EOF'
Usage: resolve_subagent_mode.sh [--host <host>] [--json <path>] [--md <path>]

Resolves whether the current run should default to subagent-assisted execution
or single-agent mode based on the host capability probe.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host)
      HOST_ARG="$2"
      shift 2
      ;;
    --json)
      JSON_OUTPUT="$2"
      shift 2
      ;;
    --md)
      MD_OUTPUT="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

json_escape() {
  printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'
}

detect_host() {
  if [[ -n "${HOST_ARG:-}" ]]; then
    printf '%s' "$HOST_ARG"
    return 0
  fi

  if [[ -n "${AI_DEV_SHOP_HOST:-}" ]]; then
    printf '%s' "$AI_DEV_SHOP_HOST"
    return 0
  fi

  local found=()
  command -v codex >/dev/null 2>&1 && found+=("codex-cli")
  command -v claude >/dev/null 2>&1 && found+=("claude-code")
  command -v gemini >/dev/null 2>&1 && found+=("gemini-cli")

  if [[ "${#found[@]}" -eq 1 ]]; then
    printf '%s' "${found[0]}"
  else
    printf '%s' "generic-llm"
  fi
}

RESOLVED_HOST="$(detect_host)"
PROBE_OUTPUT="$(bash "$ROOT_DIR/harness-engineering/validators/probe_host_capabilities.sh")"
PROBE_LINE="$(printf '%s\n' "$PROBE_OUTPUT" | grep "^${RESOLVED_HOST} subagent_spawning:" || true)"

STATUS="unverified"
VERIFICATION_METHOD="manual"
EVIDENCE="no subagent capability entry found for host '$RESOLVED_HOST'"

if [[ -n "$PROBE_LINE" ]]; then
  STATUS="$(printf '%s\n' "$PROBE_LINE" | sed -E 's/^[^:]+: ([^ ]+) .*/\1/')"
  VERIFICATION_METHOD="$(printf '%s\n' "$PROBE_LINE" | sed -E 's/^.*\(([^;]+); .*$/\1/')"
  EVIDENCE="$(printf '%s\n' "$PROBE_LINE" | sed -E 's/^.*; (.*)\)$/\1/')"
fi

MODE="single-agent"
STARTUP_COPY=""

if [[ "$STATUS" == "enabled" ]]; then
  MODE="subagent-assisted"
  STARTUP_COPY='Sub-agent assistance is enabled on this host and defaults to automatic use for discovery, review, and safe parallel sidecar work. It usually spends more total tokens than keeping everything in one context; say "single-agent mode" or "disable subagents" if you want the cheaper sequential path.'
else
  STARTUP_COPY="Sub-agent assistance is $STATUS on this host, so the framework starts in sequential single-agent mode. Say \"re-enable subagents\" only after the host capability is verified."
fi

REPORT_TEXT=$'Subagent Mode Resolver\n----------------------\n'
REPORT_TEXT+="Host: $RESOLVED_HOST"$'\n'
REPORT_TEXT+="Capability: subagent_spawning"$'\n'
REPORT_TEXT+="Status: $STATUS"$'\n'
REPORT_TEXT+="Verification: $VERIFICATION_METHOD"$'\n'
REPORT_TEXT+="Recommended mode: $MODE"$'\n'
REPORT_TEXT+="Evidence: $EVIDENCE"$'\n'
REPORT_TEXT+="Startup copy: $STARTUP_COPY"$'\n'

if [[ -n "$MD_OUTPUT" ]]; then
  mkdir -p "$(dirname "$MD_OUTPUT")"
  cat > "$MD_OUTPUT" <<EOF
# Subagent Mode Resolution

- Host: \`$RESOLVED_HOST\`
- Capability: \`subagent_spawning\`
- Status: \`$STATUS\`
- Verification: \`$VERIFICATION_METHOD\`
- Recommended mode: \`$MODE\`
- Evidence: $EVIDENCE

$STARTUP_COPY
EOF
fi

if [[ -n "$JSON_OUTPUT" ]]; then
  mkdir -p "$(dirname "$JSON_OUTPUT")"
  cat > "$JSON_OUTPUT" <<EOF
{
  "host": "$(json_escape "$RESOLVED_HOST")",
  "capability": "subagent_spawning",
  "status": "$(json_escape "$STATUS")",
  "verification_method": "$(json_escape "$VERIFICATION_METHOD")",
  "recommended_mode": "$(json_escape "$MODE")",
  "evidence": "$(json_escape "$EVIDENCE")",
  "startup_copy": "$(json_escape "$STARTUP_COPY")"
}
EOF
fi

printf '%s' "$REPORT_TEXT"
