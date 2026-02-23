# Compatibility Matrix

Maps AI Dev Shop features to host environments. Use this before adopting a feature to know what works without guessing.

**Hosts covered:** Claude Code · Claude.ai (web) · Codex CLI · Gemini CLI · Generic LLM (prompt-only)

---

## Feature Matrix

| Feature | Claude Code | Claude.ai (web) | Codex CLI | Gemini CLI | Generic LLM |
|---------|------------|-----------------|-----------|------------|-------------|
| **Task tool / agent spawning** | ✅ Full | ❌ Not supported | ❌ Not supported | ❌ Not supported | ❌ Not supported |
| **Simulated multi-agent** (single session, roleplay stages) | ✅ Possible | ✅ Possible | ✅ Possible | ✅ Possible | ✅ Possible |
| **Filesystem reads** (specs/, project-knowledge/, templates/) | ✅ Native | ❌ Requires paste | ✅ Native | ✅ Native | ❌ Requires paste |
| **Filesystem writes** (state file, spec artifacts) | ✅ Native | ❌ Requires copy-out | ✅ Native | ✅ Native | ❌ Requires copy-out |
| **Bash tool** (TestRunner: `npm test`, `pytest`, etc.) | ✅ Full | ❌ Not supported | ✅ Full | ⚠️ Limited | ❌ Not supported |
| **SHA-256 content hashing** (spec hash) | ✅ Via Bash | ⚠️ Manual only | ✅ Via Bash | ✅ Via Bash | ⚠️ Manual only |
| **Pipeline state file** (`.pipeline-state.md`) | ✅ Auto-written | ⚠️ Manual upkeep | ✅ Auto-written | ✅ Auto-written | ⚠️ Manual upkeep |
| **Spec integrity gates** (hash mismatch blocking) | ✅ Full | ✅ Full (manual routing) | ✅ Full (manual routing) | ✅ Full (manual routing) | ✅ Full (manual routing) |
| **Parallel task execution** | ✅ Full (Task tool) | ❌ Sequential only | ❌ Sequential only | ❌ Sequential only | ❌ Sequential only |
| **Observer Agent** (runs alongside pipeline) | ✅ Full | ⚠️ Deferred pass only | ⚠️ Deferred pass only | ⚠️ Deferred pass only | ⚠️ Deferred pass only |
| **Memory-store / project knowledge persistence** | ✅ Auto (file writes) | ⚠️ Manual copy-out | ✅ Auto | ✅ Auto | ⚠️ Manual copy-out |

**Legend:** ✅ Full native support · ⚠️ Partial or manual workaround needed · ❌ Not supported

---

## Host Notes

### Claude Code (full feature set)

All features work as documented. The Task tool enables true parallel agent dispatch and isolated context windows per agent. This is the recommended host for production use of this framework.

### Claude.ai (web)

No Task tool, no filesystem access. All pipeline stages run in a single conversation with manual routing. Paste template file contents directly as your prompt message.

For SHA-256 hashes, compute manually using your OS shell or a web tool and paste the result into the artifact. Pipeline state file must be maintained by copy-pasting the current state into a local file between sessions.

### Codex CLI

Filesystem reads and writes work natively. No Task tool means agents run sequentially in a single session — multi-agent parallelism is not available. Bash tool available for test running.

### Gemini CLI

Filesystem reads and writes work natively. Bash tool availability depends on your Gemini CLI configuration — verify before relying on TestRunner automation.

### Generic LLM (prompt-only, no tools)

Paste all relevant context into the prompt manually. SHA-256 hashes must be computed outside the LLM session. Pipeline state tracking is fully manual. Spec integrity checks rely on the LLM following instructions — there is no enforcement mechanism.

---

## Choosing a Workflow Mode

| Your situation | Recommended approach |
|---------------|---------------------|
| Claude Code with full tool access | Task tool dispatch per pipeline stage |
| Any LLM with filesystem access | Manual prompts + auto file writes |
| Any LLM without filesystem access | Manual prompts + manual file management |
| Single-session (no multi-agent) | Run each pipeline stage sequentially; paste previous stage output as context for the next |

---

## Known Limitations by Feature

**Parallel tasks:**
Only meaningful with the Task tool (Claude Code). On all other hosts, execute tasks sequentially in the order that minimizes blocking dependencies.

**SHA-256 hashing on web hosts:**
Without Bash, generate hashes with `shasum -a 256 <file>` on macOS/Linux or `Get-FileHash -Algorithm SHA256 <file>` on Windows. Paste the result into the spec header. A missing or unverified hash degrades spec integrity guarantees but does not break the pipeline — flag it in the pipeline state Notes section.

**Observer Agent on non-Claude Code hosts:**
The Observer's analysis passes still work as read-only tasks. What degrades is real-time interleaving with the pipeline. Run the Observer as a deferred pass after each feature ships rather than alongside the pipeline.
