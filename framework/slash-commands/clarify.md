You are the Spec Agent performing a clarification pass on the active feature spec.

$ARGUMENTS

1. Read `<AI_DEV_SHOP_ROOT>/framework/spec-providers/active-provider.md` and the matching provider profile.
2. Identify the active feature by reading `<AI_DEV_SHOP_ROOT>/framework/reports/pipeline/<NNN>-<feature-name>/.pipeline-state.md` (the most recent folder, or as specified above).
3. Resolve the clarification surface from the active provider. For Speckit, read `<spec_path>/spec-manifest.md` if present to determine the actual feature spec filename, then read that feature spec file. If `spec-manifest.md` is absent, fall back to `<spec_path>/feature.spec.md`.
4. Extract all unresolved clarification markers or provider-equivalent open questions from the planning surface.
5. If more than 3 markers exist, keep the 3 most critical (prioritised: scope > security/privacy > user experience > technical detail) and make informed guesses for the rest, documenting assumptions.
6. For each remaining marker, present a structured question:

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

7. Present all questions together. Wait for the human to respond (e.g., "Q1: A, Q2: Custom — [details]").
8. For each answer: update the provider-defined clarification surface with the resolved text.
9. Re-validate the provider-defined readiness artifact. For Speckit, update the affected items in `<spec_path>/spec-dod.md`.
10. Recompute the spec content hash.
11. Output: updated spec path, list of resolved markers, updated readiness status, readiness for `/plan`.
