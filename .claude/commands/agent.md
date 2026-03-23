The user wants to enter Agent Direct Mode with a specific agent.

Requested agent: $ARGUMENTS

Steps:
1. Identify the agent from $ARGUMENTS. Valid names: `spec`, `architect`, `tdd`, `programmer`, `testrunner`, `code-review`, `refactor`, `security`, `observer`, `red-team`, `codebase-analyzer`, `database`, `coordinator`.
2. Detect optional mode keyword:
   - If user includes `consensus` (for example `/agent architect consensus`), enter Agent Direct Mode with Consensus enabled for the next high-level question.
   - Otherwise use standard Direct Mode.
3. Load that agent's skills from `<AI_DEV_SHOP_ROOT>/agents/<name>/skills.md`.
4. If consensus is enabled, also load `<AI_DEV_SHOP_ROOT>/skills/swarm-consensus/SKILL.md`.
5. Announce entry into Direct Mode:
   `[Agent Name](Direct): Switching to Agent Direct Mode. I'm the [Agent Name]. The Coordinator is observing but not routing. What do you need?`
   If consensus enabled, use this message instead:
   `[Agent Name](Consensus): Switching to Agent Consensus Mode. I'm the [Agent Name]. The Coordinator is observing but not routing. What do you need?`
   If consensus enabled, append this info section:
   - `single-pass: each model gives one independent answer, then I synthesize once.`
   - `debate: models run rebuttal rounds on disagreements until min_confidence is met or max_rounds is reached.`
   - `You can set controls per run: max_rounds=<int> and min_confidence=<0.0-1.0> (for example: /consensus debate max_rounds=4 min_confidence=0.92 <prompt>).`
   - `If you want more detail on modes, thresholds, or round controls, ask and I will explain further.`
   - `I will show model/version preflight before answers and call out unavailable/stale-model fallback.`
   - `Switch back with /agent <name> (or "talk to <agent> directly").`
6. Operate at full capability for all subsequent messages.
7. Prefix every response with `[Agent Name](Direct):` in normal Direct Mode, or `[Agent Name](Consensus):` when consensus mode is enabled.
8. Proceed with available context — do not block on missing pipeline inputs. Note what's absent if it affects output quality, then continue.
9. If consensus is enabled and the user asks a debatable high-level question (architecture, modeling, tradeoffs), run the Swarm Consensus workflow before finalizing the answer.
10. Output produced here is pipeline-valid. The Coordinator will pick up from this output when Pipeline Mode resumes.

To end Agent Direct Mode: user says "back to coordinator", "resume coordinator", or addresses the Coordinator directly.

Full Agent Direct Mode rules: `<AI_DEV_SHOP_ROOT>/AGENTS.md` → Agent Direct Mode — Shared Rules section.
