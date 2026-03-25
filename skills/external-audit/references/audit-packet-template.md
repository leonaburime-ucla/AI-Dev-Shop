# External Audit Packet

## Ask

- **User request:** <what the user asked for>
- **Audit focus:** <what the external auditor should examine most closely>
- **Scope:** <work-log | current-diff | staged | last-commit | custom>
- **Audit target:** <commit, diff, or explicit file set>
- **Authoring packet:** <where the coordinator wrote the canonical packet>
- **Dispatch packet:** <peer-readable packet path actually handed to the external auditor>

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

1. Start with an `Auditor Scope Check` that restates what you believe you are auditing, the active scope and audit target, which files or artifacts you actually reviewed, and any ambiguity or mismatch you noticed
2. Findings ordered by severity
3. File references when possible
4. Which changes are blockers vs optional improvements
5. What looks solid and should probably stay unchanged
