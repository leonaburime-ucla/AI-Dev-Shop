# Memory Schema

Defines the entry format for `project-knowledge/memory-store.md`. The Observer writes entries here. The Coordinator and other agents read entries when relevant context is needed.

All entries are append-only. Never edit or delete past entries — add a correction entry instead.

---

## Entry Types

### DECISION
A significant choice made during the pipeline: architecture, technology, spec direction, process.

```markdown
---
## [DECISION] <short title>

- entry_id: DECISION-<YYYYMMDD>-<NNN>
- date: <ISO-8601 UTC>
- supersedes: <entry_id> | N/A
- expires_at: never | <ISO-8601 UTC>
- feature: <NNN-feature-name> | project-wide
- spec: <SPEC-NNN vX (hash)> | N/A
- category: architecture | technology | spec | process
- decision: <one sentence — what was decided>
- rationale: <why this and not the alternative>
- tags: #<tag1> #<tag2>
```

**Example:**
```markdown
---
## [DECISION] Use Stripe for payment processing

- entry_id: DECISION-20260222-001
- date: 2026-02-22T14:00:00Z
- supersedes: N/A
- expires_at: never
- feature: 003-checkout
- spec: SPEC-003 v1 (hash: abc123)
- category: technology
- decision: Stripe selected over Braintree for payment processing
- rationale: Existing team familiarity, better webhook reliability, no PCI scope expansion
- tags: #payment #stripe #technology
```

---

### FAILURE
A recurring failure cluster, an escalation, or a resolved blocker worth remembering.

```markdown
---
## [FAILURE] <short title>

- entry_id: FAILURE-<YYYYMMDD>-<NNN>
- date: <ISO-8601 UTC>
- supersedes: <entry_id> | N/A
- expires_at: never | <ISO-8601 UTC>
- feature: <NNN-feature-name>
- stage: spec | architect | tdd | programmer | testrunner | code-review | security
- cluster: <AC ID or description>
- occurrences: <n>
- resolved_by: <agent or human> on <date>
- root_cause: <one sentence>
- resolution: <what actually fixed it>
- tags: #<tag1> #<tag2>
```

**Example:**
```markdown
---
## [FAILURE] Timeout edge case in payment retry logic

- entry_id: FAILURE-20260222-001
- date: 2026-02-22T16:30:00Z
- supersedes: N/A
- expires_at: never
- feature: 003-checkout
- stage: programmer
- cluster: AC-07
- occurrences: 3
- resolved_by: Programmer Agent on 2026-02-22T17:00:00Z
- root_cause: Spec AC-07 did not define behavior when payment gateway times out after partial charge
- resolution: Spec revised to add idempotency key requirement; Programmer implemented retry with key check
- tags: #payment #timeout #idempotency #spec-gap
```

---

### FACT
Project-specific knowledge: gotchas, conventions, constraints, integration quirks. Replaces free-form `project_memory.md` entries.

```markdown
---
## [FACT] <short title>

- entry_id: FACT-<YYYYMMDD>-<NNN>
- date: <ISO-8601 UTC>
- supersedes: <entry_id> | N/A
- expires_at: never | <ISO-8601 UTC>
- category: gotcha | convention | constraint | integration | security
- source: <who observed this — agent name, human, or external>
- content: <the fact, as specific as possible>
- tags: #<tag1> #<tag2>
```

**Example:**
```markdown
---
## [FACT] Legacy billing API requires X-Client-Version header

- entry_id: FACT-20260222-001
- date: 2026-02-22T10:00:00Z
- supersedes: N/A
- expires_at: never
- category: integration
- source: Programmer Agent (discovered during 003-checkout implementation)
- content: The legacy billing API at /api/v1/charge returns 400 without X-Client-Version: 2 header. Not documented. Every call must include this header or it silently fails.
- tags: #billing #legacy-api #header #gotcha
```

---

### QUALITY
Agent output quality score from an LLM-as-judge pass. Used by the Observer to track improvement trends. (Populated once LLM-as-judge evals are implemented.)

```markdown
---
## [QUALITY] <agent> output for <feature>

- entry_id: QUALITY-<YYYYMMDD>-<NNN>
- date: <ISO-8601 UTC>
- supersedes: <entry_id> | N/A
- expires_at: never | <ISO-8601 UTC>
- feature: <NNN-feature-name>
- agent: spec | architect | tdd | programmer | code-review | security
- spec_hash: <sha256>
- scores:
  - <dimension 1>: <score>/10
  - <dimension 2>: <score>/10
- overall: <score>/10
- notes: <what dragged the score down, if anything>
- tags: #quality #<agent-name>
```

---

## Tagging Conventions

Use lowercase, hyphenated tags with `#` prefix. Suggested tags:

| Tag | When to use |
|-----|------------|
| `#spec-gap` | Failure root-caused to missing or ambiguous spec |
| `#gotcha` | Non-obvious behavior that bit the pipeline |
| `#legacy-api` | Integration with existing systems |
| `#security` | Security-related fact or decision |
| `#timeout` | Timeout, retry, or async edge case |
| `#performance` | Latency or throughput concern |
| `#architecture` | Structural/pattern decision |
| `#technology` | Library or tool selection |
| `#process` | Pipeline process change |
| `#constitution` | Constitution compliance note |

---

## How the Observer Uses This File

**Writing:**
- After each pipeline cycle, scan for new FAILURE or DECISION events worth recording
- Write new entries at the bottom of `memory-store.md`
- Never edit past entries — append a correction entry if needed

**Reading (before producing recommendations):**
- Scan for FAILURE entries with matching tags to the current failure cluster
- Scan for FACT entries with tags matching the current feature domain
- Surface relevant past entries to the Coordinator as context before re-dispatching

**Weekly pattern report:**
- Count FAILURE entries by tag to identify recurring problem areas
- Count QUALITY entries by agent to identify degrading output quality
- Flag any FACT entries that should be promoted to agent skills.md files

---

## Migration from Legacy Files

`project_memory.md` and `learnings.md` contain valuable knowledge in free-form format. Migrate entries over time:

1. For each entry in `project_memory.md`: create a `[FACT]` entry in `memory-store.md` with appropriate category and tags
2. For each entry in `learnings.md`: create a `[FAILURE]` entry with root_cause and resolution if known
3. Do not delete `project_memory.md` or `learnings.md` until fully migrated — they remain valid fallback context
