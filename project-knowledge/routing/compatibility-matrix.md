# Compatibility Matrix

Maps AI Dev Shop (speckit) features to host environments. Use this before adopting a feature to know what usually works, then confirm unstable capabilities with the local capability probe instead of trusting the matrix blindly.

**Hosts covered:** Claude Code · Claude.ai (web) · Codex CLI · Gemini CLI · Generic LLM (prompt-only)
Placeholder note: `<AI_DEV_SHOP_ROOT>` means the path to this toolkit folder (usually `AI-Dev-Shop-speckit/`).

Local verification:

```bash
bash harness-engineering/validators/probe_host_capabilities.sh
bash harness-engineering/validators/resolve_subagent_mode.sh --host <detected-host>
```

For the current environment, prefer the probe above plus `harness-engineering/capability-verification.md`. Treat this matrix as a planning default, not the final truth for version-sensitive features.

---

## Feature Matrix

| Feature | Claude Code | Claude.ai (web) | Codex CLI | Gemini CLI | Generic LLM |
|---------|------------|-----------------|-----------|------------|-------------|
| **Slash commands** (`/spec`, `/plan`, `/tasks`, `/implement`, `/review`, `/clarify`) | ✅ Full (after one-time setup) | ❌ Not supported | ❌ Not supported | ❌ Not supported | ❌ Not supported |
| **Option B manual workflow** (paste template contents as prompt) | ✅ Full | ✅ Full | ✅ Full | ✅ Full | ✅ Full |
| **Task tool / agent spawning** | ✅ Full | ❌ Not supported | ⚠️ Runtime-verified; probe locally | ⚠️ Unverified here; verify locally or with vendor docs | ❌ Not supported |
| **Simulated multi-agent** (single session, roleplay stages) | ✅ Possible | ✅ Possible | ✅ Possible | ✅ Possible | ✅ Possible |
| **Filesystem reads** (specs/, project-knowledge/, templates/) | ✅ Native | ❌ Requires paste | ✅ Native | ✅ Native | ❌ Requires paste |
| **Filesystem writes** (state file, spec artifacts) | ✅ Native | ❌ Requires copy-out | ✅ Native | ✅ Native | ❌ Requires copy-out |
| **Bash tool** (TestRunner: `npm test`, `pytest`, etc.) | ✅ Full | ❌ Not supported | ✅ Full | ⚠️ Limited | ❌ Not supported |
| **SHA-256 content hashing** (spec hash, ADR hash) | ✅ Via Bash | ⚠️ Manual only | ✅ Via Bash | ✅ Via Bash | ⚠️ Manual only |
| **Pipeline state file** (`.pipeline-state.md`) | ✅ Auto-written | ⚠️ Manual upkeep | ✅ Auto-written | ✅ Auto-written | ⚠️ Manual upkeep |
| **Constitution gates** (blocking escalation on violation) | ✅ Full | ✅ Full (manual routing) | ✅ Full (manual routing) | ✅ Full (manual routing) | ✅ Full (manual routing) |
| **[NEEDS CLARIFICATION] marker resolution** | ✅ Full | ✅ Full | ✅ Full | ✅ Full | ✅ Full |
| **FEAT number assignment** | ✅ Auto (reads specs/) | ⚠️ Manual | ⚠️ Manual | ⚠️ Manual | ⚠️ Manual |
| **Parallel task execution** (`[P]` markers in tasks.md) | ✅ Full (Task tool) | ❌ Sequential only | ⚠️ Runtime-verified; probe locally | ⚠️ Unverified here; verify locally or with vendor docs | ❌ Sequential only |
| **Observer Agent** (runs alongside pipeline) | ✅ Full | ⚠️ Deferred pass only | ⚠️ Deferred pass only | ⚠️ Deferred pass only | ⚠️ Deferred pass only |
| **Memory-store / project knowledge persistence** | ✅ Auto (file writes) | ⚠️ Manual copy-out | ✅ Auto | ✅ Auto | ⚠️ Manual copy-out |

**Legend:** ✅ Full native support · ⚠️ Version-sensitive, partial, or requires verification · ❌ Not supported

---

## Host Notes

### Claude Code (full feature set)

All features work as documented. Slash commands require the one-time setup:

```bash
cp -r <AI_DEV_SHOP_ROOT>/slash-commands/ .claude/commands/
```

The Task tool enables true parallel agent dispatch and isolated context windows per agent. This is the recommended host for production use of this framework.

### Claude.ai (web)

No Task tool, no slash commands, no filesystem access. All pipeline stages run in a single conversation with manual routing. Use Option B: paste the contents of `slash-commands/<command>.md` directly as your message.

For SHA-256 hashes, compute manually using your OS shell or a web tool and paste the result into the artifact. Pipeline state file must be maintained by copy-pasting the current state into a local file between sessions.

### Codex CLI

Filesystem reads and writes work natively. Slash commands are not supported; use Option B. Bash tool available for test running.

Do not hardcode task-spawning assumptions from memory alone. Verify current capability status with `bash harness-engineering/validators/probe_host_capabilities.sh` or `codex features list`.

### Gemini CLI

Filesystem reads and writes work natively. Bash tool availability depends on your Gemini CLI configuration — verify before relying on TestRunner automation. Slash commands not supported; use Option B.

Some Gemini CLI capabilities still require local or vendor verification in this repo. If the probe cannot prove a feature, describe it as `unverified`, not `unsupported`.

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
Claude Code supports true isolated agent dispatch. Other hosts must be treated as runtime-sensitive instead of assumed from memory. Use the local capability probe to decide whether `[P]` means real parallel isolation or only a sequencing hint on the current install.

If parallel agent support is unavailable or unverified on the current host, execute `[P]` tasks sequentially and keep discovery/validation output compact so accumulated context does not sprawl.

**SHA-256 hashing on web hosts:**
Without Bash, generate hashes with `shasum -a 256 <file>` on macOS/Linux or `Get-FileHash -Algorithm SHA256 <file>` on Windows. Paste the result into the spec header. A missing or unverified hash degrades spec integrity guarantees but does not break the pipeline — flag it in the pipeline state Notes section.

**Observer Agent on non-Claude Code hosts:**
The Observer's LLM-as-judge pass and weekly scoring still work — they are read-only analysis tasks. What degrades is real-time interleaving with the pipeline. Run the Observer as a deferred pass after each feature ships rather than alongside the pipeline.
