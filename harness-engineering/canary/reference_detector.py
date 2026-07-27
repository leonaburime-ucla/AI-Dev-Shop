#!/usr/bin/env python3
"""A dependency-graph detector, used as the subject of the ablation canary pilot.

This exists so the canary can be *run*, not merely specified. A host supplies its
own detector through the `dependency_graph` slot; that detector is what a real
promotion must put through this canary. This one stands in for it so the loop can
be proved end to end with nothing installed.

It is deliberately a real detector rather than a lookup table: it parses source,
builds an import graph, and finds cycles. That means it can be wrong in the way
the sensor doc warns about — an under-scoped entry point emits a valid, empty
finding list that is indistinguishable from an acyclic tree. Control 3 of the
canary exploits exactly that.

Stdlib only, by constraint: the simplification pass put installing packages out
of scope, and a canary that cannot run on the machine in front of you is the
problem it was written to solve.
"""

from __future__ import annotations

import ast
from pathlib import Path


def module_name(path: Path, root: Path) -> str:
    rel = path.relative_to(root).with_suffix("")
    return ".".join(rel.parts)


def collect_imports(path: Path) -> set[str]:
    """Top-level import targets, as written."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return set()

    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def build_graph(root: Path, scope: str = "**/*.py") -> dict[str, set[str]]:
    """Import graph over files matching `scope`.

    `scope` is the knob the canary ablates. Narrowing it models a real
    misconfiguration: an entry point that does not reach the changed modules.
    """
    files = sorted(root.glob(scope))
    known = {module_name(f, root): f for f in files}

    graph: dict[str, set[str]] = {name: set() for name in known}
    for name, path in known.items():
        for target in collect_imports(path):
            # Resolve to a module in this fixture, ignoring anything external.
            if target in known:
                graph[name].add(target)
            else:
                # `import infra.db` resolves to the package prefix too, so a
                # package-level import still registers an edge.
                for candidate in known:
                    if candidate == target or candidate.startswith(target + "."):
                        graph[name].add(candidate)
    return graph


def find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """Every elementary cycle, each reported once in a canonical rotation."""
    cycles: set[tuple[str, ...]] = set()
    stack: list[str] = []
    on_stack: set[str] = set()

    def walk(node: str) -> None:
        stack.append(node)
        on_stack.add(node)
        for nxt in sorted(graph.get(node, ())):
            if nxt not in on_stack:
                walk(nxt)
            else:
                cycle = stack[stack.index(nxt) :]
                # Canonical rotation so a cycle found from different entry
                # points is not counted twice.
                pivot = cycle.index(min(cycle))
                cycles.add(tuple(cycle[pivot:] + cycle[:pivot]))
        stack.pop()
        on_stack.discard(node)

    for node in sorted(graph):
        walk(node)
    return [list(c) for c in sorted(cycles)]


def find_direction_violations(
    graph: dict[str, set[str]], rules: list[dict]
) -> list[dict]:
    """Modules importing across a declared `dependency_direction` boundary."""
    violations = []
    for rule in rules:
        frm, to = rule["from_prefix"], rule["to_prefix"]
        for source, targets in sorted(graph.items()):
            if not source.startswith(frm):
                continue
            for target in sorted(targets):
                if target.startswith(to):
                    violations.append(
                        {"rule": rule["name"], "from": source, "to": target}
                    )
    return violations


def detect(
    root: Path,
    scope: str = "**/*.py",
    rules: list[dict] | None = None,
    max_cycle_length: int | None = None,
) -> dict:
    """Findings for one fixture.

    `max_cycle_length` is the longest cycle tolerated; cycles longer than it are
    findings. Omitted means every cycle is a finding, per the sensor's rule shape.
    """
    graph = build_graph(root, scope)
    cycles = find_cycles(graph)
    if max_cycle_length is not None:
        cycles = [c for c in cycles if len(c) > max_cycle_length]

    return {
        "modules_graphed": sorted(graph),
        "cycles": cycles,
        "direction_violations": find_direction_violations(graph, rules or []),
    }
