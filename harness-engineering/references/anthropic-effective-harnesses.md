# Anthropic Effective Harnesses For Long-Running Agents Notes

Source:
- https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents

This is a local distillation for repo harness design, not a copy of the article.

## Key Takeaways

### 1. Long-Running Agents Need Durable State Outside The Context Window

Anthropic treats long-horizon work as a handoff problem, not just a prompt problem. Agents need an external progress log so fresh sessions can resume without reconstructing state from memory.

### 2. Separate Setup From Execution

A clean environment bootstrap is different from iterative coding. An initializer/setup phase can prepare tools, repo context, and progress tracking before the main coding loop starts.

### 3. Track Work As Explicit Pass/Fail Inventory

Feature or task ledgers with clear status help agents pick the next highest-value incomplete item instead of wandering.

### 4. Use Small, Durable Checkpoints

Frequent git checkpoints and short progress notes reduce recovery cost when an agent breaks the workspace or a session expires.

### 5. Protect The Verification Surface

The article is explicit that tests should not disappear just to make a run look greener. Harnesses need rules that preserve the truth surface.

## Direct Implications For AI Dev Shop

- add a durable cross-session progress artifact before relying on longer autonomous runs
- separate bootstrap/setup context from execution context when long-running sessions matter
- consider a feature-status ledger for multi-session work
- add an explicit "do not delete tests to pass the run" guardrail where appropriate
