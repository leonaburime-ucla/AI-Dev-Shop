# Architect Evals

Canonical Architect suites:

- `benchmark-suite`

Status:

- `benchmark-suite` is active and committed; use the suite-local validator/status output to determine whether it is exploratory, pilot, benchmark, or stable benchmark.

Architect-specific notes:

- the benchmark suite extends the shared eval schema with architecture-family,
  conditional-skill activation metadata, domain_complexity, complexity_category,
  and engineering_concepts columns
- the suite covers both **scorecard/ADR behavior** (original seeds SEED-AR-01
  through SEED-AR-59) and **system-design skill application** (seeds
  SEED-AR-60 through SEED-AR-116) — testing capacity reasoning, operational
  depth patterns, tradeoff articulation, anti-pattern avoidance, design
  checklist compliance, and conditional depth activation
- system-design seeds test the agent's use of
  `skills/system-design/SKILL.md` + all references including
  `operational-depth-patterns.md` — the scorer reports per-skill_source
  catch rates so skill gaps are directly visible
- 9 Easy standard seeds were pruned from the original scorecard set to
  improve overall suite complexity (Easy controls retained)
