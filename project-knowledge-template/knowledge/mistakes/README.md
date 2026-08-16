# Mistakes

A notebook of mistakes agents made, so the same one stops happening.

Any agent on any host (Claude Code, Codex, Gemini/agy) writes here. One file per
mistake. Nothing reads this automatically and nothing gates on it — it is a
notebook, not a pipeline stage.

## When to write one

When you realize you got something wrong **and it cost something** — the user had
to correct you, work had to be redone, or a claim you made turned out to be false.

Do not log: expected red tests during TDD, exploratory commands that failed before
you claimed anything, or a typo you caught before it reached an artifact. Those are
normal work, not mistakes.

## How to write one

Filename: `YYYY-MM-DD-short-slug.md` (add `-2`, `-3` if the slug repeats that day).

```markdown
# <one-line title of what went wrong>

- date: YYYY-MM-DD
- agent: <which agent or host — e.g. claude-code primary, programmer, codex peer>
- caught_by: user correction | test failure | validator | my own re-read | peer review

## What I was told to do
<the instruction or task, in one or two lines>

## What I actually did
<the wrong action — concrete: the file, the command, the claim I made>

## Why it went wrong
<the reason. Anchor it to something observable where you can: an instruction you
skipped, a file you never opened, a check you didn't run, an assumption you never
verified. If you genuinely don't know, write "unclear" — a guess that sounds good
is worse than an admission, because the guards below get built on it.>

## Possible guards (ideas only — not implemented)
- <idea 1>
- <idea 2>
```

## Rules

- **Guards are ideas, not work.** Never implement one because you wrote it here.
  The human reads them and decides. Leave them as a list.
- **No secrets, no personal data, no sensitive business data, no absolute paths.**
  This directory is committed in team projects, so treat it as shared material:
  `framework/governance/data-classification.md` bars SECRET outright, bars real PII,
  and bars SENSITIVE-BUSINESS (pricing models, customer lists, unreleased feature
  names) from anything that may be shared. Use repo-relative paths, and describe
  evidence rather than pasting raw tool output or the user's exact words.
- **Append, don't rewrite.** If you make the same mistake again, write a new file.
  Repetition is the signal.

## What happens later

Nothing automatic, for now. When the same mistake shows up a third time and one of
its guard ideas looks worth building, that path already exists —
`harness-engineering/quality/failure-promotion-policy.md` covers turning a repeated
failure into a validator, checklist, or skills change.
