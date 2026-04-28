#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def discover_eval_dirs(suite_dir: Path) -> list[Path]:
    return sorted(
        child
        for child in suite_dir.iterdir()
        if child.is_dir() and (child / "seed-state").is_dir()
    )


def copy_optional(src: Path, dest: Path) -> None:
    if src.is_dir():
        shutil.copytree(src, dest)
    elif src.is_file():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)


def prepare_run(eval_dir: Path, run_id: str, force: bool) -> Path:
    seed_state = eval_dir / "seed-state"
    run_dir = eval_dir / "runs" / run_id

    if run_dir.exists():
        if not force:
            raise FileExistsError(f"Run directory already exists: {run_dir}")
        shutil.rmtree(run_dir)

    shutil.copytree(seed_state, run_dir)

    copy_optional(eval_dir / "project-brief.md", run_dir / "project-brief.md")
    copy_optional(eval_dir / "prompts", run_dir / "prompts")
    (run_dir / "eval-results").mkdir(parents=True, exist_ok=True)

    return run_dir


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare fresh run workdirs for a seeded eval suite.",
    )
    parser.add_argument("suite_dir", help="Path to the suite root")
    parser.add_argument("run_id", help="Run identifier, for example run-001")
    parser.add_argument(
        "--eval",
        dest="eval_names",
        action="append",
        default=[],
        help="Specific eval directory name to prepare. Repeatable.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing runs/<run_id>/ directories if they already exist.",
    )
    args = parser.parse_args()

    suite_dir = Path(args.suite_dir).resolve()
    if not suite_dir.exists():
        print(f"Suite directory does not exist: {suite_dir}", file=sys.stderr)
        return 1

    eval_dirs = discover_eval_dirs(suite_dir)
    if args.eval_names:
        wanted = set(args.eval_names)
        eval_dirs = [item for item in eval_dirs if item.name in wanted]
        missing = wanted.difference({item.name for item in eval_dirs})
        if missing:
            print(
                f"Unknown eval name(s): {', '.join(sorted(missing))}",
                file=sys.stderr,
            )
            return 1

    if not eval_dirs:
        print(f"No eval directories with seed-state found under {suite_dir}", file=sys.stderr)
        return 1

    for eval_dir in eval_dirs:
        run_dir = prepare_run(eval_dir, args.run_id, args.force)
        print(f"{eval_dir.name}\t{run_dir}")

    print(
        "NEXT STEP: default execution mode for seeded agent evals is "
        "'repo_persona_subagent'. Use 'repo_persona_host' only when subagents "
        "are unavailable or disabled. Use external peers only for explicit "
        "comparison runs.",
        file=sys.stderr,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
