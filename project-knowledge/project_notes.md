# Project Notes

Use for temporary notes, open questions, and parking lot items.

## Entries

- 2026-02-21: [CONVENTION] TypeScript function signatures use a two-object paradigm throughout this codebase. First argument: required key-value pairs `{ param1, param2 }: { param1: Type1; param2: Type2 }`. Second argument: optional key-value pairs with defaults `{ opt1 = default, opt2 }: { opt1?: Type3; opt2?: Type4 } = {}`. Rationale: adding or renaming optional parameters never requires touching callsites. All code examples in `AI-Dev-Shop/skills/design-patterns/references/` follow this convention. Programmer Agent must apply it to all new functions.
