# Offloads

Use this folder for large logs, diffs, traces, JSON blobs, and other artifacts that should not stay inline in chat or handoff text.

Use `<AI_DEV_SHOP_ROOT>/harness-engineering/context-offloading.md` as the rule set and `<AI_DEV_SHOP_ROOT>/templates/context-offload-template.md` as the default markdown format.

Suggested layout:

```text
reports/offloads/
  <workstream>/
    <timestamp>-<slug>.md
    <timestamp>-<slug>.txt
```

Feature-bound offloads can also live under `reports/pipeline/<NNN>-<feature-name>/offloads/` when the evidence belongs tightly to one feature run.
