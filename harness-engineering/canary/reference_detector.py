#!/usr/bin/env python3
"""A dependency-graph detector, used as the subject of the ablation canary pilot.

A host supplies its own detector through the `dependency_graph` slot; that
detector is what a real promotion must put through the canary. This one stands in
so the loop can be proved end to end with nothing installed.

It parses source, builds an import graph, and finds cycles — deliberately a real
detector, so it can fail the way real ones do.

Stdlib only: the simplification pass put installing packages out of scope, and a
validation loop that cannot run on the machine in front of you is the problem
this program exists to solve.

Corrections after adversarial review (2026-07-27):

- Relative imports were silently dropped. `from . import b` carries
  `node.module is None`, and `from .a import x` yields a bare `"a"` that never
  resolved against a package-qualified module map. Intra-package imports are
  where cycles actually live, so the detector was blind to the common case.
- Cycle finding re-entered from every node with no memo, enumerating every simple
  path. It was exponential on *acyclic* input — 35 modules took 31s — and
  recursion died at depth 998. Now: iterative Tarjan for strongly connected
  components, then elementary-cycle enumeration only inside non-trivial ones. An
  acyclic graph does no enumeration at all.
- Direction rules prefix-matched without a path boundary, so a rule naming
  `domain` also fired on `domain_utils`.
"""

from __future__ import annotations

import ast
from pathlib import Path

# Enumerating elementary cycles inside one strongly connected component is
# inherently exponential. Past this many, report the component instead of its
# cycles and mark the result inconclusive rather than hanging.
MAX_CYCLES_PER_COMPONENT = 500


def module_name(path: Path, root: Path) -> str:
    rel = path.relative_to(root).with_suffix("")
    return ".".join(rel.parts)


def resolve_relative(current: str, module: str | None, level: int) -> str | None:
    """Resolve `from ..pkg import x` against the importing module's package."""
    parts = current.split(".")
    # level 1 is the current package: drop the module's own name.
    base = parts[: len(parts) - level]
    if len(parts) - level < 0:
        return None
    return ".".join(base + ([module] if module else []))


def collect_imports(path: Path, current: str) -> set[str]:
    """Import targets, with relative imports resolved against `current`."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return set()

    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                resolved = resolve_relative(current, node.module, node.level)
                if resolved is None:
                    continue
                if node.module:
                    names.add(resolved)
                else:
                    # `from . import b` names the target in the alias list, not the
                    # module slot. Adding the bare package instead would expand to
                    # every sibling — including the importing module, inventing a
                    # self-loop that is not in the source.
                    for alias in node.names:
                        names.add(f"{resolved}.{alias.name}" if resolved else alias.name)
            elif node.module:
                # `from pkg import b` names its target in the alias list. Recording
                # the bare package and expanding it to every member fabricated edges
                # between siblings, which reported a 2-cycle for plain `a -> b -> c`.
                # Same shape as the relative-import bug above; only that branch had
                # been fixed. Record the module itself too, for `from pkg.mod import f`.
                names.add(node.module)
                for alias in node.names:
                    names.add(f"{node.module}.{alias.name}")
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
        for target in collect_imports(path, name):
            # Exact resolution only. Every `from X import y` form is now resolved to
            # `X.y` when the imports are collected, so expanding a bare package to
            # all of its members is no longer needed — and it was inventing edges
            # the source never had. Importing a package does not import its members.
            if target in known:
                graph[name].add(target)
    return graph


def strongly_connected(graph: dict[str, set[str]]) -> list[list[str]]:
    """Tarjan's SCCs, iteratively — recursion died at ~1000 modules deep."""
    index: dict[str, int] = {}
    low: dict[str, int] = {}
    on_stack: set[str] = set()
    stack: list[str] = []
    result: list[list[str]] = []
    counter = 0

    for start in sorted(graph):
        if start in index:
            continue
        work: list[tuple[str, list[str]]] = [(start, sorted(graph.get(start, ())))]
        index[start] = low[start] = counter
        counter += 1
        stack.append(start)
        on_stack.add(start)

        while work:
            node, pending = work[-1]
            if pending:
                nxt = pending.pop(0)
                if nxt not in index:
                    index[nxt] = low[nxt] = counter
                    counter += 1
                    stack.append(nxt)
                    on_stack.add(nxt)
                    work.append((nxt, sorted(graph.get(nxt, ()))))
                elif nxt in on_stack:
                    low[node] = min(low[node], index[nxt])
            else:
                work.pop()
                if work:
                    parent = work[-1][0]
                    low[parent] = min(low[parent], low[node])
                if low[node] == index[node]:
                    component = []
                    while True:
                        member = stack.pop()
                        on_stack.discard(member)
                        component.append(member)
                        if member == node:
                            break
                    result.append(sorted(component))
    return result


def find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """Every elementary cycle, each in a canonical rotation.

    Scoped to strongly connected components, so an acyclic graph costs one linear
    pass and enumerates nothing.
    """
    cycles: set[tuple[str, ...]] = set()

    for component in strongly_connected(graph):
        members = set(component)
        if len(component) == 1:
            only = component[0]
            if only in graph.get(only, ()):
                cycles.add((only,))
            continue

        sub = {n: sorted(graph[n] & members) for n in component}
        for root_node in component:
            path: list[str] = []
            seen: set[str] = set()

            def walk(node: str) -> None:
                if len(cycles) >= MAX_CYCLES_PER_COMPONENT:
                    return
                path.append(node)
                seen.add(node)
                for nxt in sub[node]:
                    if nxt == root_node:
                        cycle = list(path)
                        pivot = cycle.index(min(cycle))
                        cycles.add(tuple(cycle[pivot:] + cycle[:pivot]))
                    elif nxt not in seen and nxt > root_node:
                        walk(nxt)
                path.pop()
                seen.discard(node)

            walk(root_node)

    return [list(c) for c in sorted(cycles)]


def _segments_match(module: str, prefix: str) -> bool:
    """Path-boundary aware: `domain` matches `domain.svc`, never `domain_utils`."""
    return module == prefix or module.startswith(prefix + ".")


def find_direction_violations(
    graph: dict[str, set[str]], rules: list[dict]
) -> list[dict]:
    """Modules importing across a declared `dependency_direction` boundary."""
    violations = []
    for rule in rules:
        frm, to = rule["from_prefix"], rule["to_prefix"]
        for source, targets in sorted(graph.items()):
            if not _segments_match(source, frm):
                continue
            for target in sorted(targets):
                if _segments_match(target, to):
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

    `max_cycle_length` is the longest cycle tolerated; longer ones are findings.
    Omitted means every cycle is a finding, per the sensor's rule shape.

    `modules_graphed` is part of the contract, not debug output: a detector that
    cannot say what it traversed cannot support a zero result.
    """
    graph = build_graph(root, scope)
    cycles = find_cycles(graph)
    inconclusive = len(cycles) >= MAX_CYCLES_PER_COMPONENT
    if max_cycle_length is not None:
        cycles = [c for c in cycles if len(c) > max_cycle_length]

    return {
        "modules_graphed": sorted(graph),
        "files_read": sorted(graph),
        "cycles": cycles,
        "direction_violations": find_direction_violations(graph, rules or []),
        "inconclusive": inconclusive,
    }
