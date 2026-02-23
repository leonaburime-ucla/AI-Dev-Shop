# Agent Performance Scorecard

Written and maintained by the Observer Agent. Tracks per-agent quality trends across pipeline runs. Feeds skills.md update decisions with evidence rather than intuition.

The Observer updates this file after each feature ships and produces a full scoring pass weekly.

---

## How Scores Are Computed

Each agent is scored on the dimensions defined in `AI-Dev-Shop/skills/evaluation/eval-rubrics.md` using LLM-as-judge methodology. Scores are 1–5 per dimension. The composite score is the unweighted mean, rounded to one decimal place.

A **regression** is a composite score drop of >1.0 vs. the agent's rolling 4-run baseline. Regressions are flagged to the Coordinator immediately, not held for the weekly report.

Scores reference specific memory-store.md `[QUALITY]` entry IDs as evidence. Scores without evidence references are not valid.

---

## Scorecard

### Spec Agent

| Run | Feature | Completeness | Testability | Ambiguity Resolution | Composite | Evidence |
|-----|---------|-------------|-------------|---------------------|-----------|---------|
| — | — | — | — | — | — | — |

**Baseline:** Not yet established (requires 4+ runs)

**Recurring issues:** None logged

**Recommended skills.md updates:** None pending

---

### Architect Agent

| Run | Feature | Pattern Fit | Complexity Justification | Composite | Evidence |
|-----|---------|------------|--------------------------|-----------|---------|
| — | — | — | — | — | — |

**Baseline:** Not yet established

**Recurring issues:** None logged

**Recommended skills.md updates:** None pending

---

### TDD Agent

| Run | Feature | AC Coverage | Test Isolation | Edge Case Coverage | Composite | Evidence |
|-----|---------|------------|---------------|-------------------|-----------|---------|
| — | — | — | — | — | — | — |

**Baseline:** Not yet established

**Recurring issues:** None logged

**Recommended skills.md updates:** None pending

---

### Programmer Agent

| Run | Feature | Spec Alignment | Test Pass Rate at Handoff | Scope Discipline | Composite | Evidence |
|-----|---------|--------------|--------------------------|-----------------|-----------|---------|
| — | — | — | — | — | — | — |

**Defect escape rate:** Not yet established
(Defect escape = Required code review findings that should have been caught before handoff, divided by total Required findings.)

**Baseline:** Not yet established

**Recurring issues:** None logged

**Recommended skills.md updates:** None pending

---

### Code Review Agent

| Run | Feature | Finding Classification Accuracy | Spec Alignment Coverage | Composite | Evidence |
|-----|---------|--------------------------------|------------------------|-----------|---------|
| — | — | — | — | — | — |

**Baseline:** Not yet established

**Recurring issues:** None logged

**Recommended skills.md updates:** None pending

---

### Security Agent

| Run | Feature | Threat Coverage | Finding Severity Accuracy | Composite | Evidence |
|-----|---------|----------------|--------------------------|-----------|---------|
| — | — | — | — | — | — |

**Baseline:** Not yet established

**Recurring issues:** None logged

**Recommended skills.md updates:** None pending

---

### Red-Team Agent

| Run | Feature | BLOCKING Accuracy | ADVISORY Signal Quality | Composite | Evidence |
|-----|---------|------------------|------------------------|-----------|---------|
| — | — | — | — | — | — |

**Baseline:** Not yet established

**Recurring issues:** None logged

**Recommended skills.md updates:** None pending

---

### Coordinator

| Run | Feature | Routing Correctness | Escalation Judgment | Budget Tracking | Composite | Evidence |
|-----|---------|--------------------|--------------------|----------------|-----------|---------|
| — | — | — | — | — | — | — |

**Baseline:** Not yet established

**Recurring issues:** None logged

**Recommended skills.md updates:** None pending

---

## Cross-Agent Trends

Updated weekly by Observer.

| Pattern | First Seen | Occurrences | Affected Agents | Status | Action |
|---------|-----------|-------------|----------------|--------|--------|
| — | — | — | — | — | — |

---

## Pending skills.md Updates

Changes backed by scorecard evidence that have not yet been applied.

| Agent | Proposed Change | Evidence (memory-store entry IDs) | Priority | Status |
|-------|----------------|----------------------------------|----------|--------|
| — | — | — | — | — |

When a pending update is applied, move it to the Amendment section of the relevant agent's skills.md, and remove it from this table.

---

## Observer Notes

_No entries yet._
