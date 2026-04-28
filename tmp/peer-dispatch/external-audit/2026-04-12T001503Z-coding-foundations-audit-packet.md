# External Audit Packet

## Ask

- **User request:** Have Claude audit the current skill-structure work.
- **Audit focus:** Review whether the new `coding-foundations` parent plus `implementation-guardrails` and `testable-design-patterns` children is the right structure, whether the file boundaries are coherent, and whether the agent wiring matches that structure without drift or contradiction.
- **Scope:** work-log
- **Audit target:** Explicit file set for the coding-foundations refactor and its wiring updates.
- **Authoring packet:** `.local-artifacts/external-audit/packets/2026-04-12T001503Z-coding-foundations-audit-packet.md`
- **Dispatch packet:** `tmp/peer-dispatch/external-audit/2026-04-12T001503Z-coding-foundations-audit-packet.md`

## Work Log

- Created a new tiny parent skill, `coding-foundations`, to hold only shared micro-level axioms: explicit dependencies, decision/effect separation, mutation-by-exception, stable contracts, fail-fast defaults, and small readable units.
- Slimmed `implementation-guardrails` into the complexity/style child so it now owns scaling sanity checks, selective complexity/query-shape notes, one-source-of-truth rules, boolean-flag avoidance, and non-obvious performance tradeoffs.
- Slimmed `testable-design-patterns` into the testability child so it now clearly sits on top of `coding-foundations`, not `implementation-guardrails`.
- Rewired agent skill lists and the shared skills registry so `coding-foundations` is explicit everywhere a child skill depends on it, and TDD no longer loads `implementation-guardrails`.
- Updated the React frontend skill to point at `coding-foundations` for the baseline and `testable-design-patterns` for stricter testability rules.
- Ran repo-local consistency searches and diff review only; no tests or runtime checks were run because this was skill/routing documentation work.

## Files And Artifacts

| Path | Why it matters |
|---|---|
| `skills/coding-foundations/SKILL.md` | New parent skill that defines the shared micro-level baseline. |
| `skills/coding-foundations/references/foundations-checklist.md` | Compact checklist for the shared parent defaults. |
| `skills/coding-foundations/references/purity-and-boundaries.md` | Parent reference for decision/effect separation and acceptable impurity. |
| `skills/implementation-guardrails/SKILL.md` | Child skill now scoped to complexity/scaling/style guardrails. |
| `skills/implementation-guardrails/references/complexity-comments.md` | Existing reference that still defines when complexity/query-shape comments belong. |
| `skills/implementation-guardrails/references/defaults-checklist.md` | Child reference now narrowed to implementation guardrails after the parent extraction. |
| `skills/testable-design-patterns/SKILL.md` | Child skill now scoped to seams, contracts, and coverage-friendly structure on top of the parent. |
| `agents/programmer/skills.md` | Programmer wiring now loads parent plus both children. |
| `agents/architect/skills.md` | Architect wiring and workflow now reference the parent plus relevant children. |
| `agents/code-review/skills.md` | Code Review wiring now loads parent plus both children. |
| `agents/tdd/skills.md` | TDD wiring now loads parent plus `testable-design-patterns`, and no longer loads `implementation-guardrails`. |
| `agents/refactor/skills.md` | Refactor wiring now loads parent plus both children. |
| `framework/routing/skills-registry.md` | Shared registry now documents the parent-child structure and agent ownership. |
| `skills/frontend-react-orcbash/SKILL.md` | Cross-skill reference surface updated to use the parent for the baseline. |

## Validation

- **Checks run:** `git status --short`; bounded `git diff` review for the files above; `rg` consistency searches for `coding-foundations`, `implementation-guardrails`, and `testable-design-patterns`; manual read-through of the changed skill files and agent wiring files.
- **Checks not run:** No tests; no slash-command smoke tests; no runtime load verification for the new skill stack.
- **Known caveats:** This is documentation/routing work only. The `skills/coding-foundations/` directory and the `skills/implementation-guardrails/` directory are currently untracked in git. There is also an unrelated modified file, `skills/code-review/SKILL.md`, in the worktree that is excluded from this audit packet.

## Out-Of-Scope Local Changes

- `skills/code-review/SKILL.md` — modified in the worktree from earlier style-review changes, but not part of the coding-foundations refactor under audit.
- `.github/` — unrelated untracked local content.
- `.local-artifacts/` outside this packet/offload workflow — local scratch artifacts excluded from the audit scope.
- `programmer-subagents.png` — unrelated untracked asset.

## Open Questions

- Is `coding-foundations` small and stable enough, or does it still contain material that belongs in a child?
- Are the child boundaries clean, or is any rule still in the wrong file?
- Is the current agent wiring the right stack, especially for `Architect`, `TDD`, and `Refactor`?
- Is there any drift/conflict risk left in the new structure or in cross-skill references such as `frontend-react-orcbash`?

## Auditor Instructions

Please review this work independently. Use the Ask section's `Audit target` and `Dispatch packet` fields as the source of truth for what to inspect and which packet path was actually handed to you.

Return:

1. Start with an `Auditor Scope Check` that restates what you believe you are auditing, the active scope and audit target, which files or artifacts you actually reviewed, and any ambiguity or mismatch you noticed
2. Findings ordered by severity
3. File references when possible
4. Which changes are blockers vs optional improvements
5. What looks solid and should probably stay unchanged
