---
name: codebase-graph
version: 0.2.0
last_updated: 2026-06-25
description: Use when Coordinator or CodeBase Analyzer needs an optional local codebase graph backend, stale graph detection, or query-first codebase navigation. Wraps Graphify and Codebase Memory MCP with AI Dev Shop capability checks and human checkpoints.
---

# Skill: Codebase Graph

This skill lets AI Dev Shop use optional local graph backends as reusable repo
maps without letting third-party tools bypass harness policy.

Supported backends:

- **Codebase Memory MCP**: persistent local knowledge graph exposed through CLI
  and MCP tools. Best first choice for file/symbol lookup, source snippets,
  architecture summaries, and change-impact checks.
- **Graphify**: structural graph extraction with dependency/community mapping,
  graph reports, and query/path/explain commands. Best when community reports or
  Graphify-specific traversal are useful.

Direct `rg` and file reads remain the mandatory fallback and the validation path
for important conclusions.

## Ownership

- Upstream checkout location: `<AI_DEV_SHOP_ROOT>/integrations/graphify/upstream/`
- Upstream skill reference: `<AI_DEV_SHOP_ROOT>/integrations/graphify/upstream-skill/codex/SKILL.md`
- Capability check: `<AI_DEV_SHOP_ROOT>/harness-engineering/validators/check_graphify_capability.sh`
- Freshness check: `<AI_DEV_SHOP_ROOT>/harness-engineering/validators/check_graphify_freshness.py`
- Per-target Graphify output: `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/graphify-out/<target-name>/`
- Graphify run path: set `GRAPHIFY_OUT` to the per-target reports directory before invoking the CLI
- ADS freshness metadata: `<ADS_PROJECT_KNOWLEDGE_ROOT>/reports/graphify-out/<target-name>/.ads-graphify-status.json`
- Codebase Memory MCP upstream checkout: `<AI_DEV_SHOP_ROOT>/integrations/codebase-memory-mcp/upstream/`
- Codebase Memory MCP binary: `<AI_DEV_SHOP_ROOT>/integrations/codebase-memory-mcp/bin/codebase-memory-mcp`
- Codebase Memory MCP capability check: `<AI_DEV_SHOP_ROOT>/harness-engineering/validators/check_codebase_memory_capability.sh`
- Codebase Memory MCP local cache home: `<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/codebase-memory-mcp-home/`
- Codebase Memory MCP setup docs: `<AI_DEV_SHOP_ROOT>/integrations/codebase-memory-mcp/README.md`

Target-named folders under `reports/graphify-out/` are storage namespaces, not
target-local output. For example, `reports/graphify-out/harness-engineering/`
is allowed; a generated `graphify-out` directory inside `harness-engineering`
is not.

Do not put downloaded third-party source under `harness-engineering/`. Harness
owns checks and policy; `integrations/` owns third-party source references.

## Backend Selection

Before broad codebase discovery, check both optional backends:

```bash
bash <AI_DEV_SHOP_ROOT>/harness-engineering/validators/check_codebase_memory_capability.sh
bash <AI_DEV_SHOP_ROOT>/harness-engineering/validators/check_graphify_capability.sh
```

Interpret results conservatively:

- `enabled`: backend is usable now.
- `unverified`: some local assets exist, but a required executable/config path
  is missing or not proven.
- `unavailable`: no usable local installation was found.

Default preference:

1. Use Codebase Memory MCP for file/symbol lookup, architecture summary,
   `detect_changes`, `get_code_snippet`, and MCP-native workflows.
2. Use Graphify for community reports, Graphify graph traversal, and as a
   fallback structural map when Codebase Memory MCP is unavailable.
3. Use direct `rg`/file reads when both backends are unavailable, stale, too
   noisy, or insufficiently specific.

If neither backend is available and the target is large or unfamiliar, explain
the options and ask before downloading or installing either one. Do not silently
clone, pull, run remote installers, configure MCP clients, install hooks, or
write agent config.

Suggested explanation:

> AI Dev Shop can optionally use a local codebase graph backend before broad
> source reading. Codebase Memory MCP builds a persistent local knowledge graph
> with CLI/MCP tools for file search, symbol lookup, snippets, architecture, and
> change impact. Graphify builds a structural dependency/community graph and
> report. Both are local optional integrations under `integrations/`. Do you
> want me to set up one, or proceed with direct `rg` and file reads?

## Codebase Memory MCP Capability Check

Before relying on Codebase Memory MCP, run:

```bash
bash <AI_DEV_SHOP_ROOT>/harness-engineering/validators/check_codebase_memory_capability.sh
```

If the status is `enabled`, index or refresh the target. Use the local
integration binary when the capability report says `Local binary: enabled`;
otherwise use `codebase-memory-mcp` from `PATH` when the report says
`PATH binary: enabled`.

```bash
HOME="<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/codebase-memory-mcp-home" \
  <CODEBASE_MEMORY_COMMAND> \
  cli index_repository '{"repo_path":"<TARGET_REPO>"}'
```

Then query through CLI tools:

```bash
HOME="<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/codebase-memory-mcp-home" \
  <CODEBASE_MEMORY_COMMAND> \
  cli get_architecture '{"project":"<PROJECT_NAME>","aspects":["all"]}'

HOME="<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/codebase-memory-mcp-home" \
  <CODEBASE_MEMORY_COMMAND> \
  cli search_graph '{"project":"<PROJECT_NAME>","name_pattern":".*Handler.*","limit":20}'

HOME="<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/codebase-memory-mcp-home" \
  <CODEBASE_MEMORY_COMMAND> \
  cli detect_changes '{"project":"<PROJECT_NAME>"}'
```

Set `<CODEBASE_MEMORY_COMMAND>` to
`<AI_DEV_SHOP_ROOT>/integrations/codebase-memory-mcp/bin/codebase-memory-mcp`
for the local integration binary or `codebase-memory-mcp` for a PATH install.
Use `list_projects` after indexing to resolve the generated project name. The
current binary may not expose every README-advertised tool through CLI mode; if a
tool returns `unknown tool`, report that and fall back to available tools or
direct source reads.

If `search_code` returns zero results for a term known to exist in source files,
fall back to direct `rg`. Graph-indexed text search may not cover all raw file
content, especially non-structural literals and documentation strings.

## Graphify Capability Check

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

For Codebase Memory MCP, prefer exact structural searches first, then retrieve
source snippets:

```bash
HOME="<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/codebase-memory-mcp-home" \
  <CODEBASE_MEMORY_COMMAND> \
  cli search_graph '{"project":"<PROJECT_NAME>","name_pattern":".*Graphify.*","limit":20}'

HOME="<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/codebase-memory-mcp-home" \
  <CODEBASE_MEMORY_COMMAND> \
  cli get_code_snippet '{"project":"<PROJECT_NAME>","qualified_name":"<QUALIFIED_NAME>"}'

HOME="<ADS_PROJECT_KNOWLEDGE_ROOT>/.local-artifacts/codebase-memory-mcp-home" \
  <CODEBASE_MEMORY_COMMAND> \
  cli search_code '{"project":"<PROJECT_NAME>","pattern":"literal text","limit":20}'
```

For direct fallback, use `rg`, `rg --files`, `sed`, and focused file reads.
Record that the result came from direct source inspection rather than graph
evidence.

## Agent Usage

Coordinator uses this skill for:

- deciding whether Codebase Memory MCP or Graphify is available
- enforcing human checkpoints before downloading, installing, configuring MCP,
  installing hooks, or running persistent background modes
- routing CodeBase Analyzer with graph evidence when available

CodeBase Analyzer uses this skill for:

- initial repo map discovery
- dependency hotspot hints
- file/symbol lookup before token-heavy sampling
- query-first architecture exploration before broad source reads

Graph backend evidence supplements CodeBase Analyzer sampling. It does not
remove the Sampling Notice requirement in `skills/codebase-analysis/SKILL.md`.
