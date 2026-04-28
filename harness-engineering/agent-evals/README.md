# Agent Evals

Committed seeded eval suites live here.

Layout:

- `architect-evals/`
- `code-review-evals/`
- `programmer-evals/`

Keep suite-local artifacts together:

- `run-manifest.tsv`
- `run-results.tsv`
- `reports/`
- `runs/` when a suite retains raw execution history

The canonical suite definition and its retained run history should stay
colocalized under the owning agent bucket.

