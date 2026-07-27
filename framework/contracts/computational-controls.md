# Computational Controls Contract

Host projects declare their executable quality checks here so agents can run them without guessing.

## Host Declaration Location

`<ADS_MEMORY_ROOT>/governance/contracts/computational-controls.md`

## Blocking authority lives in the gate registry, not in this file

Each slot below has a **Blocking** field describing the condition under which a
breach *would* block. **That describes the gate's logic, not its current
authority.** Whether any given mechanical gate may actually stop a pipeline is
recorded in
`<AI_DEV_SHOP_ROOT>/harness-engineering/quality/gate-validation-status.md`.

At present **every gate added by the code-quality metrics program is
`unvalidated`**, which caps its `REQUIRED` dispositions at `RECOMMENDED`. The
`code_metrics`, `dependency_graph`, `type_safety`, `duplication`, and
`diff_coverage` slots therefore report findings but do not block. Canonical
integrity findings (`INT-1`…`INT-9`) and the two pre-existing legacy gates
(mutation regression, suite coverage) do block.

Read the registry before treating a `Blocking:` line here as enforcement.

## Named Command Slots

Every host project should declare as many of these as apply. Each slot is a single executable command.

### lint

- **Command**: the exact shell command to run (e.g., `npm run lint`, `ruff check .`)
- **Working directory**: project root unless specified (monorepos: specify package path)
- **Required**: yes/no — whether this slot must be filled before implementation work begins
- **Blocking**: yes/no — whether failure stops the pipeline or produces a warning
- **Timeout**: maximum seconds before the command is killed (default: 120)
- **Success criteria**: exit code 0 unless otherwise specified

### typecheck

- **Command**: e.g., `npx tsc --noEmit`, `mypy src/`
- **Working directory**: project root unless specified
- **Required**: yes/no
- **Blocking**: yes/no
- **Timeout**: default 180
- **Success criteria**: exit code 0

### build

- **Command**: e.g., `npm run build`, `cargo build --release`
- **Working directory**: project root unless specified
- **Required**: yes/no
- **Blocking**: yes (build failures always block)
- **Timeout**: default 300
- **Success criteria**: exit code 0

### unit_tests

- **Command**: e.g., `npm test`, `pytest tests/unit/`
- **Working directory**: project root unless specified
- **Required**: yes/no
- **Blocking**: yes/no
- **Timeout**: default 300
- **Success criteria**: exit code 0

### integration_tests

- **Command**: e.g., `npm run test:integration`, `pytest tests/integration/`
- **Working directory**: project root unless specified
- **Required**: yes/no
- **Blocking**: yes/no
- **Timeout**: default 600
- **Success criteria**: exit code 0
- **Environment**: note any required services (database, Redis, etc.)

### mutation_tests

- **Command**: a command that mutates a caller-supplied scope and emits killed and survived counts for it, plus each surviving mutant with its location. Substitute the scope with `{touched_files}`, `{touched_packages}` or `{touched_classes}` — whichever granularity the command accepts
- **Working directory**: project root unless specified
- **Required**: yes/no
- **Blocking**: conditional (default behavior is escalation; hard-blocks only on >10% score regression — full gate logic in `<AI_DEV_SHOP_ROOT>/harness-engineering/sensors/mutation-quality.md`)
- **Timeout**: default 600 (mutation testing is expensive; projects may increase)
- **Success criteria**: exit code 0 (gate behavior beyond exit code — including absolute thresholds, regression checks, and first-run baseline — is defined in `<AI_DEV_SHOP_ROOT>/harness-engineering/sensors/mutation-quality.md`)
- **Scope placeholder**: `{touched_files}` is replaced at runtime with the list of modified source files that have corresponding test files (mutating untested files produces no meaningful signal). The separator and quoting are host detail, declared alongside the command
- **Comparison base**: the VCS merge base, recomputed each run. **No baseline file** — a stored, agent-writable score with enforcement authority was the one poisonable artifact left in the harness and has been removed
- **Notes**: triggered by TestRunner after green suite + coverage evaluation. If this slot is not declared, the mutation quality sensor is inactive (advisory note only).

### static_analysis

- **Command**: e.g., `npm run analyze`, `semgrep --config=auto`
- **Working directory**: project root unless specified
- **Required**: yes/no
- **Blocking**: yes/no
- **Timeout**: default 300
- **Success criteria**: exit code 0

### code_metrics

Per-function structural metrics. Two are gated — cognitive complexity and nesting
depth, per `<AI_DEV_SHOP_ROOT>/skills/testable-design-patterns/SKILL.md`. Two are
mandatory to report and never gated — cyclomatic complexity and function size
(NLOC); they exist to help a reviewer interpret a gated result, not to produce
findings of their own.

- **Command**: a cross-language per-function command supplying the mandatory `cyclomatic` and `size_nloc` fields (both reported, never gated), plus a command supplying `cognitive` and `nesting` per the capability contract in the sensor doc. One command may cover all four. **This contract names no per-stack tools, flags or thresholds** — that is a deliberate deletion, not an omission.
- **No per-stack tool table lives here.** Declare a command that emits a numeric
  value per changed function plus the threshold and comparison operator it used,
  and prove it with the sensor's conformance fixtures. Naming specific tools,
  flags and defaults produced five confirmed defects and is not done any more —
  see the capability contract in
  `<AI_DEV_SHOP_ROOT>/harness-engineering/sensors/code-structure-quality.md`.
- **Record the operator with the threshold.** What silence proves depends on both. A threshold with no recorded operator cannot establish that an unreported function is under the band, and reporting it as `PASS` anyway is `INT-8`.
- **Secondary command** (optional): a second tool whose per-function output is merged on `file path + symbol name`. Most hosts need two — one cross-language tool for the mandatory cyclomatic field, one per-language tool for the gated cognitive metric. A single command that emits both may fill the slot alone.
- **Required output fields**: per changed function — `cyclomatic` and `size_nloc` are **mandatory** (both reported, never gated); `cognitive` and `nesting` are **conditional**, supplied where the stack has an analyzer for each. Cross-language per-function tools typically emit cyclomatic and NLOC from the same parse, so the mandatory pair usually costs one command. **`nesting` needs its own adapter on most stacks** — cross-language tools generally do not emit it, and neither do most cognitive analyzers. A missing `cognitive` or `nesting` value makes that metric's gate `INCONCLUSIVE`, never `PASS`. A declared command that cannot emit per-function cyclomatic or size values is a **declaration defect**, reported as a Required workflow finding against the contract rather than against the code under review.
- **Scoped command**: strongly recommended — this slot is only meaningful on changed files
- **Working directory**: project root unless specified
- **Required**: no
- **Blocking**: conditional — a breach blocks only when the function is **new or worsened** against the comparison base (see the sensor doc); never on untouched or unworsened legacy code
- **Timeout**: default 180
- **Success criteria**: parseable output. A non-zero exit from a threshold-enforcing linter is a finding, not a slot failure.
- **Placeholders**: `{files}` (changed files), `{base_ref}`, `{head_ref}`
- **Notes**: **cognitive complexity is the gated metric, not cyclomatic.** An analyzer that scores a flat exhaustive `switch` as a high-complexity breach is non-conformant and must be treated as advisory-only — see the conformance fixtures in the sensor doc. If this slot is not declared, the sensor is inactive and the complexity gates degrade to advisory review prompts (state this in the review report rather than implying enforcement).
- **Gate logic**: defined in `<AI_DEV_SHOP_ROOT>/harness-engineering/sensors/code-structure-quality.md`

### dependency_graph

Module-graph analysis used to detect **dependency cycles** and to mechanically
check the boundary rules declared in
`<AI_DEV_SHOP_ROOT>/framework/contracts/architecture-fitness.md`. This is the
slot that makes `no_cycle` rules executable — an agent reading a diff cannot see
a cycle that closes through files it never opened.

- **Command**: a command that emits the import graph over the full source root, naming both endpoints of every edge. Prefer one that covers cycles *and* the two mechanically-checkable boundary types, `dependency_direction` and `forbidden_import`, in a single pass — otherwise those rules are maintained in two places that drift. **`boundary_ownership` cannot be covered by any import graph** — it asserts that a human approval exists, which no graph can observe; it stays an evidence check in Code Review. **Pass `{src}`, not `{files}`**: cycle detection needs the reachable closure, and a graph built only from changed files cannot see a cycle that closes through untouched modules
- **Required output fields**: per finding — the rule name or `cycle`, the participating module paths in order, and for cycles the cycle length
- **Scoped command**: scope depends on the check. Boundary rules need the changed modules plus one level of direct importers. **Cycle detection needs the full reachable closure of every changed module** — a cycle can close through files the diff never touched, so a one-level scan cannot support a "no cycles" result and is `INCONCLUSIVE` for that check
- **Working directory**: project root unless specified
- **Required**: no
- **Blocking**: conditional — a cycle or violation blocks only when it is **new against the comparison base** and the matching rule's severity is `blocking`; pre-existing cycles in untouched modules are grandfathered
- **Timeout**: default 300
- **Success criteria**: parseable output. A non-zero exit from a rule-enforcing analyzer is a finding, not a slot failure.
- **Placeholders**: `{files}` (changed files), `{base_ref}`, `{head_ref}`
- **Notes**: distinct from `static_analysis` — that slot holds general-purpose analyzers, this one holds the tool that computes reachability. If this slot is not declared, `no_cycle` rules are **inert** (they cannot degrade to agent inspection the way the other rule types can) and the review report must say so rather than implying enforcement.
- **Gate logic**: defined in `<AI_DEV_SHOP_ROOT>/harness-engineering/sensors/dependency-structure.md`

### type_safety

Countable **unsafe typed-language operations** on changed code — the operations
that defeat the type checker rather than satisfy it. Distinct from `lint`: a lint
slot returning exit code 0 proves the configured rules passed, not that the rules
that matter here were configured or enabled.

- **Command**: e.g., `npx eslint --format json {files}` with a **type-aware** `typescript-eslint` config (`parserOptions.project` or `projectService` must be set)
- **Required output fields**: per violation — rule id, file path, and enclosing symbol. Line numbers alone are insufficient; occurrence identity is matched on `file path + rule id + enclosing symbol` because line numbers shift on any edit.
- **Strictness diff**: the sensor also diffs `tsconfig*.json` and the ESLint config between `{base_ref}` and `{head_ref}`; no separate command is declared for this
- **Scoped command**: strongly recommended — type-aware linting is substantially slower than syntactic linting and can dominate PR time on a large repo
- **Working directory**: project root unless specified
- **Required**: no
- **Blocking**: conditional — a Tier A violation blocks only when it is **new against the comparison base**; separately, **any weakening of compiler or lint strictness blocks regardless of the violation delta** (a one-line `strict: false` can move hundreds of violations to zero while making the codebase less safe)
- **Timeout**: default 600 (type-aware linting is expensive; projects may increase)
- **Success criteria**: parseable output. A non-zero exit from a rule-enforcing linter is a finding, not a slot failure.
- **Placeholders**: `{files}` (changed files), `{base_ref}`, `{head_ref}`
- **Notes**: **TypeScript-specific by default** — the only stack-specific slot here. A host may map it onto an equivalent (`# type: ignore` counts plus mypy strictness, Kotlin `!!`, C# `dynamic`); those mappings are the host's and are not claimed equivalent. A declared command whose type-aware rules are not actually active reports **zero violations while detecting nothing** — the sensor's conformance fixture exists to catch exactly this, and an unverified zero is `INCONCLUSIVE`, never `PASS`.
- **Gate logic**: defined in `<AI_DEV_SHOP_ROOT>/harness-engineering/sensors/type-safety.md`

### diff_coverage

**Changed-code branch coverage** — what fraction of the branches this change
added or modified is exercised by tests. Distinct from `unit_tests` coverage
output, which is a suite-level percentage: a suite at 98% can absorb a dozen new
untested branches without moving.

- **Command**: two layers. The **branch layer** (primary) is a host adapter that intersects the coverage report's branch records (`BRDA:` in lcov, `condition-coverage` in Cobertura, JaCoCo branch counters) with the diff's changed line ranges. The **line layer** (secondary) attributes a coverage report to the diff and reports changed lines covered. **A line-layer command satisfies the secondary metric only** — a host that reports its line ratio under a branch field name commits `INT-7`.
- **Required output fields**: `changed_branches_total`, `changed_branches_covered`, and **the same pair per changed file**. Per-file output is mandatory: the aggregate alone cannot detect denominator padding, where well-covered boilerplate lifts the ratio while the new logic stays untested. Where only line data exists, report the branch fields as `null` and gate on the line ratio, labeled as line-based.
- **Input**: the raw coverage report emitted by the `unit_tests` / `integration_tests` run — this slot does not run tests
- **Working directory**: project root unless specified
- **Required**: no
- **Blocking**: conditional. **The gate conditions and every threshold live in `<AI_DEV_SHOP_ROOT>/harness-engineering/sensors/changed-code-coverage.md`, and the arithmetic is executable in `<AI_DEV_SHOP_ROOT>/harness-engineering/gate-logic/reference.py`.** This contract deliberately does not restate them — an earlier version did, and its copy of the zero-coverage rule drifted out of date while reading as authoritative
- **Timeout**: default 120 (attribution is cheap; the expensive test run happens in another slot)
- **Success criteria**: parseable output covering the changed files. A report that does not cover the changed files is `INCONCLUSIVE`, not a pass.
- **Placeholders**: `{base_ref}`, `{head_ref}`, `{files}`, `{out}`
- **Notes**: **not delta-gated** — this is the one gate evaluated absolutely on the diff, because it measures only code the change touched and there is no legacy portion to grandfather. A slot emitting only an aggregate project percentage is a **declaration defect**; that is the `coverage-quality` metric, not this one.
- **Gate logic**: defined in `<AI_DEV_SHOP_ROOT>/harness-engineering/sensors/changed-code-coverage.md`

### duplication

Copy-paste clone detection on changed code.

- **Command**: a clone detector run over `{src}` at the sensor's declared thresholds. **Note `{src}`, not `{files}`** — clone detection compares fragments against each other, so a tool given only the changed files cannot see that a new copy matches two untouched ones, which is the most common case of the gate this sensor exists to enforce. Scan the full source scope at base and head; `{files}` narrows attribution, never the scan
- **Required output fields**: per clone group — **both site file paths and line ranges**, occurrence count, and token count. A command emitting only an aggregate duplication **percentage** is a **declaration defect**: a ratio cannot be attributed to a change, cannot be delta-compared, and is the form of this metric most often gamed by inflating the denominator.
- **Thresholds**: defined in `<AI_DEV_SHOP_ROOT>/harness-engineering/sensors/duplication.md` and executable in `gate-logic/reference.py`. **Not restated here** — a duplicated threshold is the defect this contract has produced most often.
- **Scoped command**: **no** — this is the one slot where scoping the scan destroys the check. Attribution is scoped by the sensor (is any site in the changed set?); the scan itself must cover `{src}` at base and head
- **Working directory**: project root unless specified
- **Required**: no
- **Blocking**: conditional — a Type-1/Type-2 clone group blocks when `head_occurrences > base_occurrences AND head_occurrences >= 3`, above threshold, with at least one site in changed scope. Not "a new clone group" — a two-site group already exists at base, so a novelty test never fires on the third-site crossing. Canonical arithmetic: `<AI_DEV_SHOP_ROOT>/harness-engineering/gate-logic/reference.py`. A 2-site clone is Recommended only. **Raising the declared threshold to clear a finding is scope narrowing** and is itself a Required finding (`INT-2`).
- **Timeout**: default 300
- **Success criteria**: parseable output. A non-zero exit from a threshold-enforcing tool is a finding, not a slot failure.
- **Placeholders**: `{files}` (changed files), `{src}`, `{base_ref}`, `{head_ref}`
- **Notes**: this gate is deliberately narrow. Duplication is the metric most likely to push toward a **worse** design than the one it flagged — extracting at two sites regularly yields a helper parameterized by caller identity. It also pulls directly against the `code_metrics` complexity gates; the sensor doc defines how Code Review adjudicates that conflict rather than requiring both to be satisfied.
- **Gate logic**: defined in `<AI_DEV_SHOP_ROOT>/harness-engineering/sensors/duplication.md`

## Slots With No Contract Entry

Not every sensor needs a declared command. `<AI_DEV_SHOP_ROOT>/harness-engineering/sensors/change-history.md` runs on `git log` alone — **no command slot**, and its churn, change-frequency, and revert-frequency metrics work on any repo with history. Do not add a command slot for it; the absence is deliberate.

**It does need one optional declaration.** Metric 12 (previous defects per module) requires commit-to-defect linking, which no repo has by default:

### defect_link_pattern (declaration, not a command)

- **Pattern**: a regex matching a defect reference in commit messages, e.g. `Fixes #\d+`, `JIRA-\d+`, `closes [A-Z]+-\d+`
- **Required**: no
- **Notes**: when undeclared, `change-history.md` reports the defect count as `null` and falls back to fix frequency as an explicitly-labeled proxy. **Do not present fix frequency as a defect count.** Declaring this is the only host cooperation the change-history sensor asks for, and everything except metric 12 works without it.

## When Agents Execute These Slots

| Stage | Slots used |
|-------|-----------|
| Programmer (during implementation) | lint, typecheck, build, unit_tests; code_metrics, dependency_graph, type_safety, duplication (advisory previews) |
| Programmer (before handoff) | all declared slots except mutation_tests |
| TestRunner | unit_tests, integration_tests, mutation_tests* |
| Code Review | lint, typecheck, static_analysis, code_metrics**, dependency_graph**, type_safety**, duplication**, diff_coverage*** |
| Observer (scheduled only) | code_metrics (complexity and size distribution trends — the only place the anti-fragmentation signature is watched), dependency_graph (full graph), type_safety, duplication (whole-repo trends), plus `git log` change-history passes that need no slot |

*`mutation_tests` runs conditionally after `unit_tests` and `integration_tests` pass. See TestRunner agent skills for sequencing details.

***`diff_coverage` splits by cost: TestRunner produces the raw coverage report as a side effect of the suite run it already owns, and Code Review recomputes the diff attribution and ratios itself from that report plus its own `git diff` against the merge base. Code Review never accepts a diff-coverage number from another agent. It cannot verify the raw report is authentic without re-running the suite — that residual is stated in the sensor doc rather than papered over.

**`code_metrics`, `dependency_graph`, `type_safety`, and `duplication` are executed by Code Review on **every** reviewed change, not sampled. Code Review's own invocation is the authoritative result. The Programmer may run the same command as an advisory preview and must fix what it reports, but may never restate metric values as free text in a handoff — a handoff asserting metric values without a Code Review run behind them is a Required workflow finding. Rationale: the measured party must not author the measurement, and for a check costing seconds the correct control is unconditional recomputation by the consumer rather than artifact protection.

## Behavior When Contract Is Missing

See [enforcement.md](enforcement.md) for the full enforcement model. Summary:

- **Greenfield project**: Coordinator warns at pipeline start. Programmer stage is blocked until at least `build` and one test slot are declared.
- **Brownfield project**: Advisory mode. Coordinator logs that the contract is absent. Agents proceed but handoffs note that no executable controls were verified.

## Behavior When a Check Fails

- **Blocking slot fails**: the stage cannot hand off. The agent must attempt one fix cycle, then report failure.
- **Non-blocking slot fails**: the failure is reported in the handoff summary. Downstream stages are informed. Pipeline continues.

## Behavior When a Slot Is Declared but Empty

A slot declared as required but with no command means the host acknowledges the gap. The Coordinator treats this as a known gap and reports it at pipeline start. It does not block unless enforcement is set to strict.

## Working Directory Resolution

Commands run from the host project root by default — not the toolkit root.

- `<HOST_PROJECT_ROOT>` is the root of the host repository (where `.git/` lives)
- If `<AI_DEV_SHOP_ROOT>` is a subfolder install, commands still resolve against `<HOST_PROJECT_ROOT>`
- Per-slot working directory overrides are relative to `<HOST_PROJECT_ROOT>`

## Touched-Scope Enforcement for Project-Wide Commands

Many tools (linters, type checkers) check the entire project and return a single exit code. In brownfield projects with baseline failures, agents must distinguish new violations from pre-existing ones.

Resolution order:
1. **Scoped command variant** (preferred): if the tool supports file arguments, declare a `scoped_command` alongside `command`. Example: `command: npm run lint` / `scoped_command: npx eslint {files}`. Agents use the scoped variant and pass only modified files.
2. **Diff-based attribution**: if no scoped variant exists, run the command, capture output, and attribute failures to modified files only. Pre-existing failures in untouched files are ignored for enforcement purposes.
3. **Baseline fingerprint**: if output attribution is impractical, run the command once at contract creation to capture a baseline failure set. New failures beyond baseline are violations; baseline failures are grandfathered.

If none of these methods can distinguish new from baseline failures, treat the slot as **advisory** (not blocking) until a scoped command is available.

## Monorepo Support

For monorepos with multiple packages, declare slots per package scope:

- Use a separate command slot entry per package, or
- Use a root-level command that handles routing internally (e.g., `turbo run lint`)
- Specify the working directory for each slot when it differs from `<HOST_PROJECT_ROOT>`
