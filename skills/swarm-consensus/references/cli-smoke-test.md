# Swarm Consensus CLI Smoke Test

Use this before changing preferred peer models, updating flag recommendations, or trusting a new CLI release.

What this does:

- checks which flag orderings and output modes still work on the current host
- compares text vs structured output where available
- shows whether the peer answer survives end-marker parsing
- shows how much diagnostic noise lands on `stderr`
- helps detect repo-local behavior differences, especially for `codex exec`

Run it with current preferences:

```bash
python3 skills/swarm-consensus/scripts/cli_smoke_test.py \
  --claude-model sonnet \
  --gemini-model gemini-3.1-pro-preview \
  --codex-model gpt-5.4 \
  --save-artifact
```

Run Codex in an isolated directory to compare raw CLI behavior against repo-local behavior:

```bash
python3 skills/swarm-consensus/scripts/cli_smoke_test.py \
  --codex-model gpt-5.4 \
  --codex-cd /tmp \
  --save-artifact
```

Suggested operating pattern:

- run a dated baseline once after setting up consensus on a host
- rerun after CLI upgrades, major model-family changes, or parser regressions
- save ad hoc runs in `.local-artifacts/swarm-consensus/smoke-tests/` by default
- only write to `framework/reports/swarm-consensus/smoke-tests/` when you explicitly want a retained host baseline in the repo
- treat the saved artifact as evidence for updating saved model preferences or slash-command guidance

Interpretation rules:

- prefer cases that keep the answer in `stdout` and diagnostics in `stderr`
- prefer structured output when it still preserves the peer answer cleanly
- if a model flag fails, do not update the slash command to assume it; confirm the correct flag pattern first
- if a newer model family looks better, update the saved preference only after rerunning this test
- runtime consensus runs should still show inferred models to the user and allow per-run overrides
