# Test Certification Record

- Test Suite: <name>
- Spec ID: <SPEC-id>
- Spec Version: <version>
- Spec Hash: <sha256 — must match hash in spec file>
- Certified At: <ISO-8601 UTC>
- Certified By: TDD Agent

## Covered Requirements

Map every test to the spec reference it covers. No orphan tests. No uncovered requirements.

| Spec Ref | Test Name | Type |
|---|---|---|
| REQ-01 / AC-01 | `<describe block> > <it block>` | Acceptance |
| INV-01 | `<describe block> > <it block>` | Invariant |
| EC-02 | `<describe block> > <it block>` | Edge Case |

## Known Gaps

Requirements that are not yet covered. Every gap requires a risk level. High-risk gaps block progression to Programmer.

| Spec Ref | Reason Not Covered | Risk | Resolution |
|---|---|---|---|
| EC-03 | Architecture contract not yet defined by Architect | High | Blocked — route to Architect |
| EC-05 | External dependency unavailable in test environment | Medium | Deferred to integration test phase |

## Drift Status

- [ ] Current spec hash matches certified hash above
- [ ] All High-risk gaps have been reviewed by Coordinator
- [ ] No test asserts implementation internals (only observable behavior)
