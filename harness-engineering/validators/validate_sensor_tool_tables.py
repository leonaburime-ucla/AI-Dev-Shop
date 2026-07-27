#!/usr/bin/env python3
"""Keep per-stack tool tables out of the sensor docs.

A sensor declares a **capability** — what a command must emit, and that the
sensor is `inactive` when nothing can. It does not name a tool per language with
a reference command, because those claims cannot be checked from this repository
and have been wrong every time anyone checked them upstream: a PyPI package that
does not exist, a wrong clippy default, a linter blind to `with`, a non-existent
`revive` flag, a formatter that emits no symbol name.

The rule already existed. Nothing enforced it, so it silently reverted: a pass
recorded per-stack tables as deleted, a later handoff listed "no per-stack tool
names appear anywhere" as an invariant to preserve, and 32 such rows were sitting
in 7 of 11 sensor docs the whole time. That is what an unchecked doctrine is
worth.

Not banned, deliberately:

- Naming a tool to **warn against it** ("it is not valid to declare X alone for
  branch coverage"). A warning is protective; a recommendation is the defect.
- File and report **formats** (lcov, Cobertura, JaCoCo). Those are readable specs,
  verifiable, and the sensors depend on their field names.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
SENSORS = ROOT / "harness-engineering" / "sensors"

# A table row whose first cell is a language or stack name. That shape is the
# per-stack tool table; a capability table keys on the requirement instead.
STACK_ROW = re.compile(
    r"^\|\s*\**\s*"
    r"(TypeScript|JavaScript|TypeScript\s*/\s*JavaScript|JS\s*/\s*TS|Python|Go|Golang|"
    r"Java|Kotlin|Java\s*/\s*Kotlin|Rust|C#|Ruby|PHP|Swift|Scala|Node(\.js)?|Generic)"
    r"\b[^|]*\|",
    re.IGNORECASE,
)


def main() -> int:
    violations: list[str] = []

    if not SENSORS.is_dir():
        print(f"VIOLATION: missing sensor directory {SENSORS.relative_to(ROOT)}")
        return 1

    for path in sorted(SENSORS.glob("*.md")):
        rel = path.relative_to(ROOT).as_posix()
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            violations.append(f"VIOLATION: {rel} could not be read as UTF-8.")
            continue

        for number, line in enumerate(lines, start=1):
            if STACK_ROW.match(line.strip()):
                violations.append(
                    f"VIOLATION: {rel}:{number} is a per-stack tool table row.\n"
                    f"  {line.strip()[:110]}\n"
                    f"FIX: State the capability instead — what the declared command must emit, "
                    f"and that the sensor is `inactive` when none can. Per-stack tool names, "
                    f"versions, flags and defaults cannot be verified from this repository, and "
                    f"every one that was checked upstream turned out to be wrong."
                )

    if violations:
        print("\n\n".join(violations))
        return 1

    count = len(list(SENSORS.glob("*.md")))
    print(f"PASS: no per-stack tool tables in {count} sensor doc(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
