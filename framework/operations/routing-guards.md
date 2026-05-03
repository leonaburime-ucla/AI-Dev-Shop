# Routing Guards

This file is the source of truth for command-level routing guards that prevent similar-looking requests from being handled by the wrong workflow.

## Debate Routing Guard (Blocking)

When the user asks for a debate, uses `/debate`, asks for a "2 round debate", or otherwise requests multiple agents/models to argue a question, default to **Swarm Consensus debate with external peer LLM CLIs** such as Claude, Gemini, Codex, or other configured external peers.

- Platform subagents, current-LLM helper agents, repo-persona consultations, and same-family child agents must not be used to satisfy a debate request by default.
- Use platform subagents for a debate only when the user explicitly asks for current-LLM subagents, local subagents, repo-persona debate, or cross-agent consultation.
- Generic wording such as "agents", "debaters", "external agents", or "models" is not enough to justify current-LLM subagents; route to Swarm Consensus external peers instead.
- If external peer CLIs are unavailable, say so and stop or continue only under the Swarm Consensus fallback rules. Do not silently fall back to platform subagents.
- Before launching any debate, state which protocol will be used: `Swarm Consensus debate` or `repo-persona subagent consultation`.
- When naming debate participants, show the resolved or planned **model name/version** first. CLI version strings are diagnostics only and must not be presented as model identity.

## Cowork Routing Guard

When the user asks multiple LLMs to work together on a bounded file-editing task, asks for `/cowork`, or describes agents changing files in tandem, route to `<AI_DEV_SHOP_ROOT>/framework/slash-commands/cowork.md`.

- Use `/cowork` for collaborative implementation where all participants read the scoped files, independently diagnose, converge on one edit plan, write under file-level leases, and peer-verify the resulting diffs.
- Do not route collaborative file-editing requests to `/debate`; `/debate` is reasoning-only.
- Do not route collaborative file-editing requests to `/audit-work`; `/audit-work` is independent review-only and must not apply edits.
- If the file set is unbounded or the task needs the full staged delivery pipeline, route to the normal pipeline instead of `/cowork`.
- `/cowork` may reduce the need for `/audit-work` only under its documented low-risk, green-test, no-disagreement audit-skip policy.
