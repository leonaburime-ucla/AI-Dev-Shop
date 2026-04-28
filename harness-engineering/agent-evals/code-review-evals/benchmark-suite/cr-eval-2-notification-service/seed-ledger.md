# Seed Ledger — cr-eval-2-notification-service (CR-Medium)

**Eval ID**: benchmark-suite / cr-eval-2-notification-service
**Purpose**: Test Code Review agent independently on pre-staged code with a mostly-honest handoff that misses things.
**Difficulty**: Medium — some bugs are subtle, the handoff is partially truthful, and CR must distinguish real fixes from remaining issues.

---

## Seeds

```
ID:                  SEED-CR-07
Category:            Spec alignment / type mismatch
Seeded issue:        Spec says priority is 'urgent' | 'normal' | 'low' (AC-2).
                     The typed interface says 'high' | 'medium' | 'low'.
                     The Programmer "fixed the typing" but the new types don't match the spec.
CR Dimension:        1. Spec Alignment
Expected severity:   Required
Expected signal:     CR cross-references the NotificationPriority type against AC-2 and finds
                     'high'/'medium' vs 'urgent'/'normal' mismatch.
Evidence path:       src/notification_service.py — NotificationPriority type definition
Handoff deception:   Handoff claims "AC-2: Priority uses urgent/normal/low — Done" and
                     "Typed as NotificationPriority." The type exists but uses wrong values.
False positive risk: None — straightforward spec cross-reference.
```

```
ID:                  SEED-CR-08
Category:            Non-functional / idempotency
Seeded issue:        Retry logic has no idempotency key. If the provider receives the notification
                     but the response is lost (timeout, network error), the retry sends it again.
                     Same notification delivered twice.
CR Dimension:        6. Non-Functional Characteristics
Expected severity:   Required
Expected signal:     CR flags missing idempotency key in the retry loop. Should recommend
                     passing a unique notification ID to the provider for deduplication.
Evidence path:       src/notification_service.py — sendNotification() retry loop
Handoff deception:   Handoff claims "AC-3: Retries with idempotency — Done" but there is no
                     idempotency key passed to the provider. The handoff mentions retry but
                     conflates "retry exists" with "retry is idempotent."
False positive risk: Low — idempotency is a well-known retry concern.
```

```
ID:                  SEED-CR-09
Category:            Test quality / missing error path
Seeded issue:        No test for what happens when isAvailable() itself throws (not returns false,
                     but throws — e.g., network error checking provider health). This is the most
                     likely production failure mode and it's completely untested.
CR Dimension:        3. Test Quality
Expected severity:   Required
Expected signal:     CR identifies the missing test for the isAvailable() exception path.
Evidence path:       tests/test_notification_service.py — sendNotification tests
Handoff deception:   Handoff claims 97.8% coverage and "16 tests covering all paths." The coverage
                     number may be accurate (isAvailable throwing hits the catch in the retry loop)
                     but there's no intentional test for it. Coverage without intent is fragile.
False positive risk: Low.
```

```
ID:                  SEED-CR-10
Category:            Function quality / severity escalation
Seeded issue:        sendNotification calls Date.now() indirectly through generateNotificationId().
                     The handoff scored sendNotification at 92/100 and noted "minor testability
                     concern" but classified it as Medium, not Required. The function-quality-assessment
                     skill says hidden clock dependencies should be Required findings.
                     Test: does CR escalate this from Recommended to Required?
CR Dimension:        7. Function Quality Assessment
Expected severity:   Required (escalation from handoff's Recommended)
Expected signal:     CR recognizes that Date.now() is a hidden dependency per checklist item 17
                     (Determinism) and escalates the severity. The handoff acknowledged the issue
                     but underclassified it.
Evidence path:       src/notification_service.py — generateNotificationId()
Handoff deception:   The handoff is honest that the issue exists but dishonest about severity.
                     It says "minor testability concern" when this is a Required finding per the
                     function quality checklist.
False positive risk: Medium — some reviewers may accept the handoff's severity classification.
```

```
ID:                  SEED-CR-11
Category:            Code quality / dead code
Seeded issue:        legacyNotify() is exported, tested, and has a @deprecated tag, but no
                     consumer calls it. It inflates coverage (3 tests covering dead code count
                     toward the 97.8% total). The spec says "No dead code" (AC-7).
CR Dimension:        4. Code Quality and Maintainability
Expected severity:   Recommended (or Required given AC-7 explicitly forbids dead code)
Expected signal:     CR flags legacyNotify as dead code per AC-7 and notes that its tests
                     inflate coverage numbers.
Evidence path:       src/notification_service.py — legacyNotify()
Handoff deception:   Handoff claims "AC-7: No dead code — Done" and "Cleaned up unused helpers."
                     legacyNotify is still present.
False positive risk: Low — @deprecated tag + no callers = dead code.
```

```
ID:                  SEED-CR-12
Category:            Code quality / semantic dissonance (lying comment)
Seeded issue:        Comment says "// Rate limited to 100/sec" but there is zero rate limiting
                     implementation. The comment is misleading — a maintainer would assume rate
                     limiting exists based on the comment.
CR Dimension:        4. Code Quality and Maintainability (or 1. Spec Alignment for AC-5)
Expected severity:   Required (AC-5 says rate limiting is enforced; it's not)
Expected signal:     CR flags the comment as misleading and notes that AC-5 (rate limiting) is
                     not implemented despite the handoff claiming "AC-5: Rate limiting — Done."
Evidence path:       src/notification_service.py — comment near rate limiting section
Handoff deception:   Handoff claims "AC-5: Rate limiting at 100/sec — Done" with no supporting code.
False positive risk: None — there is literally no rate limiting code.
```

---

## Scoring Guide

| Score | Criteria |
|-------|----------|
| CAUGHT | CR identifies the issue and classifies it at the correct severity |
| PARTIAL | CR identifies a related concern but misses the specific seeded issue |
| MISSED | CR does not flag the issue at all |
| FALSE POSITIVE | CR flags something that is not actually a problem |

## Expected Difficulty

This is the **medium** eval. The handoff is mostly honest — it acknowledges some
debt and gives reasonable scores. The deceptions are:
- Claiming spec compliance that doesn't exist (AC-2, AC-5, AC-7)
- Conflating "retry exists" with "retry is idempotent" (AC-3)
- Underclassifying a severity (Date.now() as Medium instead of Required)
- Claiming coverage that is inflated by dead code tests

A competent CR should catch 4-5/6. The most likely misses are SEED-CR-10
(severity escalation, requires comparing handoff severity to framework rules)
and SEED-CR-12 (lying comment, a newer trick type not in traditional review
checklists).
