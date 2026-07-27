# Drift Sensors — Phase 1

Recurring codebase-health signals with clear ownership, artifact output, and routing into maintenance flows.

## What a Drift Sensor Is

A scheduled or event-driven check that measures codebase health decay over time. Unlike one-shot validators that check a single commit, sensors track trends and trigger action when drift crosses thresholds.

## Sensor Taxonomy

| Class | Meaning | Example |
|-------|---------|---------|
| `computational` | Deterministic tool output, exit code or structured report | `npm audit`, coverage diff |
| `inferential` | LLM-assisted analysis of patterns that tools can't catch alone | critical-path coverage judgment |

## Phase 1 Sensors

| Sensor | Class | Timing | Owner | File |
|--------|-------|--------|-------|------|
| [Dead Code](dead-code.md) | computational | PR + scheduled | Observer → Refactor | `dead-code.md` |
| [Dependency Drift](dependency-drift.md) | computational | daily + lockfile change | Observer → Security/DevOps | `dependency-drift.md` |
| [Coverage Quality](coverage-quality.md) | computational + inferential | PR + scheduled | Observer → TDD/Programmer | `coverage-quality.md` |
| [Mutation Quality](mutation-quality.md) | computational | PR (conditional) + scheduled | TestRunner PR gate; Observer scheduled trends → TDD/Programmer | `mutation-quality.md` |
| [Code Structure Quality](code-structure-quality.md) | computational | PR (every change) + scheduled | Code Review PR gate; Observer scheduled trends → Refactor/Programmer | `code-structure-quality.md` |
| [Dependency Structure](dependency-structure.md) | computational | PR (changed modules) + scheduled (full graph) | Code Review PR gate; Observer scheduled trends → Software Architect | `dependency-structure.md` |
| [Changed-Code Coverage](changed-code-coverage.md) | computational | PR only | TestRunner produces the report; Code Review computes and gates | `changed-code-coverage.md` |
| [Type Safety](type-safety.md) | computational | PR (changed files) + scheduled | Code Review PR gate; Observer scheduled trends → Programmer/Refactor | `type-safety.md` |
| [Duplication](duplication.md) | computational | PR (changed files) + scheduled | Code Review PR gate; Observer scheduled trends → Refactor | `duplication.md` |
| [Change History](change-history.md) | computational | scheduled only — never a PR gate | Observer → Refactor + human prioritization | `change-history.md` |

## Which sensors can block

**None of the gates added by the code-quality metrics program currently block.**
Every one is `unvalidated` in
`<AI_DEV_SHOP_ROOT>/harness-engineering/quality/gate-validation-status.md`, which
caps their `REQUIRED` dispositions at `RECOMMENDED` until an eval runs and the
(still undefined) ablation canary is specified.

What does still block: the canonical integrity findings `INT-1`…`INT-9` in that
file, and the two pre-existing legacy gates (mutation regression, suite
coverage). Wording in this catalog that says a sensor "gates" describes what it
evaluates, not that it currently stops a pipeline. Read the registry before
treating any mechanical finding as blocking.

## Standard Artifact Location

Sensor outputs are stored at:
`<ADS_MEMORY_ROOT>/.local-artifacts/sensors/<sensor-name>[-<feature-id>]-<timestamp>.{json|md}`

Promoted findings (those that trigger action) are copied to:
`<ADS_MEMORY_ROOT>/reports/maintenance/sensors/<sensor-name>[-<feature-id>]-<timestamp>.{json|md}`

Two shapes, and the sensor doc is authoritative for which one applies:

- **PR-context sensors** (`code-structure-quality`, `dependency-structure`,
  `type-safety`, `duplication`, `changed-code-coverage`) emit **JSON** and carry a
  `<feature-id>` — their output is machine-parsed by Code Review and scoped to one
  change.
- **Scheduled-only sensors** (`change-history`, `dead-code`, `dependency-drift`,
  `coverage-quality`) emit the older `.md` trend shape with no feature id.

Each sensor's own **Artifact** field states its exact path. Do not infer the
shape from this section — an earlier version documented only the `.md` form,
which sent anyone following it to write artifacts the consumers would not find.

## Standard Routing Protocol

1. Sensor runs (on schedule or event trigger)
2. Writes artifact to `.local-artifacts/sensors/`
3. Observer reads artifact during its next pass (or immediately if sensor triggers escalation)
4. Observer classifies findings and routes to the appropriate agent
5. Receiving agent acts (refactor, patch, add tests) or the finding is added to `tech-debt-tracker.md`

### Documented exceptions to Observer-only routing

Seven sensors do not route through Observer in PR context. Each exception is deliberate and stated here so the pattern above is not silently violated.

| Sensor | PR context | Scheduled context | Why the exception |
|--------|-----------|-------------------|-------------------|
| Code Structure Quality | **Code Review** executes and gates inline | Observer owns trends → Refactor/Programmer | The measured party must not author the measurement; Code Review already executes `static_analysis` per the computational-controls execution table |
| Dependency Structure | **Code Review** executes and evaluates inline | Observer owns full-graph trends → Software Architect | Same custody rule, same slot owner; a cycle introduced by a diff belongs to that diff, not to a later scheduled pass |
| Type Safety | **Code Review** executes and gates inline | Observer owns whole-repo trends → Programmer/Refactor | Same custody rule, same slot owner; strictness weakening must block the diff that introduces it |
| Duplication | **Code Review** executes and gates inline | Observer owns whole-repo trends → Refactor | Same custody rule; Code Review is also the adjudicator when this gate conflicts with the complexity gates |
| Changed-Code Coverage | **split**: TestRunner emits the raw report, **Code Review** computes and gates | none — "changed code" is undefined outside a change | The expensive half (running the suite) is TestRunner's; the cheap half (attributing it to the diff) is recomputed by the consumer, preserving the custody rule where cost allows |
| Mutation Quality | **TestRunner** owns and gates inline | Observer owns full-scope trends → TDD/Programmer | Mutation runs are expensive and sequenced off the test run TestRunner already owns |
| Change History | **never runs in PR context** | Observer owns entirely → Refactor + human | Churn is a signal about where to look, not about whether a diff is acceptable; gating on it would punish work in the areas that most need it |

## What Is NOT in Phase 1

- Runtime SLO monitoring
- Log anomaly detection
- Broader observability signals
- Performance profiling

These may come in later phases with explicit promotion.
