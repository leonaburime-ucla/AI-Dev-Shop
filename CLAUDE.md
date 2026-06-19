# AI Dev Shop (speckit) — Claude Code Entry Point

`<AI_DEV_SHOP_ROOT>` means the path to this toolkit folder (typically `AI-Dev-Shop-speckit/`).

Read `<AI_DEV_SHOP_ROOT>/AGENTS.md` for full operating instructions: all agent definitions, pipeline stages, routing rules, convergence policy, dispatch protocol, slash commands, and human checkpoints.

## Claude Code: Spawning Agents

Use the **Task tool** to dispatch each specialized agent. Include their `<AI_DEV_SHOP_ROOT>/agents/<name>/skills.md`, the relevant `<AI_DEV_SHOP_ROOT>/skills/*/SKILL.md` files listed in their Skills section, the active spec with hash, and the specific task directive.

## Claude Code: Slash Command Setup

To activate slash commands, copy the command files once:

```bash
cp -r <AI_DEV_SHOP_ROOT>/framework/slash-commands/ .claude/commands/
```

Then type `/spec`, `/plan`, `/tasks`, `/implement`, `/code-review`, `/clarify`, `/consensus`, `/debate`, `/audit-work`, `/cowork`, or `/handoff` directly in chat. If you haven't done the copy yet, use Option B from `<AI_DEV_SHOP_ROOT>/AGENTS.md` — paste the template contents directly as a prompt.

## Tmp Space

If `/tmp` fills up (ENOSPC during audits or task spawning), clean stale session dirs:
```bash
rm -rf /private/tmp/claude-501/
```

## Eval Work — Mandatory Pre-reads

Before creating, revising, or auditing any eval suite, ALWAYS read these files first:

- `harness-engineering/agent-evals/bug-taxonomy.md`
- `harness-engineering/agent-evals/eval-design-playbook.md`
- `harness-engineering/agent-evals/README.md`

Do not begin fixture design, seed selection, or scoring until all three are loaded into context. This applies to both the coordinator and any dispatched subagent doing eval work.
