# Sensor: Dependency / Security Drift

Detects outdated dependencies, known vulnerabilities, and license compliance issues before they accumulate into a security incident or painful upgrade.

## Sensor Definition

- **Class**: `computational`
- **Timing**: daily scheduled + on lockfile change (PR trigger)
- **Owner**: Observer → routes to Security agent or DevOps agent
- **Artifact location**: `<ADS_MEMORY_ROOT>/.local-artifacts/sensors/dependency-drift-<timestamp>.md`

## Detector

The toolkit installs nothing. The host declares the commands it uses, through an
existing slot such as `static_analysis`. If nothing is declared, this sensor is
`inactive`: report the absence, never a clean bill of health.

Two distinct capabilities, and a host may have one without the other:

> **Vulnerability scan** — emit each known advisory against the **resolved**
> dependency set, with its identifier, severity, and the affected version range.
>
> **Outdated check** — emit each dependency whose resolved version trails an
> available one, distinguishing patch, minor and major.

| Requirement | Why |
|---|---|
| Reads the **resolved** dependency set, not the declared ranges | a manifest range says what is permitted; the lockfile says what ships |
| Emits an advisory identifier per finding | severity alone cannot be deduplicated across runs or looked up |
| Records the advisory database and the time it was fetched | **a scan is only as current as its database.** A stale database returns a clean result that is indistinguishable from a secure dependency set |
| Covers transitive dependencies, or says it does not | most real exposure is transitive |

The database-freshness requirement is the one most often skipped, and it is the
one that makes a zero result meaningless when skipped. Record it with the result.

This sensor is advisory here and gates nothing; a host may still wire its own
release blocking around the same commands.


## Action-on-Fail

| Finding | Severity | Action |
|---------|----------|--------|
| Critical/High vulnerability (CVSS ≥ 7.0) | **Blocker** | Observer escalates immediately; Security agent formulates patch plan |
| Medium vulnerability (CVSS 4.0-6.9) | Escalation | Observer reports; user decides timing |
| Low vulnerability | Advisory | Logged in maintenance report |
| Major version behind (3+ major) | Escalation | Observer reports; user decides upgrade timing |
| Minor/patch outdated | Advisory | Batched into weekly maintenance summary |
| License violation (copyleft in proprietary project) | **Blocker** | Observer escalates immediately |

## Routing

1. **Critical vulnerability found**:
   - Observer flags as blocker
   - Routes to Security agent with CVE details, affected package, and version range
   - Security agent produces a patch recommendation
   - Programmer applies the fix in a dedicated maintenance run

2. **Routine outdated dependencies**:
   - Observer batches into `<ADS_MEMORY_ROOT>/reports/maintenance/dependency-drift-<date>.md`
   - Adds to `harness-engineering/maintenance/tech-debt-tracker.md`
   - Presented to user at next Observer maintenance pass

3. **PR-triggered (lockfile change)**:
   - Scan runs on the new lockfile
   - If new vulnerabilities introduced, Code Review is informed
   - Advisory unless the new dep has a known critical vuln (then escalation)

## Baseline Management

- First scan establishes the current vulnerability count as baseline
- New vulnerabilities above baseline in untouched deps are flagged at next scheduled scan
- Vulnerabilities introduced by a current PR are attributed to that PR immediately

## What This Does NOT Cover

- Runtime dependency behavior (supply chain attacks at execution time)
- Transitive dep license deep-analysis beyond what the tool reports
- Custom internal package version drift
