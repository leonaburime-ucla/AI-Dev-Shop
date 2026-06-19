# Handoff — Addy Osmani Skill Integration

## What Was Done

Integrated content from [Addy Osmani's agent-skills repo](https://github.com/addyosmani/agent-skills) into the AI Dev Shop skill library. This involved:

1. **Content comparison** — deep-read of all ~90 existing skills vs Osmani's set to find actual content gaps (not just topic overlap)
2. **3-model /debate** (Codex GPT-5.5 + Gemini 3.1 Pro + Claude) on integration strategy for three question sets:
   - **Q1**: High-value extractions (significant content gaps in existing skills) → add as `references/` files
   - **Q2**: VibeCoder `idea-refine` and `interview-me` → offer as opt-in skills (not gates), marked planned
   - **Q3**: Moderate extractions → add as `references/` files with conditional triggers
3. **Implementation** — 18 new reference files created, 17 SKILL.md files modified with triggers
4. **Two full 3-auditor passes** — caught and fixed ~29 issues total across both rounds

## Current State (all committed and pushed to `main`)

### Key Commits
- `33d6d25` — feat: integrate Addy Osmani skill content (Q1+Q2+Q3) with audit fixes
- `6732cae` — fix: post-audit corrections from 3-auditor /audit-work pass (13 fixes)

### What the Last Audit Fixed (commit 6732cae)
1. TTI → TBT + INP (TTI retired from Lighthouse 10)
2. Art-direction `<source>` — removed invalid `w` descriptors from single-URL sources
3. SSRF — `ipaddr.process()` + allow-only `unicast` (not deny-list) + Azure IMDS note
4. Prometheus — "estimated percentiles" + bucket alignment + native histograms
5. Node 22+ `--import` for ESM OTel bootstrap
6. Rollout P95 thresholds defined (±10% Advance, 10-50% Hold)
7. Gated-workflow cross-ref corrected to actual section names
8. Focus trap note added to Modal (WCAG 2.4.3)
9. Touch targets: 24×24 AA min, 44×44 AAA/Apple HIG
10. idea-refine/interview-me marked "planned — not yet in repo"
11. VibeCoder under-spec: OR → AND (both artifact AND success condition missing)
12. Changelog trigger collision fixed in developer-documentation
13. branded-types.md trigger made TypeScript-conditional

## What Remains

### Pending Audit
**Codex GPT-5.5 xhigh `/audit-work` on commit `6732cae`** — dispatched 2026-06-18. ENOSPC resolved (stale tmp cleaned, disk has 67GB free). Audit in progress.

### Unimplemented Skills
These were identified in the original analysis but not yet created:
- `idea-refine` — structured sharpening pass (diverge → cluster → stress-test → "Not Doing" list)
- `interview-me` — one-question-at-a-time intent extraction
- `browser-testing-with-devtools` — wholesale new skill from Osmani
- `doubt-driven-development` — wholesale new skill from Osmani
- `using-agent-skills` — wholesale new skill from Osmani
- `source-driven-development` — wholesale new skill from Osmani

### Known Technical Issues
- **ENOSPC on /tmp**: The tmp filesystem filled up. Run `rm -rf /private/tmp/claude-501/` or set `CLAUDE_CODE_TMPDIR` env var
- **agy CLI**: Works from `/tmp` cwd to avoid AGENTS.md pollution. Model format is exact string from `agy models` (e.g., "Gemini 3.1 Pro (High)")
- **Claude Opus 4.8**: Returns 403 — not available for this account tier as a peer

## File Locations (new reference files)

All under `skills/`:
```
security-review/references/llm-owasp-and-advanced.md
performance-engineering/references/web-performance-targets.md
observability-implementation/references/observability-principles.md
systematic-debugging/references/debugging-advanced.md
advanced-frontend-architecture/references/frontend-implementation-patterns.md
code-review/references/review-discipline.md
test-design/references/test-size-model.md
devops-delivery/references/rollout-decision-thresholds.md
devops-delivery/references/pre-launch-checklist.md
devops-delivery/references/quality-gate-pipeline.md
architecture-migration/references/deprecation-lifecycle.md
superpowers-finishing-a-development-branch/references/commit-standards.md
refactor-patterns/references/rule-of-500.md
implementation-outline/references/work-breakdown.md
spec-writing/references/gated-workflow.md
developer-documentation/references/changelog-template.md
api-design/references/branded-types.md
context-engineering/references/session-setup-patterns.md
```

All have `<!-- Source: Addy Osmani / agent-skills / <skill> -->` headers.
