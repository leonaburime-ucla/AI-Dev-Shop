# Agent Handoff

Every agent output must include this block. The Coordinator validates it before advancing the pipeline. A missing or incomplete handoff is treated as an incomplete stage — the Coordinator re-dispatches the agent.

---

## Handoff: <Agent Name> → <Next Stage>

- Agent: <agent name>
- Stage: <pipeline stage — e.g., `tdd`, `programmer`, `code-review`>
- Feature: <feature name>
- Completed At: <ISO-8601 UTC>

---

### Inputs Used

List every artifact this agent read and acted on. Include version or hash where applicable.

| Artifact | Version / Hash | Notes |
|----------|---------------|-------|
| Spec: `specs/<feature>/spec.md` | v<X.Y.Z> · sha256:<hash> | |
| ADR: `specs/<feature>/adr.md` | sha256:<hash> | (if applicable) |
| Test certification: `specs/<feature>/test-certification.md` | sha256:<hash> | (if applicable) |
| <other artifact> | | |

---

### Outputs Produced

List every artifact this agent wrote or modified.

| Artifact | Location | Status |
|----------|----------|--------|
| <file> | <path> | Created / Updated |

---

### Summary

One to three sentences. What was accomplished? What was the key decision or finding?

---

### Risks and Blockers

Items that could prevent the next stage from succeeding, or that the next assignee must know.

| ID | Severity | Description | Owner | Status |
|----|----------|-------------|-------|--------|
| R-01 | High / Medium / Low | <risk description> | <agent or human> | Open / Mitigated |

If none: `None identified.`

---

### Spec Hash Verification

- Spec hash at dispatch: `sha256:<hash>`
- Spec hash verified by this agent: `sha256:<hash>`
- Match: ✅ Yes / ❌ No — if No, stop and escalate to Coordinator before this handoff is accepted

---

### Confidence

Self-assessment of output completeness and correctness.

| Dimension | Score (1–5) | Notes |
|-----------|-------------|-------|
| Spec coverage (all ACs addressed) | | |
| Output completeness | | |
| Risk identification | | |

**Overall confidence:** High / Medium / Low

Low confidence is not a blocker — it is a signal. A Low confidence handoff triggers an additional Coordinator validation pass before dispatch to the next stage.

---

### Suggested Next Assignee

- Next stage: <stage name>
- Assign to: <agent name>
- Include in context: <list the specific artifacts and sections the next agent needs>
- Flag for human: Yes / No — if Yes, describe what decision is needed

---

### Notes for Coordinator

Any routing decisions, context drift flags, or anomalies observed during this stage that do not fit the above fields.
