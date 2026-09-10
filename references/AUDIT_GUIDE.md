# Architecture Audit Guide

Use this guide before substantial structural changes.

The audit should be proportional to scope. Do not map an entire repository for a local refactor unless evidence requires it.

## Contents

1. [Establish system shape](#1-establish-system-shape)
2. [Trace representative flows](#2-trace-representative-flows)
3. [Build a dependency neighborhood](#3-build-a-dependency-neighborhood)
4. [Detect dependency cycles](#4-detect-dependency-cycles)
5. [Examine data ownership](#5-examine-data-ownership)
6. [Examine public surface area](#6-examine-public-surface-area)
7. [Examine reasons for change](#7-examine-reasons-for-change)
8. [Inspect change history when available](#8-inspect-change-history-when-available)
9. [Inspect test topology](#9-inspect-test-topology)
10. [Score findings by impact](#10-score-findings-by-impact)
11. [Required audit output](#11-required-audit-output)

## 1. Establish system shape

Identify the relevant:

- languages and frameworks;
- package/module/service layout;
- runtime entry points;
- build/test/typecheck/lint commands;
- deployment units;
- primary persistence mechanisms;
- external systems and vendor SDKs;
- async/event/queue boundaries;
- configuration sources.

Note existing architectural conventions, but verify them against actual code. Documentation can be stale.

## 2. Trace representative flows

Choose 1–3 important runtime flows through the target scope.

Examples:

```text
HTTP request
→ controller
→ application service
→ domain rule
→ repository
→ database
```

or:

```text
event
→ consumer
→ workflow
→ external API
→ persistence
→ emitted event
```

For each flow, record:

- caller/callee direction;
- data structures crossing boundaries;
- side effects;
- transaction boundaries;
- external dependencies;
- error propagation;
- hidden ordering requirements.

## 3. Build a dependency neighborhood

At minimum, capture:

```text
TARGET
├── inbound callers
├── outbound dependencies
├── shared state/data
└── external effects
```

For subsystem/repository audits, create a module graph.

Classify edges when useful:

- call/import;
- reads data;
- writes data;
- emits event;
- consumes event;
- shares type/schema;
- shares configuration;
- temporal dependency.

A plain directed graph is better than a beautiful but inaccurate diagram.

## 4. Detect dependency cycles

For every cycle, ask why it exists.

Common causes:

- responsibility split across the wrong boundary;
- one shared domain concept has multiple owners;
- a lower-level module calls back into a higher-level workflow;
- convenience imports;
- shared utility packages;
- runtime registration mechanisms leaking into domain code.

Do not “fix” a cycle by moving an import inside a function unless the architecture is otherwise correct. That hides a static symptom rather than removing the semantic cycle.

## 5. Examine data ownership

For important mutable data, create a matrix:

| Data / table / state | Reads | Writes | Invariant owner | Notes |
|---|---|---|---|---|

Warning signs:

- multiple unrelated modules write the same table/state;
- callers bypass module APIs to update internals;
- business invariants are duplicated;
- one module's persistence representation is another module's domain API;
- transaction boundaries span many modules without a clear application owner.

## 6. Examine public surface area

For each target module, identify what external code can access.

Ask:

- which exports are intentionally public?
- which internals are imported by other modules anyway?
- are callers using internal fields instead of operations?
- are large objects exposed when a narrow result would suffice?
- are SDK/framework/persistence types crossing the boundary?

A broad public surface increases the number of contracts that must remain stable.

## 7. Examine reasons for change

For each major module, list independent reasons it changes.

Example:

```text
AccountService changes because:
- authentication policy changes
- email provider changes
- subscription billing rules change
- profile validation changes
- database representation changes
```

This suggests several responsibilities may be mixed.

Then cluster by:

- domain concept;
- invariant;
- lifecycle;
- data ownership;
- external volatility;
- actual co-change history.

## 8. Inspect change history when available

Use Git history to identify:

- files that frequently change together;
- hotspots with many fixes;
- modules repeatedly touched by unrelated features;
- public APIs that cause repeated migration work;
- “central” files modified in most feature branches.

Interpret history carefully. It is evidence of change patterns, not an automatic target architecture.

## 9. Inspect test topology

Ask:

- can the target capability be unit tested without booting unrelated infrastructure?
- do tests require a database/network/entire application because boundaries are missing?
- are tests tightly coupled to implementation details?
- are there contract tests across important boundaries?
- does changing one module break many unrelated tests?

Test topology often reveals hidden architecture.

## 10. Score findings by impact

For each finding record:

- concrete evidence;
- affected workflows;
- change frequency;
- blast radius;
- defect/operational risk;
- migration difficulty;
- confidence level.

Prefer a small number of high-value findings over a long generic smell list.

## 11. Required audit output

Use `assets/templates/architecture-audit.md`.

A useful audit must distinguish:

- observed facts;
- inferred causes;
- recommended changes;
- uncertain areas requiring validation.

Do not jump directly from “this class is large” to “split it”. Size is only a signal.
