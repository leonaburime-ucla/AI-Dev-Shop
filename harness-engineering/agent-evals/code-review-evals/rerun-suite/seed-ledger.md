# Seed Ledger — Code Review Rerun Suite

This suite derives from the unresolved Code Review seeds in the persisted
`isolation-suite` artifacts.

## Seeds

### eval-3-inventory-tracker

`SEED-CR-13`
- Prior result: `PARTIAL`
- Seeded issue: Transfer path can violate the total-stock invariant because it
  performs separate source and destination writes without an atomic boundary.

`SEED-CR-14`
- Prior result: `PARTIAL`
- Seeded issue: `bulkAdjust` swallows unexpected errors by treating every
  failure as an item-level validation problem.

`SEED-CR-15`
- Prior result: `PARTIAL`
- Seeded issue: The handoff claims a debt-band fix, but the “fix” is only
  comments and does not satisfy the structural-fix obligation.

`SEED-CR-16`
- Prior result: `PARTIAL`
- Seeded issue: The capacity boundary semantics are ambiguous and the exact
  boundary test is missing, even if the chosen operator may be defensible.
