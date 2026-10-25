# Testability Anti-Patterns

Use this catalog when writing, rewriting, or reviewing code.

## Required Human Reporting Rule

If any anti-pattern below is found during implementation/refactor/review:

1. Log it in the current handoff summary.
2. Tell the human explicitly:
   - what anti-pattern was found,
   - where it appears,
   - why it hurts testability,
   - the recommended remediation route.

Do not silently proceed on repeat anti-patterns.

## Catalog

| Anti-Pattern | Why It Hurts Testing | Typical Remediation |
|---|---|---|
| Hidden global state and implicit singletons | Causes order-dependent and flaky tests | Inject dependencies; isolate state per test |
| Mixed concerns in one unit (I/O + domain logic + formatting) | Hard to unit-test behavior in isolation | Extract pure logic; isolate side-effect boundaries |
| Time/random/network directly called in core logic | Nondeterministic outputs | Use clock/RNG/network adapters and mocks at boundaries |
| Over-mocking implementation internals | Brittle tests tied to structure, not behavior | Assert observable outcomes; mock only external boundaries |
| Long methods with many branches and flags | Poor branch coverage and hard failure diagnosis | Split into small composable functions with explicit inputs |
| Feature logic embedded in framework lifecycle hooks only | Difficult targeted testing without full stack boot | Move logic into testable services/use-cases |
| Hard-coded environment paths/IDs/toggles | Tests fail across environments | Centralize config; pass via typed config objects |
| Shared mutable fixtures across tests | Test pollution and sequence coupling | Create fresh fixtures per test; remove shared mutability |
| Async fire-and-forget without observability hooks | Races and unassertable side effects | Return awaitable handles/events; expose completion signals |
| Dead defensive code paths without spec mapping | Coverage noise, unclear ownership | Remove or route to spec/refactor decision |
| Coverage suppression or source exclusion without an approved exception | Hides applicable runtime behavior and makes the coverage result untrustworthy | Restore coverage scope; test through a real seam or use the narrow exception contract |
| Capability removal disguised as coverage cleanup | Improves the percentage by weakening validation, compatibility, or recovery behavior | Restore behavior; route intentional contract changes through Spec/Architecture and Programmer |
| AP14 Invariant guarded only by a source-coupled test (source grep, file hash, comment assertion, child process) | Mutation and coverage tools cannot measure it: instrumentation breaks hash checks, child processes run uninstrumented code, and a grep passes on text that no longer behaves | Keep source scans and pins in a separate lint suite; give every invariant an in-process behavioural test; never let a child-process test be a module's only test; tests write only under a per-test temp dir |
| AP15 Dark files: production files no test imports | No test evidence at all, while an aggregate coverage gate can still pass | Every new source file lands with a test that imports it; enforce per-file coverage floors |
| Failure path around a hard-wired dependency (`catch {}`, fallback, fail-closed branch) | No test can make the dependency fail, so the branch never runs and emptying it goes unnoticed | Inject the dependency as a port so a test can supply a throwing fake |
| Security or policy defaults with no pinnable seam (buried inline, never exported) | A flipped default-deny value is caught only if some behavioural test happens to exercise that exact flag | Pin exported policy and default objects against the full literal; add one behavioural refusal per deny flag; introduce a testable seam (a named constant or resolver) where a default is buried |

The test-authoring rules that pair with these rows (throwing fakes, pinned
defaults, memoisation identity, and the rest) live in
`<AI_DEV_SHOP_ROOT>/skills/test-design/SKILL.md` § Mutation-Derived Input Rules.

Apply `<AI_DEV_SHOP_ROOT>/harness-engineering/quality/coverage-integrity-policy.md`
whenever a coverage gap or hard-to-test branch triggers implementation,
refactoring, or review work.

## Surface Template

Use this in handoffs/review notes:

```text
Testability Anti-Pattern Found
- Pattern: <name>
- Location: <file:line>
- Impact: <how this degrades test reliability/coverage>
- Recommended Route: <TDD | Refactor | Spec clarification>
```
