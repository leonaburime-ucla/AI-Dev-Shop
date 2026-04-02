#!/usr/bin/env python3
"""Run a small CLI compatibility matrix for Swarm Consensus peers."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import shutil
import socket
import subprocess
import sys
import time
from typing import List
import tomllib

END_MARKER = "<<SWARM_END>>"
DISCOVERY_CACHE_VERSION = 1
REPO_ROOT = Path(__file__).resolve().parents[3]
HOST_ROOT = REPO_ROOT.parent
REPO_WORKSPACE_ROOT = REPO_ROOT / "project-knowledge"


def resolve_workspace_root() -> Path:
    for key in ("ADS_PROJECT_KNOWLEDGE_ROOT", "ADS_WORKSPACE_ROOT"):
        raw = os.environ.get(key)
        if raw:
            return Path(raw).expanduser().resolve()
    sibling = HOST_ROOT / "ADS-project-knowledge"
    if sibling.exists():
        return sibling
    return REPO_WORKSPACE_ROOT


def display_path(path: Path) -> str:
    for base in (HOST_ROOT, REPO_ROOT):
        try:
            return path.relative_to(base).as_posix()
        except ValueError:
            continue
    return path.as_posix()


WORKSPACE_ROOT = resolve_workspace_root()
WORKSPACE_LABEL = display_path(WORKSPACE_ROOT)
DEFAULT_SMOKE_TEST_DIR = WORKSPACE_ROOT / ".local-artifacts" / "swarm-consensus" / "smoke-tests"
DEFAULT_DISCOVERY_CACHE_PATH = str(DEFAULT_SMOKE_TEST_DIR / "last-known-good.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke-test peer CLI flags and output modes for Swarm Consensus."
    )
    parser.add_argument(
        "--prompt",
        default=f"Reply with OK and then {END_MARKER} only.",
        help="Prompt to send to each CLI.",
    )
    parser.add_argument(
        "--case-timeout",
        type=int,
        default=75,
        help="Per-case timeout in seconds.",
    )
    parser.add_argument(
        "--claude-model",
        help="Explicit Claude model override for this test run.",
    )
    parser.add_argument(
        "--gemini-model",
        help="Explicit Gemini model override for this test run.",
    )
    parser.add_argument(
        "--codex-model",
        help="Explicit Codex model override for this test run.",
    )
    parser.add_argument(
        "--codex-cd",
        default=os.getcwd(),
        help="Directory passed to `codex exec --cd`. Use /tmp to isolate Codex from repo startup rules.",
    )
    parser.add_argument(
        "--save-artifact",
        action="store_true",
        help="Save the rendered report to a dated file.",
    )
    parser.add_argument(
        "--output-format",
        choices=("markdown", "json"),
        default="markdown",
        help="Report format for stdout.",
    )
    parser.add_argument(
        "--artifacts-dir",
        default=str(DEFAULT_SMOKE_TEST_DIR),
        help=f"Directory for dated smoke-test artifacts when --save-artifact is used. Override with {WORKSPACE_LABEL}/reports/swarm-consensus/smoke-tests if you want a retained repo artifact.",
    )
    parser.add_argument(
        "--discover-claude",
        action="store_true",
        help="Probe candidate Claude model names and return the first working exact model.",
    )
    parser.add_argument(
        "--claude-require",
        choices=("json", "both"),
        default="json",
        help="Success requirement for Claude discovery. Use 'both' when the workflow may need both JSON and plain-text transport.",
    )
    parser.add_argument(
        "--claude-candidate",
        action="append",
        default=[],
        help="Additional Claude model candidate to probe during discovery. Repeatable.",
    )
    parser.add_argument(
        "--discovery-cache-path",
        default=DEFAULT_DISCOVERY_CACHE_PATH,
        help="Path for the environment-keyed Claude discovery cache.",
    )
    parser.add_argument("--skip-claude", action="store_true")
    parser.add_argument("--skip-gemini", action="store_true")
    parser.add_argument("--skip-codex", action="store_true")
    return parser


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def is_jsonish(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    if stripped.startswith("{") or stripped.startswith("["):
        return True
    lines = [line for line in stripped.splitlines() if line.strip()]
    return bool(lines) and all(line.lstrip().startswith("{") for line in lines)


def ensure_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def load_json_file(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def load_saved_claude_model() -> str | None:
    payload = load_json_file(Path.home() / ".claude" / "settings.json")
    if not isinstance(payload, dict):
        return None
    model = payload.get("model")
    return str(model).strip() if model else None


def load_saved_gemini_model() -> str | None:
    payload = load_json_file(Path.home() / ".gemini" / "settings.json")
    if not isinstance(payload, dict):
        return None
    model_block = payload.get("model")
    if not isinstance(model_block, dict):
        return None
    model = model_block.get("name")
    return str(model).strip() if model else None


def load_saved_codex_config() -> dict[str, str]:
    path = Path.home() / ".codex" / "config.toml"
    try:
        with path.open("rb") as handle:
            payload = tomllib.load(handle)
    except (FileNotFoundError, OSError, tomllib.TOMLDecodeError):
        return {}

    result: dict[str, str] = {}
    model = payload.get("model")
    reasoning = payload.get("model_reasoning_effort")
    if model:
        result["model"] = str(model).strip()
    if reasoning:
        result["reasoning_effort"] = str(reasoning).strip()
    if result:
        result["config_path"] = str(path)
    return result


def extract_model_suggestion(text: str) -> str | None:
    match = re.search(r"Try --model to switch to ([^\s\"']+)", text)
    if not match:
        return None
    return match.group(1).strip().rstrip(".,)")


def normalize_model_hint(model: str | None) -> str | None:
    if not model:
        return None
    normalized = model.strip().lower()
    if not normalized:
        return None
    normalized = re.sub(r"^(?:[a-z0-9_.-]*\.)?(claude-)", r"\1", normalized)
    match = re.search(r"claude-(opus|sonnet|haiku)-(\d+(?:-\d+)?)", normalized)
    if match:
        return f"claude-{match.group(1)}-{match.group(2)}"
    if normalized in {"opus", "sonnet", "haiku"}:
        return f"claude-{normalized}"
    return normalized


def build_claude_environment(cli_versions: list[dict[str, str]], requirement: str) -> dict[str, str]:
    record = next((item for item in cli_versions if item["cli"] == "claude"), None)
    return {
        "cli": "claude",
        "cli_path": record["path"] if record else "not installed",
        "cli_version": record["version"] if record else "n/a",
        "hostname": socket.gethostname(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "transport_requirement": requirement,
    }


def build_environment_key(environment: dict[str, str]) -> str:
    return "|".join(
        [
            environment["cli"],
            environment["cli_version"],
            environment["hostname"],
            environment["system"],
            environment["release"],
            environment["machine"],
            environment["transport_requirement"],
        ]
    )


def load_discovery_cache(path: Path) -> dict:
    payload = load_json_file(path)
    if not isinstance(payload, dict):
        return {"version": DISCOVERY_CACHE_VERSION, "entries": []}
    entries = payload.get("entries")
    if not isinstance(entries, list):
        payload["entries"] = []
    payload.setdefault("version", DISCOVERY_CACHE_VERSION)
    return payload


def save_discovery_cache(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def resolve_cache_artifact_path(value: str | None) -> Path | None:
    if not value:
        return None
    candidate = Path(str(value))
    if candidate.is_absolute():
        return candidate
    if candidate.parts[:1] == (WORKSPACE_ROOT.name,):
        return (WORKSPACE_ROOT.parent / candidate).resolve()
    host_candidate = (HOST_ROOT / candidate).resolve()
    if host_candidate.exists():
        return host_candidate
    return (REPO_ROOT / candidate).resolve()


def find_cached_discovery(
    cache: dict,
    environment_key: str,
    requested_model: str | None,
    requested_hint: str | None,
) -> dict | None:
    entries = cache.get("entries", [])
    if not isinstance(entries, list):
        return None

    exact_match: dict | None = None
    hint_match: dict | None = None
    for entry in reversed(entries):
        if not isinstance(entry, dict):
            continue
        if entry.get("environment_key") != environment_key:
            continue
        artifact_path = resolve_cache_artifact_path(entry.get("artifact_path"))
        if not artifact_path or not artifact_path.exists():
            continue
        if requested_model and entry.get("requested_model") == requested_model:
            exact_match = entry
            break
        if requested_hint and entry.get("requested_model_hint") == requested_hint:
            hint_match = entry
    return exact_match or hint_match


def extract_response(case_name: str, stdout: str) -> str:
    stripped = stdout.strip()
    if not stripped:
        return ""

    try:
        if case_name == "claude_json":
            payload = json.loads(stripped)
            return str(payload.get("result", ""))
        if case_name == "gemini_json":
            payload = json.loads(stripped)
            return str(payload.get("response", ""))
        if case_name == "codex_json":
            messages: List[str] = []
            for line in stripped.splitlines():
                obj = json.loads(line)
                if obj.get("type") == "item.completed":
                    item = obj.get("item", {})
                    if item.get("type") == "agent_message":
                        messages.append(str(item.get("text", "")))
            return "\n".join(part for part in messages if part)
    except Exception:
        return stripped

    return stripped


def snippet(text: str, limit: int = 160) -> str:
    compact = text.replace("\n", "\\n")
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def resolve_model_plan(
    args: argparse.Namespace,
    discovery: dict[str, object] | None,
    cli_versions: list[dict[str, str]],
) -> dict[str, dict[str, object]]:
    installed = {record["cli"] for record in cli_versions if record["path"] != "not installed"}
    codex_config = load_saved_codex_config()
    plan: dict[str, dict[str, object]] = {}

    if "claude" in installed:
        saved_claude_model = load_saved_claude_model()
        claude_requested = args.claude_model
        claude_source = "unknown"
        claude_resolved = claude_requested or saved_claude_model
        claude_note = ""
        if claude_requested:
            claude_source = "per_run_override"
            claude_note = "explicit --claude-model"
        elif saved_claude_model:
            claude_source = "local_default"
            claude_note = "from ~/.claude/settings.json"
        if discovery and discovery.get("winner"):
            winner = discovery["winner"]
            if isinstance(winner, dict):
                claude_resolved = winner.get("model") or claude_resolved
                claude_source = str(winner.get("source") or "smoke_test_discovery")
                claude_note = f"discovery requirement={discovery.get('requirement', 'json')}"
        plan["claude"] = {
            "cli": "claude",
            "requested_model": claude_requested or "",
            "resolved_model": claude_resolved or "",
            "selection_source": claude_source,
            "command_model": claude_requested or saved_claude_model or "",
            "note": claude_note,
        }

    if "gemini" in installed:
        gemini_saved_model = load_saved_gemini_model()
        gemini_requested = args.gemini_model
        gemini_source = "unknown"
        gemini_resolved = gemini_requested or gemini_saved_model
        gemini_note = ""
        if gemini_requested:
            gemini_source = "per_run_override"
            gemini_note = "explicit --gemini-model"
        elif gemini_saved_model:
            gemini_source = "local_default"
            gemini_note = "from ~/.gemini/settings.json"
        plan["gemini"] = {
            "cli": "gemini",
            "requested_model": gemini_requested or "",
            "resolved_model": gemini_resolved or "",
            "selection_source": gemini_source,
            "command_model": gemini_resolved or "",
            "note": gemini_note,
        }

    if "codex" in installed:
        codex_requested = args.codex_model
        codex_saved_model = codex_config.get("model", "")
        codex_source = "unknown"
        codex_resolved = codex_requested or codex_saved_model
        codex_note = ""
        if codex_requested:
            codex_source = "per_run_override"
            codex_note = "explicit --codex-model"
        elif codex_saved_model:
            codex_source = "local_default"
            codex_note = f"from {codex_config.get('config_path', '~/.codex/config.toml')}"
        reasoning = codex_config.get("reasoning_effort")
        if reasoning:
            codex_note = f"{codex_note}; reasoning={reasoning}" if codex_note else f"reasoning={reasoning}"
        plan["codex"] = {
            "cli": "codex",
            "requested_model": codex_requested or "",
            "resolved_model": codex_resolved or "",
            "selection_source": codex_source,
            "command_model": codex_resolved or "",
            "note": codex_note,
        }

    return plan


def build_cases(
    args: argparse.Namespace,
    model_plan: dict[str, dict[str, object]],
) -> list[tuple[str, list[str]]]:
    prompt = args.prompt
    cases: list[tuple[str, list[str]]] = []

    if not args.skip_claude and command_exists("claude"):
        claude_base = ["claude"]
        claude_model = str(model_plan.get("claude", {}).get("command_model", "")).strip()
        if claude_model:
            claude_base += ["--model", claude_model]
        cases.append(("claude_text", claude_base + ["-p", prompt]))
        cases.append(
            ("claude_json", claude_base + ["-p", "--output-format", "json", prompt])
        )

    if not args.skip_gemini and command_exists("gemini"):
        gemini_base = ["gemini"]
        gemini_model = str(model_plan.get("gemini", {}).get("command_model", "")).strip()
        if gemini_model:
            gemini_base += ["-m", gemini_model]
        cases.append(("gemini_text", gemini_base + ["-p", prompt]))
        cases.append(("gemini_json", gemini_base + ["-o", "json", "-p", prompt]))

    if not args.skip_codex and command_exists("codex"):
        codex_base = ["codex", "exec", "--json"]
        codex_model = str(model_plan.get("codex", {}).get("command_model", "")).strip()
        if codex_model:
            codex_base += ["-m", codex_model]
        codex_base += ["--cd", args.codex_cd, "--skip-git-repo-check"]
        cases.append(("codex_json", codex_base + [prompt]))

    return cases


def probe_cli_versions() -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for cli in ("claude", "gemini", "codex"):
        path = shutil.which(cli)
        if not path:
            records.append({"cli": cli, "path": "not installed", "version": "n/a"})
            continue
        try:
            completed = subprocess.run(
                [cli, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            version_text = ensure_text(completed.stdout or completed.stderr).strip() or "unknown"
        except subprocess.TimeoutExpired:
            version_text = "timeout"
        records.append(
            {
                "cli": cli,
                "path": path,
                "version": snippet(version_text, limit=120),
            }
        )
    return records


def run_case(case_name: str, command: list[str], timeout_seconds: int) -> dict[str, object]:
    start = time.time()
    status = "ok"
    rc = 0
    stdout = ""
    stderr = ""

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        rc = completed.returncode
        stdout = ensure_text(completed.stdout)
        stderr = ensure_text(completed.stderr)
        if rc != 0:
            status = "failed"
    except FileNotFoundError as exc:
        status = "unavailable"
        rc = 127
        stderr = ensure_text(exc)
    except subprocess.TimeoutExpired as exc:
        status = "timeout"
        rc = -1
        stdout = ensure_text(exc.stdout)
        stderr = ensure_text(exc.stderr)

    duration = round(time.time() - start, 1)
    parsed = extract_response(case_name, stdout)

    return {
        "case": case_name,
        "status": status,
        "rc": rc,
        "duration_s": duration,
        "stdout_len": len(stdout),
        "stderr_len": len(stderr),
        "stdout_is_jsonish": is_jsonish(stdout),
        "parsed_has_end_marker": END_MARKER in parsed,
        "command": command,
        "parsed_snippet": snippet(parsed),
        "stdout_snippet": snippet(stdout),
        "stderr_snippet": snippet(stderr),
        "stdout_raw": stdout,
        "stderr_raw": stderr,
    }


def slim_case_result(result: dict[str, object]) -> dict[str, object]:
    return {
        "case": result["case"],
        "status": result["status"],
        "rc": result["rc"],
        "duration_s": result["duration_s"],
        "stdout_len": result["stdout_len"],
        "stderr_len": result["stderr_len"],
        "stdout_is_jsonish": result["stdout_is_jsonish"],
        "parsed_has_end_marker": result["parsed_has_end_marker"],
        "command": result["command"],
        "parsed_snippet": result["parsed_snippet"],
        "stdout_snippet": result["stdout_snippet"],
        "stderr_snippet": result["stderr_snippet"],
    }


def build_skipped_case_result(case_name: str) -> dict[str, object]:
    return {
        "case": case_name,
        "status": "skipped",
        "rc": 0,
        "duration_s": 0.0,
        "stdout_len": 0,
        "stderr_len": 0,
        "stdout_is_jsonish": False,
        "parsed_has_end_marker": False,
        "command": [],
        "parsed_snippet": "",
        "stdout_snippet": "",
        "stderr_snippet": "",
        "stdout_raw": "",
        "stderr_raw": "",
    }


def append_candidate(
    queue: list[str],
    sources: dict[str, str],
    seen: set[str],
    value: str | None,
    source: str,
) -> None:
    if not value:
        return
    normalized = value.strip()
    if not normalized or normalized in seen:
        return
    queue.append(normalized)
    sources[normalized] = source
    seen.add(normalized)


def run_claude_discovery_with_environment(
    args: argparse.Namespace,
    cli_versions: list[dict[str, str]],
) -> dict[str, object]:
    saved_model = load_saved_claude_model()
    requested_hint = normalize_model_hint(args.claude_model)
    cache_path = Path(args.discovery_cache_path)
    cache = load_discovery_cache(cache_path)
    environment = build_claude_environment(cli_versions, args.claude_require)
    environment_key = build_environment_key(environment)
    cache_entry = find_cached_discovery(cache, environment_key, args.claude_model, requested_hint)
    if cache_entry:
        winner_model = cache_entry.get("winner_model")
        return {
            "enabled": True,
            "requirement": args.claude_require,
            "saved_claude_model": saved_model,
            "requested_claude_model": args.claude_model,
            "requested_model_hint": requested_hint,
            "candidate_order": [],
            "winner": {
                "model": winner_model,
                "source": "discovery_cache",
                "json_ok": cache_entry.get("json_ok", False),
                "text_ok": cache_entry.get("text_ok", False),
                "requirement": args.claude_require,
            },
            "attempts": [],
            "cache_hit": True,
            "cache_entry": cache_entry,
            "cache_path": str(cache_path),
            "environment": environment,
            "environment_key": environment_key,
        }

    queue: list[str] = []
    sources: dict[str, str] = {}
    seen: set[str] = set()

    for candidate in args.claude_candidate:
        append_candidate(queue, sources, seen, candidate, "manual_candidate")
    append_candidate(queue, sources, seen, args.claude_model, "requested_model")
    append_candidate(queue, sources, seen, saved_model, "saved_claude_settings")
    append_candidate(queue, sources, seen, "opus", "alias_probe")

    attempts: list[dict[str, object]] = []
    winner: dict[str, object] | None = None

    idx = 0
    while idx < len(queue):
        candidate = queue[idx]
        idx += 1

        json_result = run_case(
            "claude_json",
            ["claude", "--model", candidate, "-p", "--output-format", "json", args.prompt],
            args.case_timeout,
        )
        if args.claude_require == "both":
            text_result = run_case(
                "claude_text",
                ["claude", "--model", candidate, "-p", args.prompt],
                args.case_timeout,
            )
        else:
            text_result = build_skipped_case_result("claude_text")

        suggestions: list[str] = []
        raw_streams = [
            ensure_text(json_result["stdout_raw"]),
            ensure_text(json_result["stderr_raw"]),
        ]
        if args.claude_require == "both":
            raw_streams.extend(
                [
                    ensure_text(text_result["stdout_raw"]),
                    ensure_text(text_result["stderr_raw"]),
                ]
            )
        for raw in raw_streams:
            suggestion = extract_model_suggestion(raw)
            if suggestion and suggestion not in suggestions:
                suggestions.append(suggestion)
                append_candidate(queue, sources, seen, suggestion, f"suggested_by:{candidate}")

        json_ok = bool(
            json_result["status"] == "ok" and json_result["parsed_has_end_marker"]
        )
        text_ok = bool(
            text_result["status"] == "ok" and text_result["parsed_has_end_marker"]
        )
        success = json_ok if args.claude_require == "json" else json_ok and text_ok

        attempt = {
            "candidate": candidate,
            "candidate_source": sources.get(candidate, "unknown"),
            "success": success,
            "requirement": args.claude_require,
            "json_ok": json_ok,
            "text_ok": text_ok,
            "suggested_models": suggestions,
            "json_case": slim_case_result(json_result),
            "text_case": slim_case_result(text_result),
        }
        attempts.append(attempt)

        if success:
            winner = {
                "model": candidate,
                "source": sources.get(candidate, "unknown"),
                "json_ok": json_ok,
                "text_ok": text_ok,
                "requirement": args.claude_require,
            }
            break

    return {
        "enabled": True,
        "requirement": args.claude_require,
        "saved_claude_model": saved_model,
        "requested_claude_model": args.claude_model,
        "requested_model_hint": requested_hint,
        "candidate_order": queue,
        "winner": winner,
        "attempts": attempts,
        "cache_hit": False,
        "cache_entry": None,
        "cache_path": str(cache_path),
        "environment": environment,
        "environment_key": environment_key,
    }


def render_report(
    results: list[dict[str, object]],
    args: argparse.Namespace,
    cli_versions: list[dict[str, str]],
    discovery: dict[str, object] | None,
    model_plan: dict[str, dict[str, object]],
) -> str:
    lines = [
        "# Swarm Consensus CLI Smoke Test",
        "",
        f"- Generated at: `{datetime.now(timezone.utc).isoformat()}`",
        f"- Host: `{socket.gethostname()}`",
        f"- Working directory: `{os.getcwd()}`",
        f"- Prompt: `{args.prompt}`",
        f"- Case timeout: `{args.case_timeout}s`",
        f"- Codex --cd: `{args.codex_cd}`",
        "",
        "## CLI Versions",
        "",
        "| CLI | Path | Version |",
        "|---|---|---|",
    ]
    for record in cli_versions:
        lines.append(f"| `{record['cli']}` | `{record['path']}` | `{record['version']}` |")

    if model_plan:
        lines += [
            "",
            "## Model Resolution",
            "",
            "| CLI | Requested | Resolved | Selection Source | Note |",
            "|---|---|---|---|---|",
        ]
        for cli in ("claude", "gemini", "codex"):
            item = model_plan.get(cli)
            if not item:
                continue
            lines.append(
                f"| `{cli}` | `{item.get('requested_model') or 'n/a'}` | "
                f"`{item.get('resolved_model') or 'unknown'}` | "
                f"`{item.get('selection_source') or 'unknown'}` | "
                f"`{item.get('note') or 'n/a'}` |"
            )

    lines += [
        "",
        "| Case | Status | RC | Dur (s) | JSON-ish stdout | Parsed end marker | stdout | stderr |",
        "|---|---|---|---:|---|---|---:|---:|",
    ]
    for result in results:
        lines.append(
            f"| `{result['case']}` | `{result['status']}` | `{result['rc']}` | "
            f"{result['duration_s']} | `{result['stdout_is_jsonish']}` | "
            f"`{result['parsed_has_end_marker']}` | {result['stdout_len']} | {result['stderr_len']} |"
        )

    lines.append("")

    if discovery:
        winner = discovery.get("winner")
        lines += [
            "## Claude Discovery",
            "",
            f"- Requirement: `{discovery['requirement']}`",
            f"- Saved Claude model: `{discovery['saved_claude_model'] or 'none'}`",
            f"- Requested Claude model: `{discovery['requested_claude_model'] or 'none'}`",
            f"- Cache hit: `{discovery.get('cache_hit', False)}`",
            f"- Cache path: `{discovery.get('cache_path', 'n/a')}`",
            f"- Winning model: `{winner['model'] if winner else 'none'}`",
            f"- Winning source: `{winner['source'] if winner else 'n/a'}`",
            "",
            "| Candidate | Source | Success | JSON OK | Text OK | Suggested Models |",
            "|---|---|---|---|---|---|",
        ]
        if discovery["attempts"]:
            for attempt in discovery["attempts"]:
                suggested = ", ".join(attempt["suggested_models"]) if attempt["suggested_models"] else "none"
                lines.append(
                    f"| `{attempt['candidate']}` | `{attempt['candidate_source']}` | "
                    f"`{attempt['success']}` | `{attempt['json_ok']}` | `{attempt['text_ok']}` | `{suggested}` |"
                )
        else:
            lines.append("| `n/a` | `cache_hit` | `True` | `n/a` | `n/a` | `none` |")
        lines.append("")

    for result in results:
        lines.append(f"## {result['case']}")
        lines.append(f"- Command: `{ ' '.join(result['command']) }`")
        lines.append(f"- Parsed snippet: `{result['parsed_snippet']}`")
        lines.append(f"- stdout snippet: `{result['stdout_snippet']}`")
        if result["stderr_len"]:
            lines.append(f"- stderr snippet: `{result['stderr_snippet']}`")
        lines.append("")

    return "\n".join(lines)


def render_json_report(
    results: list[dict[str, object]],
    args: argparse.Namespace,
    cli_versions: list[dict[str, str]],
    discovery: dict[str, object] | None,
    model_plan: dict[str, dict[str, object]],
) -> str:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "host": socket.gethostname(),
        "working_directory": os.getcwd(),
        "prompt": args.prompt,
        "case_timeout_seconds": args.case_timeout,
        "codex_cd": args.codex_cd,
        "cli_versions": cli_versions,
        "model_resolution": model_plan,
        "results": [slim_case_result(result) for result in results],
        "discovery": discovery,
    }
    return json.dumps(payload, indent=2)


def save_report(report: str, artifacts_dir: str, suffix: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    path = Path(artifacts_dir)
    path.mkdir(parents=True, exist_ok=True)
    target = path / f"{stamp}-cli-smoke-test{suffix}"
    target.write_text(report + "\n", encoding="utf-8")
    return target


def persist_claude_discovery(
    discovery: dict[str, object],
    cli_versions: list[dict[str, str]],
    args: argparse.Namespace,
    model_plan: dict[str, dict[str, object]],
) -> dict[str, str] | None:
    if not discovery or not discovery.get("enabled"):
        return None
    if discovery.get("cache_hit"):
        cache_entry = discovery.get("cache_entry")
        if isinstance(cache_entry, dict):
            resolved_artifact_path = resolve_cache_artifact_path(cache_entry.get("artifact_path"))
            cache_path = Path(str(discovery.get("cache_path", args.discovery_cache_path)))
            if resolved_artifact_path and cache_path.exists():
                cache = load_discovery_cache(cache_path)
                changed = False
                for entry in cache.get("entries", []):
                    if not isinstance(entry, dict):
                        continue
                    if (
                        entry.get("environment_key") == cache_entry.get("environment_key")
                        and entry.get("requested_model") == cache_entry.get("requested_model")
                        and entry.get("artifact_path") != str(resolved_artifact_path)
                    ):
                        entry["artifact_path"] = str(resolved_artifact_path)
                        changed = True
                if changed:
                    cache["updated_at"] = datetime.now(timezone.utc).isoformat()
                    save_discovery_cache(cache_path, cache)
            return {
                "artifact_path": str(resolved_artifact_path or ""),
                "cache_path": str(discovery.get("cache_path", "")),
            }
        return {"artifact_path": "", "cache_path": str(discovery.get("cache_path", ""))}

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    artifacts_dir = Path(args.artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifacts_dir / f"{timestamp}-claude-discovery.md"

    markdown_report = render_report([], args, cli_versions, discovery, model_plan)
    artifact_path.write_text(markdown_report + "\n", encoding="utf-8")

    cache_path = Path(str(discovery.get("cache_path", args.discovery_cache_path)))
    cache = load_discovery_cache(cache_path)
    environment = discovery.get("environment", {})
    environment_key = str(discovery.get("environment_key", ""))
    winner = discovery.get("winner")
    if isinstance(winner, dict) and winner.get("model"):
        new_entry = {
            "validated_at": datetime.now(timezone.utc).isoformat(),
            "environment_key": environment_key,
            "environment": environment,
            "requested_model": discovery.get("requested_claude_model"),
            "requested_model_hint": discovery.get("requested_model_hint"),
            "winner_model": winner.get("model"),
            "winner_source": "smoke_test_discovery",
            "json_ok": winner.get("json_ok"),
            "text_ok": winner.get("text_ok"),
            "artifact_path": str(artifact_path.resolve()),
        }
        entries = [
            entry
            for entry in cache.get("entries", [])
            if not (
                isinstance(entry, dict)
                and entry.get("environment_key") == environment_key
                and entry.get("requested_model") == discovery.get("requested_claude_model")
            )
        ]
        entries.append(new_entry)
        cache["entries"] = entries
        cache["updated_at"] = datetime.now(timezone.utc).isoformat()
        save_discovery_cache(cache_path, cache)

    return {
        "artifact_path": str(artifact_path),
        "cache_path": str(cache_path),
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    discovery: dict[str, object] | None = None

    cli_versions = probe_cli_versions()
    if args.discover_claude:
        discovery = run_claude_discovery_with_environment(args, cli_versions)
    model_plan = resolve_model_plan(args, discovery, cli_versions)
    if args.discover_claude:
        persistence = persist_claude_discovery(discovery, cli_versions, args, model_plan)
        if persistence:
            discovery["persistence"] = persistence
    cases = build_cases(args, model_plan)
    if args.discover_claude:
        cases = [case for case in cases if not case[0].startswith("claude_")]

    if not cases and not args.discover_claude:
        print("No runnable cases found. Install at least one of: claude, gemini, codex.", file=sys.stderr)
        return 1

    results = [run_case(name, command, args.case_timeout) for name, command in cases]
    if args.output_format == "json":
        report = render_json_report(results, args, cli_versions, discovery, model_plan)
        suffix = ".json"
    else:
        report = render_report(results, args, cli_versions, discovery, model_plan)
        suffix = ".md"
    print(report)

    if args.save_artifact:
        target = save_report(report, args.artifacts_dir, suffix)
        print(f"Saved artifact: {target}")

    if discovery and discovery.get("winner"):
        return 0
    if any(result["parsed_has_end_marker"] for result in results):
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
