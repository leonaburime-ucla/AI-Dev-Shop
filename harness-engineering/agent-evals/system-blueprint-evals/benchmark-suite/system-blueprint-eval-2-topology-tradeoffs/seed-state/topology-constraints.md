# Topology And Constraints

- Web UI talks to backend API.
- Backend owns relational data.
- Background worker handles fulfillment sync and exports.
- Order domain emits fulfillment events.
- Hard constraint variant: no external SaaS dependencies.
- Control variant: all data owners are clearly assigned and no `[OWNERSHIP UNCLEAR]` marker is needed.

Expected behavior: present 2-3 macro directions and pause for user preference before committing when the checkpoint has not happened.
