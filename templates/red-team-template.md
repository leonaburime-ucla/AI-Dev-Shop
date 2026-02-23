# Red-Team Findings: <feature-name>

- Feature: <feature name>
- Spec version: <version>
- Spec hash: sha256:<hash>
- Red-Team completed: <ISO-8601 UTC>
- Finding count: <N> BLOCKING · <N> ADVISORY

---

## BLOCKING Findings

Spec must be revised before Architect dispatch. If 3 or more BLOCKING findings exist, stop and route back to Spec Agent.

### RT-001
- Severity: BLOCKING
- Category: ambiguity | contradiction | untestable | missing-failure-mode | scope-creep
- Location: <AC ID or section reference>
- Description: <what the problem is>
- Suggested resolution: <what the spec should say to fix it>

---

## ADVISORY Findings

Spec Agent and human are informed. Human decides whether to revise or accept risk. Pipeline can advance if no BLOCKING findings remain.

### RT-002
- Severity: ADVISORY
- Category: ambiguity | contradiction | untestable | missing-failure-mode | scope-creep
- Location: <AC ID or section reference>
- Description: <what the problem is>
- Suggested resolution: <what the spec should say, or why this is acceptable risk>

---

## Routing Decision

`<N>` BLOCKING findings. `<decision: spec cleared for Architect dispatch / route back to Spec Agent>`

ADVISORY findings are included in Architect context. `<specific notes if any>`
