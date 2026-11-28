---
name: anti-over-engineering
version: 1.1.0
last_updated: 2026-11-27
description: Use when scoping, implementing, or reviewing a code change with a real simplification decision, or when explicitly auditing code bloat. Find the smallest complete change and show what it preserves.
---

# Anti-Over-Engineering

## Choose the smallest complete change

Use [Implementation Guardrails — Before You Write](../implementation-guardrails/SKILL.md#before-you-write) as the only decision ladder. Reuse its `Reuse` evidence. Do not run a second search or create a second checklist.

In the existing plan or handoff, name what must move together: affected callers, public contracts, tests, fixtures, config, and exports. Follow the real flow, including external consumers when the contract is published. Keep unrelated cleanup out of the task. For bug fixes, use [Systematic Debugging](../systematic-debugging/SKILL.md) and fix the shared cause once.

## Keep the governing constraints

For Tovu and Jini, inject everything, pass all hooks as props, keep the `(required, _optional = {})` pad where applicable, keep functions at 50 lines or fewer and complexity at 10 or less, write tests first, and add no re-export shells. Split by responsibility rather than creating forwarding helpers to meet a cap. Respect Jini First and existing ownership. A required port, hook prop, or thin adapter is not speculative just because it has one implementation.

Use [Coding Foundations](../coding-foundations/SKILL.md), [Testable Design Patterns](../testable-design-patterns/SKILL.md), and [Test Design](../test-design/SKILL.md) for the governing checks. Do not trade away correctness, trust-boundary validation, fail-fast behavior, data-loss prevention, security, accessibility, or required test evidence for a smaller diff. Keep validation and error behavior when moving code.

## Prove a cut before making it

Use [Refactor Patterns](../refactor-patterns/SKILL.md) for removal and [Code Inspection](../code-inspection/SKILL.md) for findings and disposition. Before calling a path dead, check config, flags, dynamic registration, string references, and published consumers as applicable. Name the concrete smaller alternative and the behavior it preserves, or give evidence that the behavior is retired. Remove only superseded wiring and artifacts. Preserve certified coverage for behavior that remains. If retirement or contract breakage needs an owner decision, report it without making the cut.

When an allowed simplification has a real ceiling, record `shortcut: <limit>; revisit when <observable trigger>` at the relevant code or in the existing handoff. Do not add speculative machinery or a separate ledger.

## Report the result

For a real production diff, report `Production LOC: +A / -D (net N)` against the task's comparison base. Use `git diff --numstat` or equivalent, including new files in the task diff. Exclude tests, docs, generated files, and vendored code. Report cross-repo moves on both sides. If net lines rose, say what requirement or fix needed them. LOC is evidence, not a budget or a finding severity. Do not invent a baseline or savings for plan-only or audit-only work.

In the existing handoff or review, name any material omission, check not run, or remaining risk. Use the normal reporting format.

## Attribution and license

The scope check, shortcut trigger, and closeout disclosure are adapted from
[Ponytail](https://github.com/DietrichGebert/ponytail), whose ladder was previously
adapted into Implementation Guardrails in AI-Dev-Shop commit `82c1cb7`.

MIT License

Copyright (c) 2026 DietrichGebert

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
