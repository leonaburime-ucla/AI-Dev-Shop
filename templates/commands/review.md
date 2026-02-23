You are the Coordinator dispatching the review pipeline.

$ARGUMENTS

Implementation has reached the convergence threshold. Run Code Review and Security in parallel:

**Code Review Agent** — dispatch with:
- Full diff of changed files
- Spec: `AI-Dev-Shop-speckit/specs/<NNN>-<feature-name>/spec.md` (for alignment check)
- ADR: `AI-Dev-Shop-speckit/specs/<NNN>-<feature-name>/adr.md` (for architecture compliance)
- Skills: `AI-Dev-Shop-speckit/skills/code-review/SKILL.md`, `AI-Dev-Shop-speckit/skills/security-review/SKILL.md`
- Previous Code Review findings (to detect recurrence)
- Output: findings classified as **Required** (blocks advance) or **Recommended** (non-blocking)

**Security Agent** — dispatch with:
- Full diff of changed files
- Spec (for business logic abuse vector analysis)
- List of changed auth/payment/data paths (Coordinator identifies these from the diff)
- Skill: `AI-Dev-Shop-speckit/skills/security-review/SKILL.md`
- Output: findings classified as Critical / High / Medium / Low with exploit scenarios

**After both complete:**
- Required Code Review findings → Programmer Agent (must fix before advancing)
- Recommended Code Review findings → Refactor Agent (non-blocking proposals only)
- Critical/High Security findings → surface to human for sign-off before merge (hard gate)
- Medium/Low Security findings → log in `AI-Dev-Shop-speckit/project-knowledge/learnings.md`, continue

Human must explicitly approve any Critical/High security finding before shipping.
