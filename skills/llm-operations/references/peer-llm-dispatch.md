# Peer LLM Dispatch

Use this reference when one LLM is asking another LLM CLI to review, debate, or validate work.

## Default Pattern

- Build a shared packet first.
- Make the packet packet-first and work-log-first.
- Treat raw diffs, commits, or logs as supporting evidence, not the default payload.

For most toolkit-maintenance work, the packet should lead with:

1. what changed
2. why it changed
3. exact files touched
4. what was verified
5. what was not verified
6. out-of-scope local changes
7. the exact question for the external LLM

Use commit or diff references only when they materially help the auditor inspect details.

## Heavier Repo Workloads

Treat this as guidance, not a hard constraint:

- Prefer packet-first prompts plus an explicit file list before escalating to open-ended repo exploration.
- If a peer stalls, returns empty output, or behaves inconsistently on a broad repo-audit prompt, retry once with the same packet and a bounded file set.
- If the packet already names the relevant files, prefer a bounded prompt and a constrained read-only tool surface over a broad open-ended repo-audit prompt.
- Do not assume a failure on an open-ended repo audit means the peer cannot handle repo work in general; first test whether the bounded version succeeds.

## Transport Rules

- Prefer structured output modes when the peer CLI supports them.
- Parse `stdout` only as the peer answer.
- Treat `stderr` as diagnostics and save it separately.
- Keep raw offloads in local scratch by default unless the user explicitly wants retained evidence.
- Do not treat zero-byte redirected offload files from an in-flight peer process as a failure signal by themselves. Some peers, including Claude Code in this repo's packet-audit pattern, may buffer output until process exit.
- If the peer must read a packet from disk, make sure the packet lives in a peer-readable location.
- Prefer a short prompt that points the peer at the packet path over inlining the full packet body into a shell argument when a peer-readable file is available.
- When invoking peer CLIs from shell, avoid nested heredocs, large command substitutions, or other brittle quoting patterns for long prompts. Prefer a small stable prompt string or a prompt file.
- The dispatch-copy pattern is intended to be cross-platform, but it is not yet verified on native Windows shells in this repo. Current shell examples assume a Bash-compatible environment.

### Peer-Readable Packet Locations

Do not assume every peer CLI can read every local path.

- Ignored repo paths such as `.local-artifacts/` may be invisible to some tool layers.
- Generic OS temp paths such as `/tmp` may be outside the peer's allowed workspace.
- Default pattern:
  - write the authoring packet to `.local-artifacts/`
  - create a peer-readable dispatch copy in a visible workspace path such as `tmp/<workflow>-dispatch/`
  - give the peer the dispatch copy path, not the authoring path
- If needed, create a dispatch copy inside:
  - the repo workspace, if the peer can read it there, or
  - the host's documented project temp/workspace path
- Do not put the dispatch copy under a gitignored or tool-ignored path if the peer needs to read it with file tools.

If the packet is copied for dispatch, record both:

- `authoring packet`: where the coordinator wrote it
- `dispatch packet`: the peer-readable path actually given to the external LLM

### Readability Probe

Before the full peer review or debate call, run a cheap readability probe against the dispatch packet.

- Ask the peer to read the dispatch packet and echo the first Markdown heading or another small deterministic string from it.
- If that probe fails because the path is ignored, unreadable, or out of workspace, classify it as `path_or_permission_failure`.
- Fix the dispatch path and retry once before spending tokens on the real task.
- Do not treat a failed readability probe as model disagreement or reasoning failure.

### Live-Run Observation

While the peer process is still running:

- Treat process liveness and elapsed wall-clock time as the primary signal, not the current byte count of redirected stdout/stderr files.
- For Claude Code packet-first audits, expect that stdout may not appear until the process exits.
- Do not classify a Claude run as stalled just because redirected stdout/stderr files remain empty while the process is alive.
- Keep `audit_timeout_seconds` as the hard ceiling.
- If you need a soft "this may be hung" threshold for Claude packet audits, use roughly `90s` before suspicion instead of `30-40s`.

### Dispatch Cleanup

Dispatch copies are transport artifacts, not primary evidence.

- Keep the authoring packet in `.local-artifacts/` or `reports/` according to the user's retention choice.
- Delete temporary dispatch copies after the peer run finishes unless the user explicitly asks to retain them.
- If the dispatch copy is retained temporarily for troubleshooting, say so and clean it up before closing the task when feasible.

## Failure Classification

Classify peer failures before retrying:

- `path_or_permission_failure`: peer could not read the packet or target files
- `capacity_or_rate_limit`: `429`, `503`, provider-capacity exhaustion
- `timeout`
- `malformed_or_no_output`
- `empty_result_transport_failure`: peer exited successfully but returned an empty answer body
- `truncated_output`

Only retry transient transport failures such as `429` and `503` by default.
Do not treat path/permission failures as model reasoning failures.
Fix the path, then retry once with the corrected dispatch copy.
Only classify `empty_result_transport_failure` after the peer process has exited successfully and stdout is still empty.
If a broad packet-based audit returns `empty_result_transport_failure`, retry once with a tighter prompt, a bounded file set, and a constrained read-only tool surface when the peer supports it.

## Model And Prompt Hygiene

- Pin the model when the user requests it or when reproducibility matters.
- If the workflow promises exact model reporting, do not dispatch on an inferred or alias-only model. Require an explicit or locally proven exact model name/version before running.
- Keep the ask explicit: what to inspect, what to ignore, what output shape to return.
- Require strengths as well as findings so the user sees what should stay unchanged.

## Capability Discovery

Use these sources in this order:

1. local capability probes in `harness-engineering/validators/`
2. `project-knowledge/routing/capability-probes.tsv`
3. `project-knowledge/routing/compatibility-matrix.md`
4. host-specific smoke-test artifacts when they exist

Useful local references:

- `harness-engineering/validators/probe_host_capabilities.sh`
- `harness-engineering/validators/resolve_subagent_mode.sh`
- `project-knowledge/routing/capability-probes.tsv`
- `project-knowledge/routing/compatibility-matrix.md`
- `skills/swarm-consensus/references/cli-smoke-test.md`

## Reusable Rule

If a peer-LLM interaction pattern turns out to be host-sensitive, move it into a shared reference like this one instead of copying the rule into one command only.
