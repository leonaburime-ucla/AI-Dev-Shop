---
name: codebase-analysis
version: 1.0.0
last_updated: 2026-02-22
description: Use when analyzing an existing codebase for architectural flaws, coupling issues, missing abstractions, code quality problems, or security surface before starting a new pipeline run. Produces a structured findings report using token-efficient phased analysis that scales to large codebases.
---

# Skill: Codebase Analysis

Analyzing an existing codebase requires token discipline. Reading every file is not viable for production codebases. This skill uses a three-phase approach that builds a complete picture through targeted reads rather than exhaustive ones.

Reports are saved to `AI-Dev-Shop/codebase-analysis/` — not kept in context. This makes findings persistent and loadable by the `architecture-migration` skill in a separate session.

## Token Budget Before You Start

Estimate codebase size before any reads. Check file count with a single directory listing.

| Codebase Size | File Count | Approach |
|---|---|---|
| Small | < 50 files | Full analysis, single report |
| Medium | 50–500 files | Phased analysis, single report |
| Large | 500–5,000 files | Phased analysis, report split by module |
| Very large | 5,000+ files | Ask user which modules to focus on |

For very large codebases, stop and ask: *"This codebase has approximately [N] files. Should I analyze by module (multiple sessions) or focus on a specific area first?"*

**Always exclude**: `node_modules/`, `vendor/`, `dist/`, `build/`, `.git/`, generated files, lock files.

## Phase 1 — Discovery (Minimal Tokens)

Goal: understand the codebase shape without reading code.

1. Directory tree to depth 3 (excluding dirs above)
2. Read: `package.json` / `pyproject.toml` / `Cargo.toml` / `go.mod`
3. Read: `tsconfig.json`, `eslint.config.*` if present
4. Read: `README.md` (first 80 lines only if large)
5. Read: `ARCHITECTURE.md`, `DESIGN.md`, or `docs/` index if present

**Output of Phase 1:**
- Detected language(s) and framework(s)
- Apparent architectural intent
- Module/folder map with file count per module
- Red flags visible from structure alone (no `domain/` folder in a claimed DDD project, no test files anywhere, all code in root directory)

## Phase 2 — Architecture Scan (Targeted Reads)

Goal: identify structural violations and dependency direction problems.

1. Read entry points in full (main.ts, index.ts, app.py — usually short)
2. For each top-level module folder: read its index file or first 50 lines of the largest file
3. Grep import/dependency patterns across key files (`import.*from`, `require(`)
4. Check dependency direction: does `domain/` import from `infrastructure/`? Does `routes/` contain business logic?
5. Check for circular dependency indicators

**Output of Phase 2:**
- Layer map: what layers exist vs what the apparent pattern requires
- Dependency direction violations (with file and line locations)
- Coupling hotspots (files imported by many others)
- Missing layers (no service layer, no repository interfaces, no domain folder)

## Phase 3 — Code Sampling (Controlled Reads)

Goal: quality indicators, naming, missing abstractions, security surface.

Rules:
- One representative file per module/layer, maximum 100 lines each
- For test coverage: check file existence only — do not read test files
- For security: grep for risk patterns rather than reading full files

Security grep patterns (flag, do not diagnose):
- Hardcoded strings matching key/secret patterns: `(?i)(api_?key|secret|password|token)\s*=\s*['"][^'"]{8,}`
- Direct SQL strings: `SELECT.*FROM`, `INSERT INTO`, `UPDATE.*SET`
- Dangerous evals: `eval(`, `exec(`, `Function(`
- Direct filesystem access in unexpected layers

**Output of Phase 3:**
- Code quality indicators (oversized files/functions, naming drift, missing types)
- Missing abstractions (no interfaces for external dependencies)
- Test coverage signal: which modules have test files, which don't
- Security surface flags (for Security Agent to review — not a full audit)
- Dead code indicators (unreferenced exports, commented-out blocks)

## Findings Report Format

**Small/medium codebases:** Save as `AI-Dev-Shop/codebase-analysis/ANALYSIS-<id>-<YYYY-MM-DD>.md`

**Large codebases:** Split into named parts:
- `ANALYSIS-<id>-<date>-part1-structure.md`
- `ANALYSIS-<id>-<date>-part2-dependencies.md`
- `ANALYSIS-<id>-<date>-part3-quality.md`

Each part is self-contained. `architecture-migration` can load individual parts without loading all.

```markdown
# Codebase Analysis: <project-name>

- Analysis ID: ANALYSIS-001
- Date: <ISO-8601 UTC>
- Analyst: CodeBase Analyzer Agent
- Parts: 1 of 1

## Executive Summary

- Language/Framework: TypeScript / Express
- Apparent Pattern Intent: Layered Architecture
- Files Analyzed: 47 of 312 total (excluded: node_modules, dist)
- Severity Counts: Critical: 2 | High: 5 | Medium: 8 | Low: 4
- Current State Classification: Layered (degraded)

## Findings

### FLAW-001
- Severity: Critical
- Category: Architecture Violation
- Location: `src/routes/invoice.ts:89–120`

Business logic (invoice total calculation, tax computation) implemented directly
in route handler. Cannot unit-test business rules without spinning up HTTP server.
Any reuse requires copy-paste duplication.

Evidence: Lines 89–120 perform calculations and apply business rules inline.
These have zero test coverage outside integration tests.

---

### FLAW-002
...

## What Was Not Analyzed

Due to token budget, the following were sampled but not fully read:
- `src/legacy/` (14 files — no test coverage detected)
- `src/integrations/` (8 files — entry points only)

## Recommended Next Step

Load this report into `AI-Dev-Shop/skills/architecture-migration/SKILL.md`
to generate a migration plan.
```

## Flaw Categories and Severity

**Critical** — Structural problems that block testability, safety, or extensibility:
- Business logic in route handlers or controllers
- Direct database access with no abstraction layer
- No separation between external dependencies and core logic
- Circular module dependencies

**High** — Significant debt with clear negative impact:
- Missing interfaces for external dependencies (database, email, payment providers)
- God files (single file > 500 lines with mixed responsibilities)
- No test files in any module
- Hardcoded credentials or config values

**Medium** — Accumulating debt that will slow future work:
- Naming that doesn't match domain language
- Logic duplicated across 3+ files
- Functions > 50 lines with multiple responsibilities
- Missing error handling on external calls

**Low** — Quality issues that don't block but degrade maintainability:
- Dead code (unreferenced exports, commented-out blocks)
- Naming drift (names that no longer match what the code does)
- Missing type annotations in typed languages
- Debug statements or console.log in production paths

## Analysis Anti-Patterns

**Reading too much**: Full file reads for every file defeats the purpose. Use the phase structure.

**Symptom counting over root causes**: "47 problems" is less useful than "one Critical structural violation causing most of the other issues." Identify roots.

**Judging without context**: A 500-line file may be appropriate for a configuration registry. Understand intent before classifying.

**Skipping the executive summary**: The summary is what `architecture-migration` uses as primary input. Make it precise — current state classification and severity counts are mandatory.
