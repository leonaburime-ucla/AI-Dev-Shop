# Compatibility Matrix

Maps AI Dev Shop (speckit) features to host environments. Use this before adopting a feature to know what works without guessing.

**Hosts covered:** Claude Code · Claude.ai (web) · Codex CLI · Gemini CLI · Generic LLM (prompt-only)
Placeholder note: `<AI_DEV_SHOP_ROOT>` means the path to this toolkit folder (usually `AI-Dev-Shop-speckit/`).

---

## Feature Matrix

| Feature | Claude Code | Claude.ai (web) | Codex CLI | Gemini CLI | Generic LLM |
|---------|------------|-----------------|-----------|------------|-------------|
| **Slash commands** (`/spec`, `/plan`, `/tasks`, `/implement`, `/review`, `/clarify`) | ✅ Full (after one-time setup) | ❌ Not supported | ❌ Not supported | ❌ Not supported | ❌ Not supported |
| **Option B manual workflow** (paste template contents as prompt) | ✅ Full | ✅ Full | ✅ Full | ✅ Full | ✅ Full |
| **Task tool / agent spawning** | ✅ Full | ❌ Not supported | ❌ Not supported | ❌ Not supported | ❌ Not supported |
| **Simulated multi-agent** (single session, roleplay stages) | ✅ Possible | ✅ Possible | ✅ Possible | ✅ Possible | ✅ Possible |
| **Filesystem reads** (specs/, project-knowledge/, templates/) | ✅ Native | ❌ Requires paste | ✅ Native | ✅ Native | ❌ Requires paste |
| **Filesystem writes** (state file, spec artifacts) | ✅ Native | ❌ Requires copy-out | ✅ Native | ✅ Native | ❌ Requires copy-out |
| **Bash tool** (TestRunner: `npm test`, `pytest`, etc.) | ✅ Full | ❌ Not supported | ✅ Full | ⚠️ Limited | ❌ Not supported |
| **SHA-256 content hashing** (spec hash, ADR hash) | ✅ Via Bash | ⚠️ Manual only | ✅ Via Bash | ✅ Via Bash | ⚠️ Manual only |
| **Pipeline state file** (`.pipeline-state.md`) | ✅ Auto-written | ⚠️ Manual upkeep | ✅ Auto-written | ✅ Auto-written | ⚠️ Manual upkeep |
| **Constitution gates** (blocking escalation on violation) | ✅ Full | ✅ Full (manual routing) | ✅ Full (manual routing) | ✅ Full (manual routing) | ✅ Full (manual routing) |
| **[NEEDS CLARIFICATION] marker resolution** | ✅ Full | ✅ Full | ✅ Full | ✅ Full | ✅ Full |
| **FEAT number assignment** | ✅ Auto (reads specs/) | ⚠️ Manual | ⚠️ Manual | ⚠️ Manual | ⚠️ Manual |
| **Parallel task execution** (`[P]` markers in tasks.md) | ✅ Full (Task tool) | ❌ Sequential only | ❌ Sequential only | ❌ Sequential only | ❌ Sequential only |
| **Observer Agent** (runs alongside pipeline) | ✅ Full | ⚠️ Deferred pass only | ⚠️ Deferred pass only | ⚠️ Deferred pass only | ⚠️ Deferred pass only |
| **Memory-store / project knowledge persistence** | ✅ Auto (file writes) | ⚠️ Manual copy-out | ✅ Auto | ✅ Auto | ⚠️ Manual copy-out |

**Legend:** ✅ Full native support · ⚠️ Partial or manual workaround needed · ❌ Not supported

---

## Host Notes

### Claude Code (full feature set)

All features work as documented. Slash commands require the one-time setup:

```bash
cp -r <AI_DEV_SHOP_ROOT>/templates/commands/ .claude/commands/
```

The Task tool enables true parallel agent dispatch and isolated context windows per agent. This is the recommended host for production use of this framework.

### Claude.ai (web)

No Task tool, no slash commands, no filesystem access. All pipeline stages run in a single conversation with manual routing. Use Option B: paste the contents of `templates/commands/<command>.md` directly as your message.

For SHA-256 hashes, compute manually using your OS shell or a web tool and paste the result into the artifact. Pipeline state file must be maintained by copy-pasting the current state into a local file between sessions.

### Codex CLI

Filesystem reads and writes work natively. No Task tool means agents run sequentially in a single session — multi-agent parallelism is not available. Slash commands are not supported; use Option B. Bash tool available for test running.

### Gemini CLI

Filesystem reads and writes work natively. Bash tool availability depends on your Gemini CLI configuration — verify before relying on TestRunner automation. Slash commands not supported; use Option B.

### Generic LLM (prompt-only, no tools)

Paste all relevant context into the prompt manually. Use Option B for every pipeline stage. SHA-256 hashes must be computed outside the LLM session. Pipeline state tracking is fully manual. Constitution gates and spec integrity checks rely on the LLM following instructions — there is no enforcement mechanism.

---

## Choosing a Workflow Mode

| Your situation | Recommended approach |
|---------------|---------------------|
| Claude Code with full tool access | Option A — slash commands + Task tool |
| Any LLM with filesystem access | Option B — manual prompts + auto file writes |
| Any LLM without filesystem access | Option B — manual prompts + manual file management |
| Single-session (no multi-agent) | Run each pipeline stage sequentially in one conversation; paste previous stage output as context for the next |

---

## Known Limitations by Feature

**Parallel tasks (`[P]` markers):**
The Task tool (Claude Code) spawns each agent as a genuinely isolated subprocess with its own context window. This is the only host where `[P]` tasks run with true parallel execution and context isolation.

Codex CLI and Gemini CLI do not have an equivalent sub-agent dispatch mechanism. There is no API or built-in command to spawn a separate agent instance mid-session on these hosts. `[P]` tasks must be executed sequentially in a single session; context from earlier tasks accumulates rather than being isolated. On these hosts, treat `[P]` markers as sequencing hints — order independent tasks to minimize blocking, but do not expect isolation or true concurrency.

**SHA-256 hashing on web hosts:**
Without Bash, generate hashes with `shasum -a 256 <file>` on macOS/Linux or `Get-FileHash -Algorithm SHA256 <file>` on Windows. Paste the result into the spec header. A missing or unverified hash degrades spec integrity guarantees but does not break the pipeline — flag it in the pipeline state Notes section.

**Observer Agent on non-Claude Code hosts:**
The Observer's LLM-as-judge pass and weekly scoring still work — they are read-only analysis tasks. What degrades is real-time interleaving with the pipeline. Run the Observer as a deferred pass after each feature ships rather than alongside the pipeline.
