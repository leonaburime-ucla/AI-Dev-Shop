---
name: spec-writing
version: 1.0.0
last_updated: 2026-02-22
description: Use when writing or reviewing specifications, converting product intent into testable requirements, versioning and hashing specs, or structuring acceptance criteria and edge cases.
---

# Skill: Spec Writing

Specs are ground truth. Every downstream agent — Architect, TDD, Programmer, Code Review, Security — builds on what the spec says. If the spec is wrong or vague, every agent executes confidently on a flawed foundation and produces passing tests for the wrong behavior. This is the most dangerous failure mode in a multi-agent system.

## What a Spec Is

A spec converts fuzzy product intent into precise, versioned, testable statements. It answers:
- What problem are we solving?
- What does done look like, in observable terms?
- What is explicitly out of scope?
- What are the hard constraints?
- What are the edge cases?

A spec is not implementation guidance. It does not say how to build something — only what the system must do and prove.

## Spec Anatomy

Every spec must include:

**Header Metadata**
```
Spec ID:      SPEC-001
Version:      1.2
Last Edited:  2026-02-21T14:00:00Z
Hash:         sha256:<hash of canonical content>
```

The hash is a fingerprint of the spec's exact content. It gives the TDD Agent and CI system certainty that a test was written against this exact version, not a silently edited one.

**Goals**
One to three sentences. What problem does this solve and for whom?

**Scope**
- In scope: explicit list of what this spec covers
- Out of scope: explicit list of what it does not cover — this prevents scope creep and ambiguity

**Requirements**
Numbered. Observable. Testable. No vague language.

Bad: "The system should be fast and handle errors gracefully."
Good:
- REQ-01: The invoice creation endpoint must return a response within 500ms at p99 under 100 concurrent requests.
- REQ-02: If the customer ID does not exist, the API must return HTTP 422 with error code `CUSTOMER_NOT_FOUND`.

**Acceptance Criteria**
One or more per requirement. Format: Given / When / Then or plain testable statement.

- AC-01 (REQ-01): Given 100 concurrent POST /invoices requests, when measured over 60 seconds, then p99 latency ≤ 500ms.
- AC-02 (REQ-02): Given a POST /invoices with customerId "nonexistent-id", when the request is processed, then response is 422 with body `{"error": "CUSTOMER_NOT_FOUND"}`.

**Invariants**
Conditions that must always hold, regardless of input or state. These become assertion sets in tests.

- INV-01: Invoice total must always equal sum of line item subtotals.
- INV-02: An invoice in status "paid" must never transition back to "pending".

**Edge Cases**
Concrete scenarios, not categories. "What happens when X?" not "Handle edge cases."

- EC-01: What happens when a line item has quantity 0?
- EC-02: What happens when the same invoice is submitted twice with identical idempotency key?
- EC-03: What happens when currency conversion rate is unavailable at invoice creation time?

**Dependencies**
External systems, APIs, or services this spec relies on.

**Open Questions**
Unresolved ambiguities that require human decision before TDD can proceed.

## Versioning and Hashing

Every time the spec changes:
1. Increment version (semantic: major for scope changes, minor for clarifications)
2. Update Last Edited timestamp (ISO-8601 UTC)
3. Recompute hash from canonical content

The hash is what the TDD Agent binds tests to. If the spec changes and the hash changes, all tests certified against the old hash are automatically flagged as stale by CI. This is the drift detection mechanism.

Canonical content for hashing: strip the metadata header, normalize whitespace, hash the rest.

## Code Examples Over Prose

For requirements involving interfaces, data shapes, or API contracts, a single code example communicates more precisely than paragraphs of description — and leaves less room for agent misinterpretation.

**Without example (ambiguous):**
> REQ-04: The invoice creation endpoint must accept a list of line items, each with a product ID, quantity, and unit price.

**With example (precise):**
> REQ-04: The invoice creation endpoint must accept a request body matching this shape:
> ```typescript
> interface CreateInvoiceRequest {
>   customerId: string;
>   lineItems: Array<{
>     productId: string;
>     quantity: number;        // must be > 0
>     unitPriceInCents: number; // must be > 0
>   }>;
>   idempotencyKey: string;
> }
> ```

Include code examples when: the requirement defines an interface, a response shape, an event structure, a state machine, or any data contract. Skip them when a plain English requirement is unambiguous.

## Agent Directives (Optional)

For complex tasks, include task-specific agent boundary rules directly in the spec. These are different from global rules in AGENTS.md — they apply only to this spec.

```
## Agent Directives

✅ Always:
- Return errors using the standard envelope format from ADR-001: `{ "error": { "code": "...", "message": "..." } }`
- Use the existing CustomerRepository interface — do not add direct database queries

⚠️ Ask before:
- Adding new database columns (requires migration coordination)
- Changing the InvoiceCreated event shape (downstream consumers depend on it)

🚫 Never:
- Implement currency conversion in this feature — out of scope (EC-03)
- Send emails directly — use the NotificationService interface only
```

Use this section when the task has high-risk boundaries that aren't covered by the architecture ADR alone.

## Large Spec Strategy

For features that touch multiple domains or services, split into sub-specs rather than writing one long spec:

- `SPEC-012a`: Invoice creation (this service's behavior)
- `SPEC-012b`: Payment processing integration (the boundary contract)
- `SPEC-012c`: Email notification side effect

Each sub-spec gets its own hash and can be run through TDD independently. The parent spec references child IDs. This keeps individual specs focused and prevents attention degradation in the agents reading them.

## Quality Standards

A spec is ready when:
- Every requirement is observable (can be measured or verified)
- Every requirement has at least one acceptance criterion
- No acceptance criterion contains vague qualifiers ("fast", "robust", "intuitive", "appropriate")
- Invariants are explicit and minimal (only include what must never be violated)
- Edge cases are concrete scenarios, not categories
- Out-of-scope items are listed
- Open questions are listed (not silently assumed away)
- Metadata is complete and hash is current
- Code examples included for all interface and data shape requirements

## Common Failure Modes

**Vague language**: "The system should handle errors gracefully" — unverifiable. Replace with specific error codes, response shapes, and recovery behavior.

**Hidden assumptions**: "Obviously the user will be authenticated" — write it down. TDD and Programmer agents do not share your implicit knowledge.

**Missing scope boundaries**: Not stating what's out of scope invites agents to implement things you didn't want.

**Spec change without hash update**: The most dangerous failure. Tests keep passing against the old spec while the implementation drifts. Always recompute the hash.

**Narrative fluff**: Long prose paragraphs explaining context belong in project_notes.md. The spec should be dense with requirements, not background.

**Interface described in prose**: Any requirement describing a data shape, API contract, or interface that could be expressed as a TypeScript interface or JSON example should be. Prose descriptions generate more interpretation variance across agents.

## What Belongs Where

| Content | Location |
|---|---|
| Requirements, acceptance criteria, invariants, edge cases | Spec file |
| Architecture decisions and pattern choices | ADR in `AI-Dev-Shop/specs/` — see `AI-Dev-Shop/skills/architecture-decisions/SKILL.md` |
| Project conventions and tribal knowledge | `AI-Dev-Shop/project-knowledge/project_memory.md` |
| Lessons learned from past mistakes | `AI-Dev-Shop/project-knowledge/learnings.md` |
| Open questions and parking lot items | `AI-Dev-Shop/project-knowledge/project_notes.md` |

## Spec Change Protocol

When requirements change mid-development:
1. Update the spec with new version and hash
2. Notify Coordinator
3. Coordinator routes back to TDD Agent to recertify tests against new hash
4. Programmer Agent is not dispatched until tests are recertified
5. CI must validate hash alignment before any merge

Human review is required at spec approval and at any major scope change.
