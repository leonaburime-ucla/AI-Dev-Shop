# Handoff Traps

A valid blueprint must include:

- One explicit P0 Core/Foundation package.
- P0 kept thin, with no feature-owned schema or business logic.
- Critical User Journeys that cross domains.
- Spec decomposition table with Depends on filled for API/event/schema dependencies.
- Handoff to Spec with approved boundaries and unresolved decisions.

Horizontal slicing is only valid for shared platform/foundation work when explicitly justified.
