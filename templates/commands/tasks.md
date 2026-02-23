You are the Coordinator generating the task list for the approved feature.

$ARGUMENTS

The ADR has been human-approved. Generate the task list:

1. Identify the active feature folder in `AI-Dev-Shop-speckit/specs/`.
2. Read `AI-Dev-Shop-speckit/specs/<NNN>-<feature-name>/adr.md` for the parallel delivery plan and module boundaries.
3. Read `AI-Dev-Shop-speckit/specs/<NNN>-<feature-name>/spec.md` for AC priorities (P1/P2/P3).
4. Write `AI-Dev-Shop-speckit/specs/<NNN>-<feature-name>/tasks.md` using `AI-Dev-Shop-speckit/templates/tasks-template.md`:
   - Phase 0: Setup (tooling, directory structure)
   - Phase 1: Foundational infrastructure (blocks all stories)
   - Phase 2+: One phase per user story, ordered P1 first
   - Phase N: Polish
   - Mark tasks [P] that touch different files with no shared mutable state
   - Add checkpoint annotations after Phase 1 and after each story phase
5. Output: tasks.md path, total task count, parallelizable task count, phase structure summary, recommended next command (`/implement`).
