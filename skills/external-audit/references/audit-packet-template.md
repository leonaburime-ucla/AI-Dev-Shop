# External Audit Packet

## Ask

- **User request:** <what the user asked for>
- **Audit focus:** <what the external auditors should examine most closely>
- **Scope:** <work-log | current-diff | staged | last-commit | custom>
- **Suggested changes mode:** <patches | notes | none>
- **Audit target:** <commit, diff, or explicit file set>
- **Planned auditors:** <claude, gemini, codex, or explicit subset>
- **Authoring packet:** <where the coordinator wrote the canonical packet>
- **Dispatch packet:** <peer-readable packet path actually handed to each external auditor>

## Work Log

- <action taken>
- <why it was done>
- <important tradeoff or design choice>

## Files And Artifacts

| Path | Why it matters |
|---|---|
| `<path>` | <reason> |

## Validation

- **Checks run:** <tests, smoke tests, diff review, none>
- **Checks not run:** <what was skipped>
- **Known caveats:** <limitations or uncertainty>

## Out-Of-Scope Local Changes

- <file or local change excluded from audit scope and why>

## Open Questions

- <question 1>
- <question 2>

## Auditor Instructions

Please review this work independently. Use the Ask section's `Audit target` and `Dispatch packet` fields as the source of truth for what to inspect and which packet path was actually handed to you.

Do not assume any other auditor has seen the same issues you see. Return your own review only; the Coordinator will synthesize across auditors after all independent responses are collected.

Return:

1. Start with an `Auditor Scope Check` that restates what you believe you are auditing, the active scope and audit target, which files or artifacts you actually reviewed, and any ambiguity or mismatch you noticed
2. Findings ordered by severity using this taxonomy: `blocker` means must fix before relying on the work; `high` means real risk if ignored; `medium` means notable improvement or maintainability risk; `low` means minor inconsistency or polish
3. File references when possible
4. Which changes are blockers vs optional improvements
5. For each finding, include `Finding Rationale` with these fields. Do not include private chain-of-thought; provide concise evidence-backed audit reasoning only:
   - `Checked:` files, artifacts, commands, or packet sections inspected
   - `Expected:` the contract, behavior, invariant, or quality bar the work should satisfy
   - `Observed:` the concrete mismatch, omission, risk, or evidence found
   - `Why it matters:` user, correctness, security, maintainability, or workflow impact
   - `Recommended fix:` the smallest actionable fix or the decision needed
   - `Confidence:` high, medium, or low, with the main uncertainty if not high
6. What looks solid and should probably stay unchanged
7. If `Suggested changes mode` is `notes`, include `Suggested Changes` with file-level edit guidance and concise replacement snippets when useful
8. If `Suggested changes mode` is `patches`, include `Suggested Changes` plus `Proposed File Changes` with unified diffs or bounded replacement snippets only for files you actually reviewed; if the scope is too uncertain for safe patch proposals, fall back to notes and say why
