# Maintenance Reports

This folder stores generated maintenance reports used by recurring harness cleanup passes.

The scheduled maintenance workflow refreshes `harness-maintenance.md` and can open a small PR when the generated report changes.

Host capability reports are environment-specific and should be generated on demand rather than committed as universal truth. Use:

```bash
bash harness-engineering/validators/probe_host_capabilities.sh --md reports/maintenance/host-capabilities.md --json reports/maintenance/host-capabilities.json
```
