---
name: codebase-graph
version: 0.1.0
last_updated: 2026-06-06
description: Use when Coordinator or CodeBase Analyzer needs a persistent Graphify map of a repo, stale graph detection, or query-first codebase navigation. Wraps upstream Graphify with AI Dev Shop capability checks and human checkpoints.
---

# Skill: Codebase Graph

This skill lets AI Dev Shop use Graphify as a reusable repo map without letting
Graphify bypass harness policy.

## Ownership

- Upstream checkout location: `<AI_DEV_SHOP_ROOT>/integrations/graphify/upstream/`
- Upstream skill reference: `<AI_DEV_SHOP_ROOT>/integrations/graphify/upstream-skill/codex/SKILL.md`
- Capability check: `<AI_DEV_SHOP_ROOT>/harness-engineering/validators/check_graphify_capability.sh`
- Freshness check: `<AI_DEV_SHOP_ROOT>/harness-engineering/validators/check_graphify_freshness.py`
- Per-target Graphify output: `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/graphify-out/<target-name>/`
- Graphify run path: set `GRAPHIFY_OUT` to the per-target reports directory before invoking the CLI
- ADS freshness metadata: `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/graphify-out/<target-name>/.ads-graphify-status.json`

Target-named folders under `reports/graphify-out/` are storage namespaces, not
target-local output. For example, `reports/graphify-out/harness-engineering/`
is allowed; `<AI_DEV_SHOP_ROOT>/harness-engineering/graphify-out/` is not.

Do not put downloaded Graphify source under `harness-engineering/`. Harness owns
checks and policy; `integrations/graphify/` owns third-party source references.

## Capability Check

Before relying on Graphify, run:

```bash
bash <AI_DEV_SHOP_ROOT>/harness-engineering/validators/check_graphify_capability.sh
```

Interpret status conservatively:

- `enabled`: `graphify` CLI is installed and usable now.
- `unverified`: managed upstream checkout exists, but the CLI is not installed.
- `unavailable`: neither CLI nor managed checkout is present.

If the user explicitly wants Graphify and the managed checkout is missing, run:

```bash
bash <AI_DEV_SHOP_ROOT>/harness-engineering/validators/check_graphify_capability.sh --download
```

If the user asks to update the managed checkout, run:

```bash
bash <AI_DEV_SHOP_ROOT>/harness-engineering/validators/check_graphify_capability.sh --update
```

If the user asks to refresh the copied upstream skill reference after an
upstream update, run:

```bash
bash <AI_DEV_SHOP_ROOT>/harness-engineering/validators/check_graphify_capability.sh --sync-skill
```

Downloading or updating Graphify is a human-approved action. Do not silently
clone or pull third-party code during ordinary analysis.

## Default Safety Policy

Default to code-only structural graphing. Do not run any of these unless the
user explicitly requests or approves it:

- `graphify extract <path>` full semantic extraction
- `--mode deep`
- docs/PDF/image/video/audio semantic extraction
- `graphify global add` or `graphify extract --global`
- `graphify hook install`
- `graphify watch`
- Neo4j push, MCP server, or other long-running integrations

The safe default command after a CLI is available is:

```bash
GRAPHIFY_OUT="$(python3 <AI_DEV_SHOP_ROOT>/harness-engineering/validators/check_graphify_freshness.py <TARGET_REPO> --prepare-output --print-output-path)" \
  graphify update <TARGET_REPO> --force
```

Always pass `--force` — without it, incremental runs duplicate existing edges.
Graphify's `update` is pure AST extraction (zero tokens), so a full re-extract
is cheap and correct.

`--prepare-output --print-output-path` creates
`<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/graphify-out/<target-name>/` and prints
that path for `GRAPHIFY_OUT`. Do not let Graphify create a real
`<TARGET_REPO>/graphify-out/` directory. If an older non-empty
`<TARGET_REPO>/graphify-out/` directory already exists, rerun the prepare step
with `--migrate-existing-output` to move that generated output into the reports
location before running Graphify again.

Use `--no-cluster` when the user wants the cheapest structural pass and does not
need community/report output:

```bash
GRAPHIFY_OUT="$(python3 <AI_DEV_SHOP_ROOT>/harness-engineering/validators/check_graphify_freshness.py <TARGET_REPO> --prepare-output --print-output-path)" \
  graphify update <TARGET_REPO> --force --no-cluster
```

## Freshness Metadata

After creating or updating a graph, write freshness metadata:

```bash
python3 <AI_DEV_SHOP_ROOT>/harness-engineering/validators/check_graphify_freshness.py <TARGET_REPO> --write --mode code_update
```

For an approved semantic pass, add:

```bash
python3 <AI_DEV_SHOP_ROOT>/harness-engineering/validators/check_graphify_freshness.py <TARGET_REPO> --write --mode semantic_extract --semantic-enabled --human-approved-semantic
```

The metadata file is
`<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/graphify-out/<target-name>/.ads-graphify-status.json`
and includes:

```json
{
  "generated_at": "YYYY-MM-DDTHH:MM:SSZ",
  "target_root": "<absolute path>",
  "graph_output_dir": "<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/graphify-out/<target-name>",
  "target_git_head": "<git sha or null>",
  "target_dirty": true,
  "latest_source_mtime": "YYYY-MM-DDTHH:MM:SSZ",
  "graph_json_mtime": "YYYY-MM-DDTHH:MM:SSZ",
  "graphify_version": "<graphify --version output>",
  "mode": "code_update",
  "semantic_enabled": false,
  "human_approved_semantic": false
}
```

A graph is stale when any of these are true:

- `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/graphify-out/<target-name>/graph.json` is missing
- status metadata is missing
- `target_git_head` differs from the current target repo `HEAD`
- the target repo is dirty and the graph was generated before the changed files
- the current task requires semantic/docs/media coverage but the status says
  `semantic_enabled: false`

Check freshness mechanically:

```bash
python3 <AI_DEV_SHOP_ROOT>/harness-engineering/validators/check_graphify_freshness.py <TARGET_REPO>
```

When stale, prefer the `GRAPHIFY_OUT=... graphify update <TARGET_REPO> --force`
command above for code questions. Ask for human approval before escalating to
semantic extraction.

## Query-First Use

When a fresh graph exists and the user asks a codebase or architecture question,
query the graph before broad raw-file discovery:

```bash
graphify query "<question>" --graph <ADS_PROJECT_KNOWLEDGE_ROOT>/reports/graphify-out/<target-name>/graph.json
graphify path "<A>" "<B>" --graph <ADS_PROJECT_KNOWLEDGE_ROOT>/reports/graphify-out/<target-name>/graph.json
graphify explain "<concept>" --graph <ADS_PROJECT_KNOWLEDGE_ROOT>/reports/graphify-out/<target-name>/graph.json
```

If the query result is insufficient, say so and fall back to targeted source
inspection. Do not present graph-inferred relationships as fact without the
confidence and source evidence returned by Graphify.

## Agent Usage

Coordinator uses this skill for:

- deciding whether Graphify is available
- enforcing human checkpoints before expensive or persistent Graphify modes
- routing CodeBase Analyzer with graph evidence when available

CodeBase Analyzer uses this skill for:

- initial repo map discovery
- dependency hotspot hints
- query-first architecture exploration before token-heavy sampling

Graphify evidence supplements CodeBase Analyzer sampling. It does not remove the
Sampling Notice requirement in `skills/codebase-analysis/SKILL.md`.
