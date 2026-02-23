# Benchmarks

A fixed set of reference inputs and expected outputs for each agent role. The Observer uses these to detect regressions when agent `skills.md` files change.

---

## Structure

```
benchmarks/
  spec-agent/
    sample-001-simple-crud/
      input.md          — the user's feature description
      expected-output.md — what a good spec looks like
      baseline-score.md  — Observer's last recorded score against the rubric
  architect-agent/
    sample-001-/
      ...
  tdd-agent/
  programmer-agent/
  code-review-agent/
  security-agent/
```

---

## How to Use

### Regression Detection (run after any skills.md change)

1. Pass `input.md` to the relevant agent with no other context
2. Score the output using `AI-Dev-Shop/skills/evaluation/eval-rubrics.md`
3. Compare to `baseline-score.md` — if overall score drops more than **1.0/10.0**, treat as a regression
4. Either revert the skills.md change or improve it until score recovers

### Release Gate

Do not ship changes to agent instructions that cause a regression of more than **1.0/10.0** on any dimension, or more than **0.5/10.0** on overall average, for the agent being changed.

---

## Adding Benchmarks

When a new failure pattern is resolved that took 3+ cycles, it is a good candidate for a benchmark:

1. Create a new `sample-NNN-<short-name>/` folder under the relevant agent
2. Write `input.md` — the input that caused the problem (sanitized)
3. Write `expected-output.md` — what the correct output looks like
4. Run the agent against it and record the score in `baseline-score.md`
5. The Observer should reference this benchmark in its next pattern report

---

## Baseline Score Format

```markdown
# Baseline Score: <agent> / <sample-name>

- Scored by: Observer Agent
- Date: <ISO-8601 UTC>
- Skills.md version: <hash or description>

| Dimension | Score |
|-----------|-------|
| <dimension 1> | 8.0 |
| <dimension 2> | 7.5 |

Overall: 7.75 / 10.0
Notes: <what to watch — any dimension scoring below 7.0>
```
