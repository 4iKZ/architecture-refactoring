# Architecture Principles

This file provides the conceptual model used by the skill. Treat these principles as reasoning tools, not dogma.

## Contents

1. [Architecture is a structure for containing change](#1-architecture-is-a-structure-for-containing-change)
2. [Cohesion](#2-cohesion)
3. [Coupling](#3-coupling)
4. [Information hiding](#4-information-hiding)
5. [Ownership](#5-ownership)
6. [Stable dependency direction](#6-stable-dependency-direction)
7. [Change affinity](#7-change-affinity)
8. [Local reasoning](#8-local-reasoning)
9. [Explicit coupling can be healthy](#9-explicit-coupling-can-be-healthy)
10. [Architecture is a trade-off](#10-architecture-is-a-trade-off)

## 1. Architecture is a structure for containing change

The strongest practical test of a module boundary is:

> When requirement X changes, where must the code change, and how much unrelated knowledge is required to make that change safely?

High-quality architecture tends to localize likely changes. Poor architecture turns local requirements into cross-cutting edits.

This is why the skill prioritizes **change propagation** and **blast radius** over visual cleanliness.

## 2. Cohesion

Cohesion measures how strongly the responsibilities inside a boundary belong together.

Evidence of high cohesion:

- responsibilities express one recognizable capability;
- code shares domain vocabulary;
- the same invariants apply across the module;
- code operates on the same owned state;
- pieces have similar lifecycle and change reasons;
- files/classes frequently need to change together for the same feature.

Evidence of low cohesion:

- one module changes for unrelated business reasons;
- methods operate on disjoint data and dependencies;
- the module mixes orchestration, policy, persistence, formatting, transport, and vendor-specific details without a clear reason;
- different parts could evolve independently but are forced through one public object.

Do not infer cohesion from file size. “Small” and “cohesive” are not synonyms.

## 3. Coupling

Coupling is the knowledge or constraint one part of the system imposes on another.

Inspect multiple forms:

### Structural coupling
Imports, direct calls, inheritance, shared types.

### Data coupling
Shared tables, shared schemas, cross-module mutation, persistence-model leakage.

### Semantic coupling
One module knows another module's internal states, rules, naming conventions, error semantics, or workflow stages.

### Temporal coupling
Operations must happen in a hidden order: initialize A before B, write X before calling Y, commit before publishing Z.

### Runtime coupling
Availability or latency of one component directly controls another.

### Configuration coupling
Several components must agree on hidden environment variables, paths, feature flags, or initialization values.

### Deployment coupling
Components can only be released safely together.

A transport change does not automatically remove semantic coupling. `A → Kafka → B` may remain more tightly coupled than a simple function call if A still depends on B's exact business semantics.

## 4. Information hiding

A module should hide design decisions that callers do not need to know.

Good boundaries expose stable capabilities and conceal volatile implementation details.

Prefer:

```text
payment.charge(order_id, amount) -> PaymentResult
```

instead of exposing:

```text
payment.get_database_connection()
caller edits payment rows directly
caller reproduces payment state transitions
```

Information hiding reduces the number of places that must change when implementation choices evolve.

## 5. Ownership

For every important rule or mutable state, ask:

> Who is the authoritative owner?

Ambiguous ownership creates coupling because several modules must coordinate before anything can change.

Healthy ownership usually means:

- one module owns the invariants;
- external modules request operations rather than mutate internals;
- the owner defines the public contract;
- other modules may cache or project data, but do not silently become co-owners.

## 6. Stable dependency direction

Stable policy should not be forced to know volatile implementation details when a useful seam exists.

Examples of volatile details:

- database engines;
- cloud/vendor SDKs;
- HTTP clients;
- message brokers;
- LLM providers;
- filesystem layout;
- framework-specific request/response types.

An abstraction is useful when it isolates a meaningful reason for change. It is wasteful when it simply renames a concrete class.

## 7. Change affinity

Code that repeatedly changes together for the same reason is evidence that it may belong together.

Useful evidence sources:

- Git co-change history;
- issue/PR history;
- repeated multi-file edits for one feature;
- shared domain invariants;
- recurring bug-fix patterns.

Do not use co-change statistics blindly. Two files may change together because architecture is already poor. Combine historical evidence with domain meaning and dependency analysis.

## 8. Local reasoning

A well-bounded module allows someone to answer most questions about a capability without inspecting the entire repository.

A boundary is stronger when developers can understand:

- what it owns;
- what it guarantees;
- what it needs;
- how to test it;
- what can change internally without affecting callers.

This is particularly important for coding agents, because architecture directly determines how much repository context the agent must load to make a safe change.

## 9. Explicit coupling can be healthy

The goal is not zero coupling.

Modules in one system must collaborate. Prefer coupling that is:

- intentional;
- narrow;
- typed or schema-defined where possible;
- stable relative to the implementations behind it;
- observable and testable;
- owned by a clear side of the boundary.

Hidden coupling is generally more dangerous than visible coupling.

## 10. Architecture is a trade-off

Every boundary removes some coupling and introduces other coupling.

For any proposed refactor ask:

1. What dependency disappears?
2. What dependency is introduced?
3. Which side now owns the knowledge?
4. Is the new dependency more stable?
5. Does the likely change blast radius shrink?
6. Does operational or cognitive complexity increase?
7. Is that increase justified?

There is no universally “clean” architecture independent of workload, domain, team, runtime, and expected change.
