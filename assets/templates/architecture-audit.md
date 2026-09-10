# Architecture Audit

## Scope

Target:

Task scope: Local / Subsystem / Repository-wide

Reason for audit:

## Baseline

Build command(s):

Test command(s):

Typecheck/lint/static-analysis command(s):

Known pre-existing failures:

Behavior that must remain unchanged:

## Current system map

### Relevant modules/components

| Module | Responsibility observed in code | Owns data? | Main callers | Main dependencies |
|---|---|---:|---|---|
| | | | | |

### Representative runtime flow(s)

```text
<flow>
```

### Dependency view

```text
<module dependency graph>
```

## Data ownership

| Data / table / state | Readers | Writers | Current invariant owner | Problem? |
|---|---|---|---|---|
| | | | | |

## Findings

### Finding 1 — <title>

Observed evidence:

Architectural mechanism:

Why it matters:

Affected workflows:

Change frequency: Low / Medium / High / Unknown

Blast radius: Low / Medium / High

Migration risk: Low / Medium / High

Confidence: Low / Medium / High

### Finding 2 — <title>

Observed evidence:

Architectural mechanism:

Why it matters:

Affected workflows:

Change frequency:

Blast radius:

Migration risk:

Confidence:

## Highest-value target

Problem to solve first:

Why this outranks other findings:

## Proposed target boundary

Responsibility:

Owned invariants:

Owned data/state:

Public contract:

Implementation details to hide:

Allowed dependencies:

Forbidden dependencies:

## Alternatives considered

### Option A

Change:

Benefits:

Costs/risks:

### Option B

Change:

Benefits:

Costs/risks:

## Recommendation

Recommended option:

Coupling expected to disappear:

Coupling expected to be introduced:

Why the trade-off is better:

## Uncertainties / assumptions to validate

-
