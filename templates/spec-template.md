# Spec: <feature-name>

- Spec ID: SPEC-<id>
- Version: <semver — major for scope changes, minor for clarifications>
- Last Edited: <ISO-8601 UTC>
- Content Hash: <sha256 of content below the header metadata block>
- Owner: <human>

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

- AC-01 (REQ-01): Given <precondition>, when <action>, then <observable outcome>.
- AC-02 (REQ-01): <alternate criteria for same requirement if needed>
- AC-03 (REQ-02): ...

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

Unresolved ambiguities requiring human decision before TDD can proceed.

- OQ-01: <question — owner — target resolution date>

## Agent Directives (optional)

Task-specific boundary rules that override or supplement global AGENTS.md rules for this spec only.

✅ Always:
- <specific constraint for this task>

⚠️ Ask before:
- <high-impact action requiring human confirmation>

🚫 Never:
- <hard stop specific to this task>
