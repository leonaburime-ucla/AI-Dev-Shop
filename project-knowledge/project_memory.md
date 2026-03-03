# Project Memory

Use for stable project-specific nuances and conventions.

> **Routing authority:** Before writing any new entry to this file, read `<AI_DEV_SHOP_ROOT>/project-knowledge/knowledge-routing.md`. That file determines which memory file is the correct destination for any given content type. Only content classified as a stable convention, gotcha, constraint, or project-wide pattern belongs here.

## Entries

- YYYY-MM-DD: <fact/convention/gotcha>

- 2026-02-23: [CONVENTION] Inline documentation is required on all newly created functions, methods, classes, and modules — including nested functions, local helpers, and callbacks. Every parameter, return type, and thrown error must be documented. Functions with non-obvious behavior must include an explanation of intent. Use the language's idiomatic format: TypeDoc/JSDoc for TypeScript/JavaScript, docstrings for Python, Rustdoc for Rust, Javadoc for Java, XML doc comments for C#, etc. There are no exceptions for "small" or "obvious" functions.
- 2026-02-28: [CONVENTION] If multiple skills conflict on implementation guidance, agents must follow `project-knowledge/skill-conflict-resolution.md`: report the conflict, present Option A (boundary-safe) and Option B (tactical), ask the user which to apply, and default to Option A if no choice is provided.
- 2026-02-28: [CONVENTION] React/Next.js tasks must follow `project-knowledge/react-skill-operations.md` preflight loading and precedence rules, and use the "React strict mode" shortcut when deterministic skill injection is requested.
- 2026-03-03: [TERMINOLOGY] "Big Four" means coverage metrics in this exact order: `% Stmts | % Branch | % Funcs | % Lines`. "Big Five" means Big Four plus `Uncovered Line #s`.
