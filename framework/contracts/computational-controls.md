# Computational Controls Contract

Host projects declare their executable quality checks here so agents can run them without guessing.

## Host Declaration Location

`<ADS_PROJECT_KNOWLEDGE_ROOT>/governance/contracts/computational-controls.md`

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

### static_analysis

- **Command**: e.g., `npm run analyze`, `semgrep --config=auto`
- **Working directory**: project root unless specified
- **Required**: yes/no
- **Blocking**: yes/no
- **Timeout**: default 300
- **Success criteria**: exit code 0

## When Agents Execute These Slots

| Stage | Slots used |
|-------|-----------|
| Programmer (during implementation) | lint, typecheck, build, unit_tests |
| Programmer (before handoff) | all declared slots |
| TestRunner | unit_tests, integration_tests |
| Code Review | lint, typecheck, static_analysis |

## Behavior When Contract Is Missing

See [enforcement.md](enforcement.md) for the full enforcement model. Summary:

- **Greenfield project**: Coordinator warns at pipeline start. Programmer stage is blocked until at least `build` and one test slot are declared.
- **Brownfield project**: Advisory mode. Coordinator logs that the contract is absent. Agents proceed but handoffs note that no executable controls were verified.

## Behavior When a Check Fails

- **Blocking slot fails**: the stage cannot hand off. The agent must attempt one fix cycle, then report failure.
- **Non-blocking slot fails**: the failure is reported in the handoff summary. Downstream stages are informed. Pipeline continues.

## Behavior When a Slot Is Declared but Empty

A slot declared as required but with no command means the host acknowledges the gap. The Coordinator treats this as a known gap and reports it at pipeline start. It does not block unless enforcement is set to strict.

## Monorepo Support

For monorepos with multiple packages, declare slots per package scope:

- Use a separate command slot entry per package, or
- Use a root-level command that handles routing internally (e.g., `turbo run lint`)
- Specify the working directory for each slot when it differs from project root
