# Sensor: Coverage Quality Analysis

Tracks test coverage trends, identifies critical-path gaps, and detects coverage decay over time. Goes beyond raw percentage to assess whether the right things are tested.

## Sensor Definition

- **Class**: `computational` (coverage numbers) + `inferential` (critical-path judgment)
- **Timing**: PR (coverage diff) + scheduled (weekly trend analysis)
- **Owner**: Observer → routes to TDD agent or Programmer
- **Artifact location**: `<ADS_MEMORY_ROOT>/.local-artifacts/sensors/coverage-quality-<timestamp>.md`

## Detector

The toolkit installs nothing. The host declares the command it already uses to
produce a coverage report — through an existing slot such as `static_analysis`,
or alongside its test slots. If nothing is declared, this sensor is `inactive`:
report the absence, never a zero.

So the contract is a **capability**, not a tool:

> Declare a command that emits a **per-file** coverage report in a documented
> format, over the whole project rather than a selected subset.

| Requirement | Why |
|---|---|
| Per-file records, not a single project total | a project percentage cannot locate anything, and is the form of this metric most easily moved by adding or removing files |
| Covers the whole project | a report over a subset reads as full coverage of a small codebase |
| States whether branch recording was enabled | branch recording is usually opt-in; a report without it looks identical to code with no branches |

This sensor is advisory and gates nothing. Its numbers are context for the gated
coverage sensor, not a substitute for it.

## What This Sensor Measures

### Computational (tool-derived)
- Overall line/branch/function coverage percentage
- Coverage delta on modified files (did coverage go up or down with this change?)
- Uncovered files count (files with 0% coverage)
- Coverage per module/package

### Inferential (LLM-assisted, scheduled only)
- Are critical paths covered? (auth flows, payment paths, data mutations)
- Are edge cases tested or only happy paths?
- Does coverage correlate with complexity? (high-complexity files should have higher coverage)

## Action-on-Fail

| Finding | Severity | Action |
|---------|----------|--------|
| PR drops overall coverage by >5% | Escalation | Code Review flags; Programmer asked to add tests |
| PR drops coverage on modified files specifically | Advisory | Noted in handoff summary |
| Critical-path module has <50% coverage | Escalation | Observer reports; TDD agent recommended |
| Zero-coverage file is modified | Advisory | Programmer reminded to add test |
| Weekly trend shows 3+ consecutive weeks of decline | Escalation | Observer reports systemic test debt |

Coverage alone is never a hard blocker — it's an escalation or advisory signal. The quality of tests matters more than the number.

## Routing

1. **PR context**:
   - Coverage diff computed against base branch
   - Results included in Code Review context
   - Significant drops flagged to Programmer before handoff

2. **Scheduled context**:
   - Observer reads weekly trend artifact
   - If sustained decline or critical-path gaps detected:
     - Creates maintenance entry
     - Routes to TDD agent for test-plan recommendations
     - Adds to `harness-engineering/maintenance/tech-debt-tracker.md`

3. **Inferential analysis** (scheduled only, not PR):
   - Observer applies critical-path judgment to identify high-risk uncovered areas
   - Produces a ranked list of "most dangerous coverage gaps"
   - Routes to user for prioritization (not auto-assigned)

## Baseline Management

- First coverage report establishes the baseline
- Target: coverage should not decrease without justification
- Justified decreases: removing dead tests, removing dead code (coverage denominator changes)
- Unjustified decreases: new code without tests, test deletions without replacement

## What This Does NOT Cover

- Test quality (a test that asserts nothing still counts as "covered") — see `mutation-quality.md` for fault-injection grading of test effectiveness
- Integration/E2E coverage (only unit-level coverage tooling in phase 1)
- Performance test coverage

## Related Sensors

- **Mutation Quality** (`harness-engineering/sensors/mutation-quality.md`): answers "would tests catch a bug on covered lines?" — complementary to this sensor's "what lines do tests execute?" A file can have 100% coverage and 30% mutation score when tests execute code but never assert on results.
