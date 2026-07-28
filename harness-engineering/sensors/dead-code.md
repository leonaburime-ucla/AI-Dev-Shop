# Sensor: Dead Code Detection

Finds unused exports, unreachable code, and orphaned files that accumulate as the codebase evolves.

## Sensor Definition

- **Class**: `computational`
- **Timing**: PR (incremental, modified-file scope) + scheduled (weekly, full repository)
- **Owner**: Observer → routes to Refactor agent
- **Artifact location**: `<ADS_MEMORY_ROOT>/.local-artifacts/sensors/dead-code-<timestamp>.md`

## Detector

The toolkit installs nothing. The host declares the command it uses, through an
existing slot such as `static_analysis`. If nothing is declared, this sensor is
`inactive`: report the absence, never a zero.

So the contract is a **capability**, not a tool:

> Declare a command that emits each unreferenced symbol or file with its
> **location**, computed over the full source root.

| Requirement | Why |
|---|---|
| Names and locates each finding | "12 unused symbols" routes to nobody |
| Analyses the full source root | reachability is a whole-program property; a scoped run reports entry points as dead |
| States how it treats dynamic references | reflection, string-keyed dispatch, DI containers and test-only usage are where this metric produces confident false positives |

**This sensor is advisory and gates nothing, deliberately.** Dead-code detection
has the highest false-positive cost of any metric here — its findings propose
deletions, and a wrong one removes working behaviour. Treat every finding as a
question, not an instruction.


## Action-on-Fail

| Context | Severity | Action |
|---------|----------|--------|
| PR — new dead code introduced by current change | Advisory | Warn Programmer in handoff; do not block |
| Scheduled — total dead code exceeds baseline by >20% | Escalation | Observer reports to user, recommends Refactor pass |
| Scheduled — critical-path module has dead branches | Escalation | Observer flags for review |

Dead code is never a hard blocker on its own — it's a quality signal, not a safety signal.

## Routing

1. **PR context**: Programmer receives advisory note before handoff. Code Inspection mentions it if the dead code is in modified files.
2. **Scheduled context**: Observer reads the weekly scan artifact. If findings exceed threshold:
   - Creates a maintenance entry in `<ADS_MEMORY_ROOT>/reports/maintenance/`
   - Routes to Refactor agent with specific file paths and dead-code evidence
   - Adds to `harness-engineering/maintenance/tech-debt-tracker.md`

## Baseline Management

First scan establishes a baseline count. Future scans are compared against baseline:
- Baseline increases only when new code is intentionally added
- Baseline decreases when cleanup is verified
- Threshold breach = baseline + 20% growth without corresponding new-feature justification

## What This Does NOT Cover

- Runtime dead code (code that executes but has no observable effect) — requires runtime instrumentation
- Feature flags that are "off" — those need product decision, not automated cleanup
