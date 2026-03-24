# External Audit Packet

## Ask

- **User request:** <what the user asked for>
- **Audit focus:** <what the external auditor should examine most closely>
- **Scope:** <work-log | current-diff | staged | last-commit | custom>
- **Audit target:** <commit, diff, or explicit file set>
- **Dispatch packet:** <peer-readable packet path when a dispatch copy is needed; otherwise "same as authoring packet">

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

Return:

1. Findings ordered by severity
2. File references when possible
3. Which changes are blockers vs optional improvements
4. What looks solid and should probably stay unchanged
