#!/usr/bin/env python3
"""Run a small CLI compatibility matrix for Swarm Consensus peers."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from typing import List

END_MARKER = "<<SWARM_END>>"


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
        help="Save the markdown report to a dated file.",
    )
    parser.add_argument(
        "--artifacts-dir",
        default=".local-artifacts/swarm-consensus/smoke-tests",
        help="Directory for dated smoke-test artifacts when --save-artifact is used. Override with framework/reports/swarm-consensus/smoke-tests if you want a retained repo artifact.",
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


def build_cases(args: argparse.Namespace) -> list[tuple[str, list[str]]]:
    prompt = args.prompt
    cases: list[tuple[str, list[str]]] = []

    if not args.skip_claude and command_exists("claude"):
        claude_base = ["claude"]
        if args.claude_model:
            claude_base += ["--model", args.claude_model]
        cases.append(("claude_text", claude_base + ["-p", prompt]))
        cases.append(
            ("claude_json", claude_base + ["-p", "--output-format", "json", prompt])
        )

    if not args.skip_gemini and command_exists("gemini"):
        gemini_base = ["gemini"]
        if args.gemini_model:
            gemini_base += ["-m", args.gemini_model]
        cases.append(("gemini_text", gemini_base + ["-p", prompt]))
        cases.append(("gemini_json", gemini_base + ["-o", "json", "-p", prompt]))

    if not args.skip_codex and command_exists("codex"):
        codex_base = ["codex", "exec", "--json"]
        if args.codex_model:
            codex_base += ["-m", args.codex_model]
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
    }


def render_report(
    results: list[dict[str, object]],
    args: argparse.Namespace,
    cli_versions: list[dict[str, str]],
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
    for result in results:
        lines.append(f"## {result['case']}")
        lines.append(f"- Command: `{ ' '.join(result['command']) }`")
        lines.append(f"- Parsed snippet: `{result['parsed_snippet']}`")
        lines.append(f"- stdout snippet: `{result['stdout_snippet']}`")
        if result["stderr_len"]:
            lines.append(f"- stderr snippet: `{result['stderr_snippet']}`")
        lines.append("")

    return "\n".join(lines)


def save_report(report: str, artifacts_dir: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    path = Path(artifacts_dir)
    path.mkdir(parents=True, exist_ok=True)
    target = path / f"{stamp}-cli-smoke-test.md"
    target.write_text(report + "\n", encoding="ascii")
    return target


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    cases = build_cases(args)

    if not cases:
        print("No runnable cases found. Install at least one of: claude, gemini, codex.", file=sys.stderr)
        return 1

    cli_versions = probe_cli_versions()
    results = [run_case(name, command, args.case_timeout) for name, command in cases]
    report = render_report(results, args, cli_versions)
    print(report)

    if args.save_artifact:
        target = save_report(report, args.artifacts_dir)
        print(f"Saved artifact: {target}")

    if any(result["parsed_has_end_marker"] for result in results):
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
