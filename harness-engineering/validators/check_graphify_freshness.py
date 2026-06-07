#!/usr/bin/env python3
"""Write or check AI Dev Shop freshness metadata for Graphify outputs."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "graphify-out",
    "node_modules",
    "vendor",
    "dist",
    "build",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "ADS-project-knowledge",
}

SKIP_PATH_PREFIXES = {
    ("integrations", "graphify", "upstream"),
}

REPO_ROOT = Path(__file__).resolve().parents[2]


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def run_git(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def graphify_version() -> str | None:
    candidates: list[str] = []
    env_bin = os.environ.get("GRAPHIFY_BIN")
    if env_bin:
        candidates.append(env_bin)
    candidates.append("graphify")
    candidates.append(str(REPO_ROOT / "integrations" / "graphify" / ".venv" / "bin" / "graphify"))
    seen: set[str] = set()
    unique_candidates = []
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        unique_candidates.append(candidate)
    for candidate in unique_candidates:
        version = graphify_version_for(candidate)
        if version:
            return version
    return None


def graphify_version_for(command: str) -> str | None:
    try:
        result = subprocess.run(
            [command, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def newest_source_mtime(root: Path) -> str | None:
    newest = 0.0
    for dirpath, dirnames, filenames in os.walk(root):
        current_dir = Path(dirpath)
        rel_parts = current_dir.relative_to(root).parts
        if any(rel_parts[: len(prefix)] == prefix for prefix in SKIP_PATH_PREFIXES):
            dirnames.clear()
            continue
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS]
        for name in filenames:
            path = current_dir / name
            try:
                newest = max(newest, path.stat().st_mtime)
            except OSError:
                continue
    if newest <= 0:
        return None
    return datetime.fromtimestamp(newest, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_status(root: Path, args: argparse.Namespace) -> dict:
    graph_out = root / "graphify-out"
    graph_json = graph_out / "graph.json"
    git_head = run_git(root, "rev-parse", "HEAD")
    git_dirty = run_git(root, "status", "--porcelain")
    now = iso_now()
    return {
        "generated_at": now,
        "target_root": str(root),
        "target_git_head": git_head,
        "target_dirty": bool(git_dirty),
        "latest_source_mtime": newest_source_mtime(root),
        "graph_json_mtime": (
            datetime.fromtimestamp(graph_json.stat().st_mtime, timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
            if graph_json.exists()
            else None
        ),
        "graphify_version": graphify_version(),
        "mode": args.mode,
        "semantic_enabled": args.semantic_enabled,
        "human_approved_semantic": args.human_approved_semantic,
    }


def load_status(status_path: Path) -> dict | None:
    try:
        return json.loads(status_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def freshness(root: Path, status: dict | None, semantic_required: bool) -> tuple[str, str]:
    graph_json = root / "graphify-out" / "graph.json"
    if not graph_json.exists():
        return "missing", "graphify-out/graph.json is missing"
    if not status:
        return "stale", ".ads-graphify-status.json is missing or unreadable"

    current_head = run_git(root, "rev-parse", "HEAD")
    recorded_head = status.get("target_git_head")
    if current_head and recorded_head and current_head != recorded_head:
        return "stale", "target git HEAD differs from recorded graph HEAD"

    graph_mtime = datetime.fromtimestamp(graph_json.stat().st_mtime, timezone.utc)
    latest_source = parse_iso(newest_source_mtime(root))
    if latest_source and latest_source > graph_mtime:
        return "stale", "source files are newer than graphify-out/graph.json"

    if semantic_required and not status.get("semantic_enabled"):
        return "stale", "semantic graph coverage is required but metadata says semantic_enabled=false"

    return "fresh", "graph metadata matches current freshness checks"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", nargs="?", default=".", help="target repo root")
    parser.add_argument("--write", action="store_true", help="write/update .ads-graphify-status.json")
    parser.add_argument("--strict", action="store_true", help="exit non-zero when stale or missing")
    parser.add_argument("--semantic-required", action="store_true", help="treat semantic coverage as required")
    parser.add_argument("--semantic-enabled", action="store_true", help="record semantic_enabled=true when writing")
    parser.add_argument(
        "--human-approved-semantic",
        action="store_true",
        help="record human_approved_semantic=true when writing",
    )
    parser.add_argument("--mode", default="code_update", help="mode to record when writing")
    args = parser.parse_args()

    root = Path(args.target).expanduser().resolve()
    if not root.exists():
        print(f"error: target does not exist: {root}", file=sys.stderr)
        return 2

    status_path = root / "graphify-out" / ".ads-graphify-status.json"
    if args.write:
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status = build_status(root, args)
        status_path.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    else:
        status = load_status(status_path)

    state, reason = freshness(root, status, args.semantic_required)
    print("Graphify Freshness Check")
    print("------------------------")
    print(f"Target: {root}")
    print(f"Status: {state}")
    print(f"Reason: {reason}")
    print(f"Metadata: {status_path}")
    if status:
        print(f"Generated: {status.get('generated_at')}")
        print(f"Mode: {status.get('mode')}")
        print(f"Semantic enabled: {status.get('semantic_enabled')}")

    if args.strict and state != "fresh":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
