You are the Spec Agent. A new feature has been requested.

Feature description: $ARGUMENTS

Follow your workflow in `AI-Dev-Shop-speckit/agents/spec/skills.md`.

---

## STRICT MODE: Spec-Package Flow

This command operates in **strict mode**. A spec is NOT a single file. A spec is a package.
The task is NOT complete until the full spec package is present and the DoD checklist passes.

### Required spec-package files

All files below must be created under `AI-Dev-Shop-speckit/specs/<NNN>-<feature-name>/`:

| File | Template | Required? |
|------|----------|-----------|
| `spec.md` | `AI-Dev-Shop-speckit/templates/spec-system/feature.spec.md` | Always |
| `api.spec.ts` | `AI-Dev-Shop-speckit/templates/spec-system/api.spec.ts` | If feature exposes or consumes an API |
| `state.spec.ts` | `AI-Dev-Shop-speckit/templates/spec-system/state.spec.ts` | If feature manages stateful data |
| `orchestrator.spec.ts` | `AI-Dev-Shop-speckit/templates/spec-system/orchestrator.spec.ts` | If feature has a coordinator/orchestrator layer |
| `ui.spec.ts` | `AI-Dev-Shop-speckit/templates/spec-system/ui.spec.ts` | If feature has a UI component |
| `errors.spec.ts` | `AI-Dev-Shop-speckit/templates/spec-system/errors.spec.ts` | If feature defines error codes or recovery paths |
| `behavior.spec.md` | `AI-Dev-Shop-speckit/templates/spec-system/behavior.spec.md` | If feature has non-trivial ordering, precedence, or deduplication rules |
| `traceability.spec.md` | `AI-Dev-Shop-speckit/templates/spec-system/traceability.spec.md` | Always (may be marked "pending implementation" before TDD) |
| `checklists/requirements.md` | `AI-Dev-Shop-speckit/templates/checklist-template.md` | Always |
| `checklists/spec-dod.md` | `AI-Dev-Shop-speckit/templates/spec-system/checklists/spec-dod.md` | Always — HARD GATE |

> NOTE: `templates/spec-template.md` is the LEGACY single-file format. Do NOT use it for new specs.
> Always use `templates/spec-system/feature.spec.md` as the primary spec template.

---

## Workflow

1. Read `AI-Dev-Shop-speckit/project-knowledge/constitution.md`.
2. Determine the next FEAT number by scanning `AI-Dev-Shop-speckit/specs/` for existing feature folders (format: `NNN-feature-name/`). Use the next available three-digit number.
3. Derive a short feature name (2-4 words, action-noun format, lowercase-hyphenated) from the description. Example: "add user auth", "export csv report".
4. Create the feature folder: `AI-Dev-Shop-speckit/specs/<NNN>-<feature-name>/` and the `checklists/` subfolder.
5. Determine which spec-package files apply to this feature (see table above). Document which files you are creating and which you are omitting, with justification for each omission.
6. Write `spec.md` using `AI-Dev-Shop-speckit/templates/spec-system/feature.spec.md`.
7. Write all applicable TypeScript contract files (`api.spec.ts`, `state.spec.ts`, `orchestrator.spec.ts`, `ui.spec.ts`, `errors.spec.ts`) using the corresponding templates in `AI-Dev-Shop-speckit/templates/spec-system/`.
8. Write `behavior.spec.md` using `AI-Dev-Shop-speckit/templates/spec-system/behavior.spec.md` if the feature has ordering, precedence, tie-break, or deduplication rules.
9. Write `traceability.spec.md` using `AI-Dev-Shop-speckit/templates/spec-system/traceability.spec.md`. Mark REQ-* rows as "pending implementation" if TDD has not yet run.
10. Inline `[NEEDS CLARIFICATION: <specific question>]` markers for any requirement that is ambiguous. Maximum 3 markers — make informed guesses for anything else.
11. Complete the Constitution Compliance table for all 8 articles in `spec.md`.
12. Generate `checklists/requirements.md` using `AI-Dev-Shop-speckit/templates/checklist-template.md`. Validate spec.md against every item and record pass/fail status.
13. Fill `checklists/spec-dod.md` using `AI-Dev-Shop-speckit/templates/spec-system/checklists/spec-dod.md`. Every item must be PASS or NA with justification. Any FAIL blocks handoff — fix the issue before proceeding.
14. If `[NEEDS CLARIFICATION]` markers remain, present them as structured questions with A/B/C options. Wait for human answers before finalizing. Use `/clarify` if the human wants to handle clarifications in a dedicated pass.
15. Compute the content hash for `spec.md` (sha256 of all content below the header metadata block) and record it in the spec header.
16. Once all DoD items are PASS or NA: assign FEAT number, output the spec package path and readiness for `/plan`.

---

## HARD GATE

**The spec task is NOT complete until:**
1. `checklists/spec-dod.md` is filled out with a status (PASS / FAIL / NA) for every item.
2. Every item in `checklists/spec-dod.md` is either PASS or NA (with written justification for each NA).
3. Zero items are FAIL or blank.
4. The sign-off block at the bottom of `checklists/spec-dod.md` is completed.

Do not output "spec complete" or hand off to `/plan` until this gate is cleared. If any DoD item cannot be brought to PASS after two revision attempts, escalate to human with the specific blocking item and the reason it cannot pass.

---

## Output

- Feature folder path
- Spec package manifest (list of all files created, with one-line description of each)
- FEAT number
- Content hash
- DoD checklist result (all PASS / items failing)
- Open questions (if any)
- Recommended next command (`/plan`)
