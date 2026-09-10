# Refactoring Playbook

Choose the smallest structural operation that addresses the demonstrated architecture problem.

## Contents

1. [Move responsibility](#1-move-responsibility)
2. [Extract a cohesive module](#2-extract-a-cohesive-module)
3. [Merge artificial boundaries](#3-merge-artificial-boundaries)
4. [Introduce a facade](#4-introduce-a-facade)
5. [Introduce an adapter](#5-introduce-an-adapter)
6. [Introduce a boundary contract](#6-introduce-a-boundary-contract)
7. [Invert dependency](#7-invert-dependency)
8. [Break a cycle](#8-break-a-cycle)
9. [Assign state ownership](#9-assign-state-ownership)
10. [Separate policy from volatile mechanism](#10-separate-policy-from-volatile-mechanism)
11. [Strangler migration](#11-strangler-migration)
12. [Shrink public surface](#12-shrink-public-surface)
13. [Move orchestration upward](#13-move-orchestration-upward)
14. [Event-driven decoupling — only when semantics justify it](#14-event-driven-decoupling--only-when-semantics-justify-it)
15. [Microservice extraction — high bar](#15-microservice-extraction--high-bar)

## 1. Move responsibility

Use when logic lives in a module that does not own the relevant data, invariant, or domain concept.

Typical sequence:

```text
identify true owner
→ add operation to owner
→ route one caller through it
→ verify
→ migrate remaining callers
→ remove duplicated rule
```

Success condition: the invariant or decision has one clear owner.

## 2. Extract a cohesive module

Use when one module contains a cluster that has a distinct domain responsibility and independent change reason.

Before extracting, identify:

- owned data;
- invariants;
- incoming operations;
- outgoing dependencies;
- public contract.

Do not extract merely because a file is long.

## 3. Merge artificial boundaries

Use when modules:

- always change together;
- constantly call each other;
- share the same invariants/data ownership;
- add ceremony without independent evolution.

Merging can **reduce** coupling by restoring cohesion.

## 4. Introduce a facade

Use when callers know too much about a subsystem's internal sequence or object graph.

Before:

```text
caller
→ parser
→ validator
→ cache
→ repository
→ notifier
```

After:

```text
caller
→ subsystem facade
```

The facade is useful only if it centralizes a coherent capability rather than becoming another god object.

## 5. Introduce an adapter

Use around volatile external mechanisms:

- database libraries;
- vendor/cloud SDKs;
- LLM providers;
- HTTP clients;
- filesystem access;
- queue/broker clients;
- observability vendors.

Keep vendor-specific types on the adapter side where practical.

## 6. Introduce a boundary contract

Use when callers depend on internal representation.

Examples:

- persistence entity → domain/result DTO;
- vendor response → internal result type;
- large mutable object → narrow immutable request/result;
- raw event payload → validated event contract.

Keep contracts purpose-specific. Do not create a universal “common model” shared by the whole repository.

## 7. Invert dependency

Use when stable policy depends directly on volatile implementation and a real seam exists.

Example:

```text
business policy → Stripe SDK
```

becomes:

```text
business policy → payment capability contract ← Stripe adapter
```

Do not invert every dependency mechanically. If the implementation is stable, local, and trivial, abstraction may add more cost than value.

## 8. Break a cycle

Preferred order of investigation:

1. Is one responsibility in the wrong module?
2. Should two modules actually be one cohesive boundary?
3. Is shared state causing mutual knowledge?
4. Can orchestration move to a third application-level owner?
5. Can one direction depend on a narrow contract instead?

Avoid “cycle fixes” based only on lazy imports, service locators, globals, or event indirection.

## 9. Assign state ownership

Use when multiple modules mutate the same state.

Strategy:

```text
identify invariant owner
→ make writes flow through owner
→ preserve read models where needed
→ migrate direct mutations
→ enforce boundary
```

For databases, this can be a logical ownership change without physically splitting the database.

## 10. Separate policy from volatile mechanism

Useful when business rules are entangled with framework/transport/storage concerns.

Examples:

- request object handling mixed into pricing rules;
- ORM calls scattered through domain decisions;
- retry/vendor error handling embedded in core policy;
- prompt-provider SDK details embedded in agent planning logic.

Extract only enough seam to make the policy independently understandable/testable.

## 11. Strangler migration

Use for risky or widely used code paths.

Pattern:

```text
old public path
       ↓
compatibility seam
      ↙ ↘
 old       new
```

Migrate callers gradually. Remove the compatibility path only after verification.

## 12. Shrink public surface

Use when many internals are de facto API.

Sequence:

- identify actual external usage;
- define supported entry points;
- migrate direct internal imports;
- mark internal namespaces clearly;
- enforce import/dependency rules when tooling supports it.

## 13. Move orchestration upward

Use when low-level modules call one another bidirectionally to coordinate workflows.

Often the better structure is:

```text
application orchestrator
  ├── capability A
  └── capability B
```

instead of:

```text
A ↔ B
```

This is especially useful when A and B should remain independently coherent.

## 14. Event-driven decoupling — only when semantics justify it

Use events when producers should not require immediate knowledge of specific consumers and eventual processing is acceptable.

Before choosing events, define:

- event ownership;
- delivery guarantees;
- ordering requirements;
- idempotency;
- schema evolution;
- failure handling;
- observability;
- replay semantics.

Do not replace a simple synchronous call with a queue solely to make a diagram look decoupled.

## 15. Microservice extraction — high bar

Consider only when independent deployment/scaling/ownership/reliability needs justify operational distribution.

First prove that the capability already has a strong logical boundary:

- clear ownership;
- stable contract;
- data boundary;
- manageable consistency model;
- limited cross-boundary chatter.

If those are missing, service extraction usually creates a distributed monolith.
