# Skills Registry Exceptions

Use this file only when a canonical shared skill should exist on disk but should not appear in `skills-registry.md`.

Default rule: shared skills under `skills/*/SKILL.md` must be registered. This file is the narrow escape hatch for deliberate exclusions.

## Format

- one bullet per excluded skill path
- wrap the path in backticks
- explain the reason in plain language after the path

Example:

Example entry: `skills/<deprecated-skill>/SKILL.md` — deprecated but kept temporarily for migration support

## Current Exceptions

- `skills/roast/SKILL.md` — user-invoked `/roast` council (6 adversarial personas + judge); dispatched directly by the human, owned by no pipeline agent, so it has no routing row to register. Registered here instead so `validate_registry_integrity.py` passes rather than halting every later check in `run-all.sh`.
- `skills/improve-codebase-architecture/SKILL.md` — Matt Pocock skills import (2026-06-30) kept as reference material only; todo.md intake decision was to NOT register it as a first-class AI Dev Shop skill until its upstream dependencies (`/codebase-design`, `/grilling`, `subagent_type=Explore`) are mapped to native equivalents
- `skills/supabase-upstream/SKILL.md` — official Supabase vendor drop; loaded only through progressive disclosure references in `skills/supabase/SKILL.md` and `agents/database/supabase/skills.md`; not a standalone agent skill
- `skills/supabase-postgres-best-practices/SKILL.md` — official Supabase vendor drop; loaded only through progressive disclosure references in `skills/supabase/SKILL.md`, `skills/postgresql/SKILL.md`, and `agents/database/supabase/skills.md`; not a standalone agent skill
- `skills/impeccable/SKILL.md` — third-party vendor drop (pbakaus/impeccable, 2026-07-26) with its own commands, scripts, and reference docs; user-invoked frontend design/critique/polish workflow, not wired into any AI Dev Shop pipeline agent
- `skills/taste-skill/SKILL.md` — locally-authored router (mirrors `skills/expo-react-native/SKILL.md`) over 13 vendored third-party subskills from Leonxlnx/taste-skill nested at `skills/taste-skill/vendor/*/SKILL.md` (not individually registered, same as `skills/expo/skills/*/SKILL.md`); user-invoked alternative design-taste workflow, not wired into any AI Dev Shop pipeline agent
