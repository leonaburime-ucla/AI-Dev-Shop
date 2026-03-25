# Startup Reminders

Tracks one-time setup prompts. The Coordinator reads this file on every startup
and skips any reminder listed under Dismissed.

To re-enable a reminder, tell the Coordinator: "re-enable reminder: <name>"
or delete the line from the Dismissed section.

---

## Dismissed

(none)

---

## slash-commands-setup

Available commands: `/spec` `/plan` `/tasks` `/implement` `/code-review` `/clarify` `/agent` `/consensus` `/audit-work`
Placeholder note: `<AI_DEV_SHOP_ROOT>` means the toolkit folder path (usually `AI-Dev-Shop-speckit/`).

### Claude Code

If the user says "yes" or "set up slash commands", run this via Bash:
```bash
cp -r <AI_DEV_SHOP_ROOT>/framework/slash-commands/ .claude/commands/
```
Confirm success, then offer to dismiss the reminder.
After setup, `/spec`, `/plan`, `/code-review`, `/consensus`, `/audit-work`, etc. work directly in chat.

### Gemini CLI

Slash commands are not natively supported. Use Option B:
paste the contents of `<AI_DEV_SHOP_ROOT>/framework/slash-commands/<command>.md` as your message.

### Codex CLI

Slash commands are not natively supported. Use Option B:
paste the contents of `<AI_DEV_SHOP_ROOT>/framework/slash-commands/<command>.md` as your message.

### Claude.ai (web)

Slash commands and filesystem access are not available. Use Option B:
open `<AI_DEV_SHOP_ROOT>/framework/slash-commands/<command>.md` on your machine, copy the contents,
and paste as your message. You will also need to paste relevant project files manually.

### Generic LLM

Slash commands are not supported. Use Option B:
open `<AI_DEV_SHOP_ROOT>/framework/slash-commands/<command>.md` on your machine, copy the contents,
and paste as your prompt along with any relevant project files.

### Host Detection

- Prefer the actual runtime/session identity over installed binaries on disk
- If startup code already knows the host, pass it explicitly to resolver scripts or set `AI_DEV_SHOP_HOST`
- Task tool + Bash tool available → usually Claude Code
- Bash tool available, no Task tool → Gemini CLI or Codex CLI; do not guess if both are installed
- No tool access → Claude.ai or Generic LLM
- If uncertain, ask the user which host they are on or stay conservative
