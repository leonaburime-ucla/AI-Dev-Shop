# Project Memory

Use for stable project-specific nuances and conventions.

> **Routing authority:** Before writing any new entry to this file, read `AI-Dev-Shop/project-knowledge/knowledge-routing.md`. That file determines which memory file is the correct destination for any given content type. Only content classified as a stable convention, gotcha, constraint, or project-wide pattern belongs here.

## Entries

- YYYY-MM-DD: <fact/convention/gotcha>

- 2026-02-23: [CONVENTION] TypeDoc/JSDoc is required on all newly created functions, including nested functions and local helper functions defined inside other functions. Applies to all agents writing TypeScript or JavaScript. Every parameter, return type, and thrown error must be documented. Functions with non-obvious behavior must include a `@remarks` or inline prose explanation.

- 2026-02-23: [CONVENTION] Object parameter ordering: required fields must come first, optional fields must come second. This applies to all TypeScript interfaces, type aliases, and function parameter destructuring patterns throughout the codebase. Required fields are those without a `?` modifier or a default value. Optional fields are those with a `?` modifier or a default value. Mixing required and optional fields arbitrarily is a code review deficiency.

- 2026-02-23: [CONVENTION] Page orchestrator prop defaults to the concrete orchestrator used internally. When a page component accepts an orchestrator as a prop (for testability or dependency injection), the prop must be typed as the interface or abstract type, and the default value must be the concrete orchestrator instance used in production. Pattern: `{ orchestrator = concreteOrchestratorInstance }: { orchestrator?: OrchestratorInterface } = {}`. This enables tests to inject a mock while production pages require no explicit prop.
