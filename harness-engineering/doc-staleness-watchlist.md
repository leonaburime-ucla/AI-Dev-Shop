# Doc Staleness Watchlist

High-risk docs that should be reviewed against concrete repo artifacts on a recurring cadence.

| Doc | Verify Against | Cadence Days | Last Reviewed | Reason |
|---|---|---:|---|---|
| `AGENTS.md` | `agents/`, `skills/coordination/SKILL.md`, `workflows/multi-agent-pipeline.md`, `project-knowledge/operations/pipeline-quickstart.md` | 30 | 2026-03-22 | Root runtime map must stay aligned with actual routing and workflow docs. |
| `project-knowledge/operations/pipeline-quickstart.md` | `AGENTS.md`, `workflows/multi-agent-pipeline.md`, `project-knowledge/routing/file-trigger-table.md` | 30 | 2026-03-22 | Quickstart is the human-readable map and must reflect current routing defaults. |
| `project-knowledge/routing/file-trigger-table.md` | `agents/`, `skills/coordination/SKILL.md` | 21 | 2026-03-22 | Trigger routing should stay aligned with current agent ownership. |
| `workflows/multi-agent-pipeline.md` | `agents/`, `templates/`, `project-knowledge/routing/file-trigger-table.md` | 30 | 2026-03-22 | Stage context and routing assumptions drift easily when new docs land. |
| `harness-engineering/context-offloading.md` | `agents/coordinator/skills.md`, `agents/programmer/skills.md`, `agents/testrunner/skills.md` | 30 | 2026-03-22 | Offloading rules should match the actual roles expected to apply them. |
