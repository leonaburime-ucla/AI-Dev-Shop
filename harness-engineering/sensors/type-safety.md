# Sensor: Type Safety

Counts **unsafe typed-language operations** on changed code — the operations that
defeat the type checker rather than satisfy it — and delta-gates new ones.

Closes the gap where unsafe operations were nominally "covered by the `lint`
slot" but had no named, countable, ratchetable signal. A lint slot that returns
exit code 0 tells you the configured rules passed; it does not tell you whether
the rules that matter here were configured, enabled, or suppressed.

## Sensor Definition

- **Class**: `computational`
- **Timing**: PR (changed files) + scheduled (whole-repo trend)
- **PR owner**: **Code Inspection** (executes the declared `type_safety` slot; same
  custody rule as `code_metrics` — the measured party never authors the measurement)
- **Scheduled owner**: Observer → routes to Programmer/Refactor
- **Artifact**: `<ADS_MEMORY_ROOT>/.local-artifacts/sensors/type-safety-<feature-id>-<timestamp>.json`

## Stack scope — stated plainly

**This is the only sensor in the set that is language-specific.** It is defined
for TypeScript, where "unsafe operation" has a precise meaning: an expression
whose type is `any`, an assertion that overrides inference, or a directive that
suppresses the checker.

Equivalents exist elsewhere and a host may map the slot onto them — Python
`# type: ignore` counts plus mypy strictness, Kotlin `!!`, C# `dynamic` and
nullable-disable pragmas, Go unchecked `interface{}` assertions. Those mappings
are the host's to make and are **not** claimed to be equivalent here. On a stack
with no mapping, this sensor is inactive and the review report says so. Do not
present an inactive sensor as a clean result.

## What is counted

Two tiers, gated differently. The split is not cosmetic — it separates *creating*
an untyped value from *acting* on one.

### Tier A — soundness holes (new occurrence → `REQUIRED`, fixed `High`)

These defeat the checker or discard an error. There is no reading of the diff in
which they are the safe option.

| Signal | Source |
|---|---|
| `@typescript-eslint/no-unsafe-assignment` | type-aware rule |
| `@typescript-eslint/no-unsafe-call` | type-aware rule |
| `@typescript-eslint/no-unsafe-member-access` | type-aware rule |
| `@typescript-eslint/no-unsafe-return` | type-aware rule |
| `@typescript-eslint/no-unsafe-argument` | type-aware rule |
| `@typescript-eslint/no-floating-promises` | type-aware rule — an unawaited promise drops its rejection |
| `@ts-ignore` directive | source scan |
| **`@ts-expect-error` with no description** | source scan — functionally `@ts-ignore` with an expiry; see below |
| **`@ts-nocheck` directive** | source scan — disables checking for an **entire file**; the cheapest total bypass in the language |
| **Double assertion** — `as unknown as T`, `as any as T` | AST rule / source scan |
| **New `any` in an exported or otherwise shared declaration** (return type, parameter, public field) | type-aware rule + export check |
| New or broadened rule suppression for any Tier A rule (`eslint-disable*`) | source scan |
| Compiler-strictness weakening (see below) | config diff |

### Tier B — discipline signals (new occurrence → `RECOMMENDED`, `Medium`)

These are how untyped values enter. They are legitimate at real boundaries and
the correct fix is often a validated parse — a larger change than the diff at
hand may warrant.

| Signal | Source |
|---|---|
| `@typescript-eslint/no-explicit-any` — **local, non-exported only** | syntactic rule + export check |
| Non-null assertion `!` (`@typescript-eslint/no-non-null-assertion`) | syntactic rule |
| Single type assertion `as T` other than `as const` | AST rule |
| `@ts-expect-error` **with** a description | source scan |

**Why a local `any` is Tier B while consuming an `any` is Tier A.** An `any` at a
genuine boundary — `JSON.parse`, an untyped third-party module, a `fetch` body —
is honest about what is actually known at that point. The risk materializes where
the value is *used* without narrowing, and that is what the `no-unsafe-*` family
reports. Gating consumption rather than declaration is more precise and
false-fires less.

**But that reasoning only holds while the `any` stays local.** An `any` in an
*exported* signature exports the unsoundness: unchanged callers in files this
diff never touched now consume it, outside the changed scope this sensor
measures, so the Tier A consumption finding never fires anywhere. That is why
exported `any` is Tier A above. The honest type at a boundary is `unknown`, which
forces narrowing at the point of use; `any` is the type that silently doesn't.

**Double assertions are Tier A for the same reason.** `JSON.parse(x) as unknown
as T` launders a Tier A unsafe-member-access into two Tier B assertions and
asserts a shape nothing verified. Any assertion chain of length ≥ 2 is treated as
a soundness hole, not a discipline signal — the intermediate `unknown` exists
only to silence the checker. A single `as T` from a related type stays Tier B.

**A *described* `@ts-expect-error` is Tier B and `@ts-ignore` is Tier A** because
`@ts-expect-error` fails the build when the error it suppresses goes away. It
carries an expiry; `@ts-ignore` does not.

**A bare `@ts-expect-error` — no description — is Tier A.** An earlier draft
listed only the described form in Tier B and neither form in Tier A, so the
strictly worse variant fell through both tiers and produced no finding at all,
while its better-documented sibling produced a `Medium`. That is a gradient
pointing the wrong way: an agent minimising findings learns to *delete the
description*. Without a rationale the directive is `@ts-ignore` that happens to
expire, so it is graded with `@ts-ignore`.

Note the `rg` reference command already matches both forms; the defect was in
classification, not detection.

## Compiler-strictness weakening — not delta-gated

A per-file violation count is trivially gamed by one line in `tsconfig.json`.
Turning off `strict`, setting `strictNullChecks: false`, adding
`skipLibCheck` to hide a real breakage, or adding a path to `exclude` can move
hundreds of violations to zero while making the codebase strictly less safe.

Therefore: **any weakening of compiler or lint strictness is a `REQUIRED`
finding on its own, regardless of the violation delta**, and it is not eligible
for the "no new violations" pass. This is the same rule
`<AI_DEV_SHOP_ROOT>/harness-engineering/quality/coverage-integrity-policy.md`
applies to coverage-ignore directives, applied to the type checker.

Weakening includes: disabling any `strict`-family flag, downgrading a Tier A rule
from `error` to `warn` or `off`, adding files to `exclude`/`ignorePatterns`, and
adding a blanket file-level `eslint-disable`. A widened exclusion within the same
work requires recorded human approval, per that policy.

Strengthening is always allowed and never blocks — including when it surfaces a
large number of pre-existing violations. Those are grandfathered; see Brownfield.

## Tools

The host declares a command in the `type_safety` slot of
`<AI_DEV_SHOP_ROOT>/framework/contracts/computational-controls.md`.

So the contract is a **capability**, not a tool:

> Declare a command that emits, per finding, a **rule identifier** with its file
> and position. Prove it with the conformance fixtures below. If it cannot, this
> sensor is `inactive` — reported as absent, never as clean.

| Signal group | What the declared command must do |
|---|---|
| Tier A + Tier B rules | Run **type-aware**. The Tier A rules cannot be decided from syntax alone, and a syntax-only configuration silently reports zero for them |
| Single assertions, assertion style | Emit a rule id per occurrence, from the same run |
| **Double assertions** (`as unknown as T`) | **No stock rule is known to detect these.** Detection needs a local AST rule matching an assertion expression whose operand is itself an assertion expression, and its rule id must appear in the output. Absent that rule, this signal is `inactive`, not clean |
| Directive and suppression counts | Count `@ts-ignore`, `@ts-expect-error`, `@ts-nocheck` and `eslint-disable` occurrences with positions. See the AST requirement below — a regex over source is not sufficient |
| Compiler strictness | Report whether the change touches compiler or lint configuration, so a strictness reduction is visible alongside the findings it suppresses |

**No stock lint rule detects the Tier A double assertion.** An earlier draft
paired `consistent-type-assertions` with `no-unnecessary-type-assertion` and
claimed the two covered it. They do not: the first enforces assertion *style*
(angle-bracket vs `as`), and the second flags assertions that do **not** change a
type — while both legs of `value as unknown as T` change the type deliberately,
which is the entire point of the laundering. So neither rule fires, and the
conformance fixture below would fail against the declared command.

Detecting it needs a host-authored AST rule: flag any `TSAsExpression` whose
`.expression` is itself a `TSAsExpression` (equivalently, any assertion chain of
length ≥ 2). It is a few lines of rule code, but it is **not** available off the
shelf, and a host that declares only the stock rules has no Tier A
double-assertion detector — report that as a declaration defect rather than a
clean result.

**Assertion detection must be AST-backed, not regex.** An earlier draft of this
file specified
`rg -n --json '@ts-ignore\|@ts-expect-error\|\bas\s+(?!const\b)[A-Z]'`. That
command is broken in two independent ways and must not be used:

1. **It does not run.** ripgrep's default engine rejects look-around —
   `error: look-around, including look-ahead and look-behind, is not supported` —
   so the command exits 2. A sensor whose detector exits non-zero produces no
   findings, which is indistinguishable from clean output unless the fixtures
   below catch it.
2. **The alternation was wrong anyway.** Inside a single-quoted pattern, `\|` is
   a *literal pipe*, not alternation, so even with `--pcre2` it would search for
   the one long literal string rather than three alternatives. Hence the separate
   `-e` flags above.

And even a corrected regex is the wrong tool: `as any as T`, `as string`,
`as\n  T` across a line break, and assertions inside template strings all defeat
text matching in one direction or the other. Use the lint rules. Reserve
`ripgrep` for the comment directives, which are genuinely lexical.

A single `eslint` invocation covers both tiers when the config enables the
type-aware rules; the `rg` scan exists only for the directives ESLint does not
report as violations.

## The activation trap — why a clean result must be proven

The `no-unsafe-*` family and `no-floating-promises` are **type-aware rules**.
They require `parserOptions.project` (or `projectService`) pointing at a real
`tsconfig`. Type-aware linting is substantially slower than syntactic linting, so
many repos never enable it.

**When it is not enabled, these rules do not run and ESLint reports zero
violations.** A sensor that reports that as "clean" is reporting the absence of a
detector as the absence of a problem — the single most dangerous failure mode in
this whole harness.

So a Tier A count of zero is only reportable as `PASS` when rule activation has
been **positively verified** by the conformance fixture below. Otherwise the
result is `INCONCLUSIVE`, the gate degrades to advisory, and the report says the
detector did not run.

## Conformance Fixtures (required before this sensor may block)

| Fixture | Expectation |
|---|---|
| A file calling a method on a `JSON.parse` result without narrowing | `no-unsafe-member-access` and/or `no-unsafe-call` reported — **proves type-aware linting is on** |
| An async function called without `await` or `.catch()` | `no-floating-promises` reported |
| A `tsconfig.json` diff turning `strict` from `true` to `false` | strictness-weakening finding raised with no violation-count change |
| A file whose only change is adding `// eslint-disable-next-line @typescript-eslint/no-unsafe-call` over an existing violation | counted as a **new Tier A occurrence**, not as a fix |
| A file with `// @ts-nocheck` at the top | counted as a Tier A occurrence — proves the whole-file bypass is detected |
| `const t = JSON.parse(s) as unknown as Thing` | counted as a Tier A double assertion, **not** as two Tier B assertions |
| An exported function returning `any` | counted as Tier A; the same `any` on a non-exported local returns Tier B |
| **Every declared command run end-to-end, exit codes captured** | no detector exits non-zero — catches an unparseable pattern, a missing plugin, or a bad glob before any result is trusted |

The last four fixtures are the anti-gaming controls and are not optional.
Suppressing a violation is not resolving it, and a detector that fails to start
is not a clean result.

Re-run fixtures on any ESLint, `typescript-eslint`, or TypeScript version change,
and compute base and head with the same versions. Never compare a count produced
by one rule set to a count produced by another — a rule-set change invalidates
the delta entirely and the result is `INCONCLUSIVE` for that run.

## Gate Logic

Delta-based against the VCS merge base, consistent with every other gate here.
There is no stored baseline file.

```text
BREACH = a Tier A occurrence exists in the changed scope
         AND it is not present at the same site in the merge base

BREACH = compiler or lint strictness weakened   (independent of any count)
```

- Counts are compared **per changed file**, not repo-wide. A repo-wide total
  lets a reduction in one file pay for a regression in another.
- Occurrence identity is `file path + rule id + enclosing symbol`. Line numbers
  shift on any edit and must not be used for matching.
- Pre-existing violations in untouched files are irrelevant and never block.
- **Relocation needs its own matcher, because the identity key cannot express
  it.** A cross-file move changes `file path`, so under the key above the moved
  violation is unmatched at base and reads as new. Resolve in this order:
  1. Git rename data maps the old path to the new one → same occurrence, report
     as relocated.
  2. No rename record, but the enclosing symbol name and the violating
     expression's normalized text both match a base-side occurrence in a deleted
     file → same occurrence, relocated.
  3. Otherwise → **treat it as new.** The conservative direction is deliberate:
     an agent that moves an unsafe operation and argues it is grandfathered must
     not win by default. A false "new" costs one justification; a false
     "relocated" silently launders a Tier A finding.
- If the rule set, tool version, or tsconfig changed in the same diff, the count
  delta is `INCONCLUSIVE` — but the strictness check still applies and can still
  block on its own.

## Severity

| Finding | Severity | Disposition |
|---|---|---|
| New Tier A occurrence in changed code | `High` | `REQUIRED` |
| Compiler or lint strictness weakened without recorded approval | `High` | `REQUIRED` |
| New Tier A suppression comment over an existing violation | `High` | `REQUIRED` |
| New Tier B occurrence in changed code | `Medium` | `RECOMMENDED` |
| Pre-existing violation, untouched | — | advisory note only |
| Tier A count of zero without verified rule activation | — | `INCONCLUSIVE`, never `PASS` |
| Any declared detector exiting non-zero for a non-finding reason | — | `INCONCLUSIVE`; fix the declaration |

**Dispositions in this table apply at `validated` status.** This gate's current
status is in
`<AI_DEV_SHOP_ROOT>/harness-engineering/quality/gate-validation-status.md`; while
it is `unvalidated`, every `REQUIRED` above is capped at `RECOMMENDED`. Canonical
integrity findings (`INT-1`…`INT-9`) are never capped.

Mechanically-sourced severities are **fixed and may not be downgraded** by a
reviewing agent, consistent with `code-structure-quality.md`. A reviewer may
uphold a documented justification; it may not relabel an unresolved breach.

**A zero count earns no credit.** It establishes that this detector found nothing
— nothing more.

## Custody

Identical to `code-structure-quality.md`. Code Inspection executes the command on
every reviewed change and its run is authoritative. Programmer may run it as an
advisory preview and must never restate results as free text in a handoff; a
handoff asserting counts with no Code Inspection run behind it is a Required workflow
finding.

## Brownfield

First run records nothing and blocks nothing — the merge base supplies the
comparison. A repo with 4,000 existing `any`s blocks on number 4,001 only if the
change introduces it in a file it touched.

Enabling type-aware linting on a large legacy repo will surface a very large
number of pre-existing violations at once. That is a **strengthening**, it is
explicitly allowed, and it must not be reported as a regression. The correct
handling is: land the config change, treat the newly-visible set as the
grandfathered baseline via the merge base, and gate only what follows.

## Action-on-Fail

| Finding | Severity | Action |
|---|---|---|
| New Tier A occurrence, no upheld justification | Required | Code Inspection reports at fixed severity; **blocks only at `validated` gate status** (see the registry); otherwise routes to Programmer as `RECOMMENDED` |
| Strictness weakened without approval | Required | `INT-1`; blocks regardless of gate status; routes to Programmer and flags to the human |
| Suppression added over an existing violation | Required | `INT-4`; blocks regardless of gate status |
| New Tier B occurrence | Advisory | Recommended finding in the CR report |
| Slot declared but rules not type-aware | Required (workflow) | `INCONCLUSIVE`; fix the declaration before relying on the gate |
| Slot undeclared, or stack has no mapping | Advisory | Note absence in the CR report; gates are not enforced |

## Known Limitations

- **TypeScript-specific.** See Stack scope. Cross-stack parity is asserted by no
  one and should not be implied in a report.
- **Type-aware linting is slow.** On a large repo it can dominate PR time. The
  scoped-command form is not optional in practice, and a host may reasonably run
  the full pass only on the scheduled cadence.
- **Structural escapes are not covered.** `Function`, `object`, an index
  signature returning `any`, or a lying `.d.ts` declaration file all defeat the
  checker without producing a Tier A violation. This sensor counts named
  operations, not every route to unsoundness. A declaration file that asserts a
  shape the runtime does not have is the largest uncovered hole here and no
  listed tool finds it.
- **Export detection is host-specific.** The Tier A/B split for `any` depends on
  knowing whether a declaration is reachable from a public entry point. A simple
  `export` keyword check approximates this and will misclassify re-exports,
  barrel files, and package `exports` maps. Where the host cannot resolve public
  reachability, treat `any` in any `export`ed declaration as Tier A — the
  conservative direction.
- **Per-file activation is not proven by one global fixture.** The conformance
  run proves type-aware linting works *somewhere*. A per-file `eslint-disable`,
  an `ignorePatterns` entry, or a file excluded from the `tsconfig` `include` can
  still leave an individual changed file unlinted. Where the host supports it,
  inspect the effective config per changed file rather than trusting one global
  probe.
- **Unvalidated.** Like every gate in this harness, the tier assignments and
  dispositions are provisional until the eval runs.

## Related

- `<AI_DEV_SHOP_ROOT>/framework/contracts/computational-controls.md` — the `type_safety` slot
- `<AI_DEV_SHOP_ROOT>/harness-engineering/quality/coverage-integrity-policy.md` — the suppression and scope-narrowing rule this sensor applies to the type checker
- `code-structure-quality.md` — the custody and fixed-severity precedent
- `<AI_DEV_SHOP_ROOT>/skills/function-quality-assessment/references/finding-rubric.md` — dispositions
