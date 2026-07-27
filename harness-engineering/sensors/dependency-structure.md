# Sensor: Dependency Structure

Detects **dependency cycles** and mechanically enforces **architecture-boundary
violations** on changed code. Closes the gap where
`framework/contracts/architecture-fitness.md` declared boundary rules but nothing
computed a module graph to check them against.

## Sensor Definition

- **Class**: `computational`
- **Timing**: PR (changed modules) + scheduled (full graph)
- **PR owner**: **Code Review** (executes the declared `dependency_graph` slot; same custody rule as `code_metrics`)
- **Scheduled owner**: Observer → routes to Software Architect
- **Artifact**: `<ADS_MEMORY_ROOT>/.local-artifacts/sensors/dependency-structure-<feature-id>-<timestamp>.json`

## Why this sensor exists

`architecture-fitness.md` carries three rule types — `dependency_direction`,
`forbidden_import`, `boundary_ownership`. **None can express "no cycles,"** and
until this sensor existed the declared rules were checked by an agent reading
imports rather than by a tool computing reachability. An agent reading a diff
cannot see a cycle that closes through three files it did not open.

This sensor adds the fourth rule type and the mechanical check.

## New rule type: `no_cycle`

Declared in `<ADS_MEMORY_ROOT>/governance/contracts/architecture-fitness.md`
alongside the existing three.

- **Name**: identifier, e.g. `no-cycles-in-domain`
- **Type**: `no_cycle`
- **Scope**: glob the rule applies to, e.g. `src/domain/**`
- **Severity**: `blocking` or `advisory`
- **Max cycle length**: optional; omit to forbid all cycles in scope
- **Rationale**: why this boundary exists

## Tools

The toolkit installs nothing; the host declares a command in the `dependency_graph`
slot of `<AI_DEV_SHOP_ROOT>/framework/contracts/computational-controls.md`. If the
slot is undeclared this sensor is inactive, and `no_cycle` rules go dark rather
than degrading to agent inspection — the review report must say so.

| Stack | Tool | Reference command | Emits |
|---|---|---|---|
| TypeScript / JavaScript | **dependency-cruiser** (recommended) | `npx depcruise --output-type json {src}` | cycles, forbidden deps, orphans — one pass |
| TypeScript / JavaScript (light) | `madge` | `npx madge --circular --json {src}` | cycles only |
| Python | `pydeps` / `import-linter` | `lint-imports --config .importlinter` | cycles, layer contracts |
| Go | `go list` + `godepgraph` | `godepgraph -s {pkg}` | package graph |
| Java / Kotlin | ArchUnit / JDepend | project-specific | cycles, layer rules |
| Generic fallback | none | — | sensor inactive; boundary rules stay agent-checked |

**dependency-cruiser is the recommended default for JS/TS** because it covers
cycles *and* the two mechanically-checkable boundary rule types in one
declaration — a host can map `dependency_direction` and `forbidden_import`
straight onto its `forbidden` ruleset rather than maintaining two sources of
truth.

`boundary_ownership` is the third declared rule type and is **not** among them —
it asserts that a human approval exists, which no import graph can observe. Three
of the four `architecture-fitness` rule types are tool-backed here; the fourth
stays an evidence check. Do not describe this sensor as covering all four.

## Conformance Fixtures (required before this sensor may report a clean result)

**An under-scoped command is indistinguishable from an acyclic repository.** A
`dependency_graph` command whose entry point or glob misses the changed modules
exits 0 and emits a valid, empty findings list. Nothing in the output separates
"no cycles" from "graphed nothing." Because this sensor is the *only* mechanism
that can check `no_cycle` at all — an agent reading a diff cannot substitute for
it — an unexercised detector here fails silently and completely.

| Fixture | Expectation |
|---|---|
| Two modules in the **changed scope** with a direct circular import | reported as a cycle of length 2, both modules named — **proves the graph reaches the changed files** |
| A three-module cycle closing through a file the diff does not touch | reported — proves the traversal is not limited to changed files alone |
| A module violating a declared `dependency_direction` rule | reported against that rule by name — proves the contract rules were actually loaded, not just the cycle check |
| An acyclic module importing five others | **not** reported — negative control against a tool misconfigured to flag fan-out |

A zero-finding result without a passing fixture run is `INCONCLUSIVE`, not
`PASS`. Report the difference rather than implying the graph was computed.

Re-run fixtures on any tool or ruleset change, and compute base and head with the
same tool version and configuration.

## Traversal scope — one importer level is not enough for cycles

PR context computes the graph over changed modules plus their direct importers.
That is sufficient to attribute a *violation* to the diff, but it is **not**
sufficient to prove the absence of a cycle: a cycle can close through modules
several hops away that the diff never touched.

So the scope rule is split by question:

- **Boundary-rule violations**: changed modules plus one importer level is
  adequate — a violation is a property of an edge, and the changed edges are all
  in scope.
- **Cycle detection**: traverse the **full reachable closure** of every changed
  module. Anything less cannot support a "no cycles" claim, and a partial
  traversal reporting zero cycles must be recorded as `INCONCLUSIVE` for the
  cycle check specifically, not as a pass.

If the closure is too large to compute in PR time, say so and mark the cycle
check `INCONCLUSIVE`. Do not narrow the traversal and report the result as clean.

## Gate Logic

**Delta-based, same as every other gate in this harness.**

```text
BREACH = a cycle or violation exists in the changed scope
         AND it is not present in the merge base
```

- A cycle that already existed and is untouched: **no block**, advisory note.
- A cycle a change **introduces or lengthens**: **REQUIRED**.
- A boundary violation a change introduces: **REQUIRED** if the rule is
  `blocking`, `RECOMMENDED` if `advisory` (per the existing Validator Priority
  Rule in `architecture-fitness.md`).
- Pre-existing violations in untouched files remain grandfathered — this sensor
  does not change that contract.

**Scope depends on the question — see "Traversal scope" above.** Boundary-rule
checks need the changed modules plus one level of direct importers. **Cycle
detection needs the full reachable closure of every changed module**; a partial
traversal cannot support a "no cycles" claim and is `INCONCLUSIVE` for the cycle
check. A whole-repo scan is not required for either, but a one-level scan is not
sufficient for cycles.

## Severity

| Finding | Severity | Disposition |
|---|---|---|
| New dependency cycle in `blocking` scope | `High` | `REQUIRED` |
| New violation of a `blocking` boundary rule | `High` | `REQUIRED` |
| New violation of an `advisory` rule | `Medium` | `RECOMMENDED` |
| Pre-existing cycle, untouched | — | advisory note only |
| Zero findings without a passing conformance fixture | — | `INCONCLUSIVE`, never `PASS` |
| Cycle check run over a partial closure | — | `INCONCLUSIVE` for cycles, never `PASS` |

Mechanically-sourced severities are **fixed and may not be downgraded** by a
reviewing agent, consistent with `code-structure-quality.md`. A reviewer may
uphold a documented justification; it may not relabel an unresolved breach.

**Two different axes use the words `blocking` and `advisory`; do not conflate
them.** A host declares `Severity: blocking | advisory` **per boundary rule** in
`architecture-fitness.md` — that is an authoring choice about one rule. This
sensor's own **validation status** is separate, harness-wide, and named
`unvalidated` / `validated` / `inactive` precisely to avoid the collision.

They compose, and the stricter wins: a violated `blocking`-severity rule is
`REQUIRED` **at `validated` status**, and while this sensor is `unvalidated` it is
still capped at `RECOMMENDED`. A host-declared `blocking` rule does **not**
currently block.

**Dispositions in this table apply at `validated` status.** Current status is in
`<AI_DEV_SHOP_ROOT>/harness-engineering/quality/gate-validation-status.md`.
Canonical integrity findings (`INT-1`…`INT-9`) are never capped — including `INT-3`,
downgrading a declared rule's `Severity` from `blocking` to `advisory` to clear a
finding.

**`boundary_ownership` is not covered by this sensor at any status.** It is an
approval rule — "changes here require security sign-off" — and no import graph
can prove an approval exists. It remains an evidence check performed by Code
Review against the handoff, and describing this sensor as covering all four rule
types is wrong.

## Custody

Identical to `code-structure-quality.md`: Code Review executes the command on
every reviewed change and its run is authoritative. Programmer may run it as an
advisory preview and must never restate results as free text.

## Brownfield

First run records nothing and blocks nothing — the merge base supplies the
comparison, so there is no baseline file to write or poison. A repo with 40
existing cycles blocks on cycle 41 only if the change introduces it.

## Known Limitations

- **Cycle detection is import-graph only.** Runtime cycles via dynamic import,
  DI containers, or string-keyed registries are invisible to every tool listed.
- **Rule mapping is host work.** Translating declared `dependency_direction` /
  `forbidden_import` rules into the tool's own config is manual and can drift.
  Where the tool supports it, generate the config from the contract rather than
  maintaining both.
- **Unvalidated.** Like every gate in this harness, thresholds and severities are
  provisional until the eval runs.

## Related

- `framework/contracts/architecture-fitness.md` — rule declarations, including the new `no_cycle` type
- `code-structure-quality.md` — function-local metrics; deliberately does not cover module-graph properties
- `dead-code.md` — orphan/unused detection, adjacent concern
