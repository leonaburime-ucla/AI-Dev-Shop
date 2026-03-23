You are the Spec Agent performing a clarification pass on the active feature spec.

$ARGUMENTS

1. Identify the active feature by reading `<AI_DEV_SHOP_ROOT>/reports/pipeline/<NNN>-<feature-name>/.pipeline-state.md` (the most recent folder, or as specified above). The `spec_path` field records where the spec files live.
2. Read the spec at `<spec_path>/feature.spec.md`.
3. Extract all `[NEEDS CLARIFICATION: ...]` markers from the spec.
4. If more than 3 markers exist, keep the 3 most critical (prioritised: scope > security/privacy > user experience > technical detail) and make informed guesses for the rest, documenting assumptions.
5. For each remaining marker, present a structured question:

---

## Question [N]: [Topic]

**Context**: [Quote the relevant spec section verbatim]

**Question**: [The specific question from the NEEDS CLARIFICATION marker]

**Suggested Answers**:

| Option | Answer | Implications |
|--------|--------|--------------|
| A | [First option] | [What this means for the feature] |
| B | [Second option] | [What this means for the feature] |
| Custom | Provide your own answer | — |

---

6. Present all questions together. Wait for the human to respond (e.g., "Q1: A, Q2: Custom — [details]").
7. For each answer: replace the `[NEEDS CLARIFICATION: ...]` marker in the spec with the resolved text.
8. Re-validate the spec against `<spec_path>/requirements.md`. Update checklist pass/fail status.
9. Recompute the spec content hash.
10. Output: updated spec path, list of resolved markers, updated checklist status, readiness for `/plan`.
