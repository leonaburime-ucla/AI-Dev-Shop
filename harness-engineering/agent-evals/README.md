# Agent Evals

Committed seeded eval suites live here.

## Layout

- `architect-evals/`
- `code-review-evals/`
- `programmer-evals/`

Keep suite-local artifacts together:

- `run-results.tsv` — single file for both run metadata and per-seed scoring

The canonical suite definition and its retained run history should stay
colocalized under the owning agent bucket.

## Directory Naming Guide

| Name | Scope | Purpose |
|------|-------|---------|
| `eval-results/` | Run-level (`runs/run-001/eval-results/`) | Agent output from a specific eval run: the results file the agent writes during execution |

Additionally, `seed-state/eval-results/` in code-review evals contains the
**fake handoff** that is INPUT to the CR agent (part of the seeded fixture),
not agent output.

## Execution Guard (Blocking)

Each eval MUST run in its own isolated subagent context. Do not batch
multiple evals into a single subagent.

Rules:

1. **One subagent per eval.** Each eval gets a fresh subagent loaded with
   only that eval's `project-brief.md`, `prompts/`, and `seed-state/`.
   Cross-eval context bleed invalidates results.
2. **Agent persona bootstrap required.** The subagent must be bootstrapped
   with the correct agent persona per `AGENTS.md` Delegated Agent Bootstrap.
   For programmer evals, load the Programmer persona. For code-review evals,
   load the Code Review persona.
3. **No shared state between evals.** Each subagent starts from the clean
   `runs/<run-id>/` directory created by `prepare_eval_run.py`. Do not
   carry findings, context, or corrections from one eval into another.
4. **Parallel is fine, batching is not.** Running 9 subagents in parallel
   (one per eval) is encouraged. Running 1 subagent sequentially across all
   9 evals is a blocking violation.

Why: seeded evals are designed so each eval has its own independent project
brief, its own bugs, and its own fake context. Mixing eval contexts causes
the agent to import assumptions from unrelated projects, miss seeds due to
context window saturation, and produce results that cannot be scored per-eval.

## After Each Run — Coordinator Responsibilities

The subagent writes its results to `eval-results/eval-results-run.md` inside
its run directory. The coordinator (whoever dispatches the run) is responsible
for updating the suite-level `run-results.tsv` — append one row per seed with:

`run_id`, `eval_name`, `run_scope` (benchmark_full / targeted_regression),
`execution_mode` (repo_persona_subagent / repo_persona_host /
external_peer_cli), `agent`, `model_id`, `model_label`, `seed_id`,
`result` (CAUGHT / PARTIAL / MISSED / FALSE_POSITIVE), `severity_correct`,
`reviewer_notes`, `executed_at`.

The subagent must include its model name and version in the eval-results
file. The coordinator copies that into the TSV. Do not rely on the subagent
to write TSVs directly — it only has access to its own run directory.

