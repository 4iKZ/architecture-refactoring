# Verification Guide

Architectural refactoring needs two independent verification tracks: behavioral correctness and structural improvement.

## Contents

1. [Behavioral verification](#1-behavioral-verification)
2. [Structural verification](#2-structural-verification)
3. [Architecture rules as code](#3-architecture-rules-as-code)
4. [Useful metrics — evidence, not goals](#4-useful-metrics--evidence-not-goals)
5. [Verification record](#5-verification-record)
6. [Completion criteria](#6-completion-criteria)

## 1. Behavioral verification

Run what the repository supports:

- unit tests;
- integration tests;
- contract tests;
- end-to-end tests;
- type checking;
- static analysis;
- linting;
- build/package verification;
- critical smoke flows.

Prefer targeted tests after each small migration step and broader suites at stable checkpoints.

If behavior is insufficiently tested, add characterization tests before moving important logic.

## 2. Structural verification

Ask whether the architecture actually improved.

### Dependency graph

Check:

- cycles removed/reduced;
- dependency direction matches intended ownership;
- no new backdoor imports were introduced;
- fan-out/fan-in changed as expected.

Re-run the dependency check after the change and record the raw output. If a cycle is claimed removed, show the import or call that no longer exists (or the tool's report). A structural claim without the check output is a hypothesis, not verification.

### Public surface

Check:

- fewer internal details are exposed;
- callers use supported entry points;
- persistence/vendor/framework types do not leak unintentionally;
- boundary contracts are smaller and clearer.

### Ownership

Check:

- important mutable state has an authoritative owner;
- duplicated invariants were removed;
- direct cross-module mutation decreased;
- transaction/orchestration responsibility is explicit.

### Test isolation

Check:

- core logic can be tested with fewer unrelated dependencies;
- tests require less whole-application setup;
- boundary contracts can be tested independently;
- mocks/fakes correspond to meaningful seams rather than every internal class.

### Change blast radius

Perform a thought experiment using representative future changes.

Examples:

- replace database/provider implementation;
- add a new business rule;
- add a new caller;
- modify one domain state transition;
- change an external API schema.

Compare how many modules would need to know about the change before vs. after.

## 3. Architecture rules as code

Where tooling permits, encode durable boundaries.

Examples:

```text
domain MUST NOT import infrastructure
presentation MUST NOT directly access persistence
module_a MUST NOT import module_b.internal
cross-module dependency cycles MUST NOT exist
```

Language-specific tools may include architecture test libraries, dependency graph analyzers, lint rules, package visibility, or custom CI checks.

Do not add enforcement that the codebase cannot realistically maintain.

## 4. Useful metrics — evidence, not goals

Potential indicators:

- number of module cycles;
- public exports;
- fan-in / fan-out;
- number of cross-boundary writes;
- number of modules touched by representative features;
- Git co-change frequency;
- test setup size;
- dependency depth;
- build/test scope required for local changes.

Never optimize metrics blindly. A lower dependency count can coexist with worse semantics.

## 5. Verification record

For each major migration step record:

```text
Changed boundary:
Behavior checks run:
Behavior result:
Structural expectation:
Structural evidence:
Unexpected effects:
Next safe step:
```

## 6. Completion criteria

A substantial refactor should not be considered complete until:

- required behavior remains correct;
- callers have migrated to the intended public path;
- obsolete compatibility paths are removed or explicitly tracked;
- architecture rules/docs reflect the new structure;
- remaining risks and deferred debt are recorded;
- the new design demonstrably reduces knowledge or change propagation for the target problem.
