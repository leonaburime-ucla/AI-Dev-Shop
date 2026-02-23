> WARNING: LEGACY/DEPRECATED IN STRICT MODE
> This single-file template is the legacy format. In strict mode, use the full spec package under templates/spec-system/ instead.
> This file is retained for backward compatibility only. New specs must use the spec-system package.

# Spec: <feature-name>

- Spec ID: SPEC-<id>
- Feature: FEAT-<scan existing specs in AI-Dev-Shop/specs/ for next available number — 001, 002, 003, ...>
- Version: <semver — major for scope changes, minor for clarifications>
- Last Edited: <ISO-8601 UTC>
- Content Hash: <sha256 of content below the header metadata block>
- Owner: <human>

> **[NEEDS CLARIFICATION] vs Open Questions — use the right one:**
>
> **`[NEEDS CLARIFICATION]`** — inline marker for a requirement that is too ambiguous to be testable as written. Blocks Architect dispatch. Must be resolved (replaced with the actual decision) or escalated to human before the spec can advance. Use this when the ambiguity is in the requirement text itself.
> Example: `The user can export results [NEEDS CLARIFICATION: CSV only, or also PDF and JSON?]`
>
> **Open Questions** — tracked questions that do not block Architect dispatch. They have a known owner and a resolution target date. Use this for decisions that are not needed yet (e.g., "Which analytics provider to use — owner: PM — resolve by 2026-03-01").
>
> Zero unresolved `[NEEDS CLARIFICATION]` markers is a hard gate. Open Questions with no owner or date should be converted to `[NEEDS CLARIFICATION]` markers.

## Problem

What problem are we solving and for whom? One to three sentences.

## Scope

**In scope:**
- <explicit list of what this spec covers>

**Out of scope:**
- <explicit list of what this spec does not cover — prevents scope creep>

## Requirements

Numbered. Observable. Testable. No vague qualifiers ("fast", "robust", "intuitive").

- REQ-01: <requirement>
- REQ-02: <requirement>

## Acceptance Criteria

One or more per requirement. Format: `Given / When / Then` or a plain testable statement.

Priority: **P1** = must-have (blocks shipping), **P2** = should-have (high value), **P3** = nice-to-have (can defer).

- AC-01 (REQ-01) [P1]: Given <precondition>, when <action>, then <observable outcome>.
- AC-02 (REQ-01) [P1]: <alternate criteria for same requirement if needed>
- AC-03 (REQ-02) [P2]: ...

## Invariants

Conditions that must always hold regardless of input or state. These become assertion sets in tests.

- INV-01: <condition that must never be violated>
- INV-02: ...

## Edge Cases

Concrete scenarios, not categories. "What happens when X?" not "Handle edge cases."

- EC-01: What happens when <specific scenario>?
- EC-02: What happens when <specific scenario>?

## Dependencies

External systems, APIs, or services this spec relies on.

- <dependency and what it provides>

## Open Questions

Questions that do not block Architect dispatch but need resolution before TDD begins. Each must have an owner and a target resolution date. Questions without an owner or date are not Open Questions — convert them to `[NEEDS CLARIFICATION]` markers in the relevant requirement.

- OQ-01: <question — owner — target resolution date>

## Constitution Compliance

Completed by the Spec Agent. Verified by the Architect Agent.

| Article | Status | Notes |
|---------|--------|-------|
| I — Library-First | COMPLIES / EXCEPTION / N/A | |
| II — Test-First | COMPLIES / EXCEPTION / N/A | |
| III — Simplicity Gate | COMPLIES / EXCEPTION / N/A | |
| IV — Anti-Abstraction Gate | COMPLIES / EXCEPTION / N/A | |
| V — Integration-First Testing | COMPLIES / EXCEPTION / N/A | |
| VI — Security-by-Default | COMPLIES / EXCEPTION / N/A | |
| VII — Spec Integrity | COMPLIES / EXCEPTION / N/A | |
| VIII — Observability | COMPLIES / EXCEPTION / N/A | |

Any EXCEPTION requires a justification row in the ADR's Complexity Justification table.

## Agent Directives (optional)

Task-specific boundary rules that override or supplement global AGENTS.md rules for this spec only.

✅ Always:
- <specific constraint for this task>

⚠️ Ask before:
- <high-impact action requiring human confirmation>

🚫 Never:
- <hard stop specific to this task>
