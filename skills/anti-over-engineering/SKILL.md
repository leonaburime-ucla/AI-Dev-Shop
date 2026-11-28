---
name: anti-over-engineering
version: 1.0.0
last_updated: 2026-11-27
description: Use whenever writing, planning, extracting, fixing or reviewing code, to keep the change as small as the problem. It catches speculative abstraction, parallel mechanisms, unused options, wrapper layers, defensive code for impossible states, and test bloat, and it requires a net-lines check before finishing. Load it for every implementation, refactor, extraction, bug-fix and plan-review job.
---

# Skill: Anti-Over-Engineering

The owner's standing worry: **"we have a bunch of excess code."** Every change must leave the codebase the same size or smaller unless new behaviour truly needs new code. The best change is the smallest one that fully solves today's problem and passes the gates.

This skill sits on top of `coding-foundations` and `implementation-guardrails`; load them together.

## Not over-engineering (owner-mandated, keep doing these)
- Injecting host-specific dependencies as ports ("inject everything"), and passing custom hooks as props.
- The required-args object + `_optional = {}` pad convention. Never plan removing pads.
- Tests written first for behaviour and bugs. Small functions (<= 50 lines) and complexity <= 10.
These are the house style. The rules below are about everything else.

## The rules
1. **Solve the problem in front of you.** No "for later" options, flags, generics, plugin points or config keys that no caller uses today. If a second caller is real and named in the brief, fine; a guessed one is not.
2. **Reuse before you write.** Search for an existing function, port, store, route, helper or test fixture first (see `implementation-guardrails` → Before You Write). Extend it rather than add a parallel mechanism. Two ways to do one thing is a defect.
3. **No pass-through layers.** No wrapper that only forwards arguments, no re-export shell, no compatibility alias, no "manager"/"service"/"helper" class around one function, no interface with a single implementation unless it is an injected port the rules require.
4. **One generic parameter or abstraction must pay for itself.** It needs two real current users that differ. Otherwise write the concrete code.
5. **No defensive code for impossible states.** Validate at trust boundaries (user input, network, files, IPC, model output). Inside the typed core, trust the types: no re-checking what the caller already guaranteed, no try/catch that only re-throws or logs-and-continues.
6. **Delete as you go.** When you replace code, remove the old path, its tests, its exports, its docs and its config in the same change. Dead code, commented-out code and unused exports are bugs.
7. **Small diffs for bug fixes.** A bug fix is the failing test plus the minimal production change. No drive-by refactors, renames or "while I'm here" cleanups in the same change. Note them in the report instead.
8. **Tests prove behaviour, not lines.** One test per behaviour or branch; table-drive repeats. No tests of mocks, no snapshot dumps of whole objects, no copy-pasted fixtures when a shared builder exists. Coverage targets are met with meaningful assertions, not padding.
9. **Comments explain why, not what.** No restating the code, no banners, no changelog comments.
10. **Docs and plans stay short.** A plan lists the steps and files; it does not re-explain the codebase.

## Before you finish (mandatory)
- Run `git diff --stat` and report **net production lines** (added minus removed, excluding tests and docs).
- For each new file, function, type, option or export: name its caller. If you can't, delete it.
- For each new abstraction: name the two differing current users, or inline it.
- If net production lines went up, say in one line why the new behaviour needs them.
- In reviews, list every over-engineering finding with file:line and the smaller alternative.

## Red flags to search your own diff for
`Factory`, `Manager`, `Base`, `Abstract`, `Strategy` with one strategy, `options?.` branches nobody passes, `TODO: future`, `// for extensibility`, `export *` re-exports, new config keys, new packages, a second store/registry/router/logger for something that already has one, `as unknown as`, catch blocks without a recovery action.
