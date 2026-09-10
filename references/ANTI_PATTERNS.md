# Refactoring Anti-Patterns

These patterns frequently appear when coding agents are told only to “improve architecture”, “apply SOLID”, or “reduce coupling”.

## Contents

1. [Interface inflation](#1-interface-inflation)
2. [Wrapper onion](#2-wrapper-onion)
3. [Folder-driven architecture](#3-folder-driven-architecture)
4. [Utility gravity](#4-utility-gravity)
5. [Event-bus laundering](#5-event-bus-laundering)
6. [Premature microservices](#6-premature-microservices)
7. [God facade / god service](#7-god-facade--god-service)
8. [Dependency injection everywhere](#8-dependency-injection-everywhere)
9. [Repository-pattern reflex](#9-repository-pattern-reflex)
10. [Abstract-base-class inheritance tree](#10-abstract-base-class-inheritance-tree)
11. [Mechanical single-responsibility splitting](#11-mechanical-single-responsibility-splitting)
12. [Fake cycle removal](#12-fake-cycle-removal)
13. [Shared database denial](#13-shared-database-denial)
14. [Cleanup piggybacking](#14-cleanup-piggybacking)
15. [Big-bang rewrite](#15-big-bang-rewrite)
16. [Pattern compliance as success criterion](#16-pattern-compliance-as-success-criterion)

## 1. Interface inflation

Symptom:

```text
UserService
→ IUserService
→ UserServiceImpl
→ UserServiceFactory
```

with one implementation, no volatile seam, and no meaningful ownership boundary.

Why it fails: more names and hops, same semantic dependency.

## 2. Wrapper onion

Symptom: every dependency receives a facade, adapter, manager, provider, and factory regardless of volatility.

Why it fails: cognitive depth increases while information hiding may not improve.

## 3. Folder-driven architecture

Symptom: moving files into `domain/`, `service/`, `repository/`, `adapter/` without changing ownership or dependencies.

Why it fails: the directory tree looks clean while runtime coupling remains unchanged.

## 4. Utility gravity

Symptom: `common`, `shared`, `utils`, `core`, or `base` becomes the place for anything used twice.

Why it fails: unrelated domains acquire a common dependency and the package becomes expensive to change.

Rule: reuse is not sufficient evidence for shared ownership.

## 5. Event-bus laundering

Symptom:

```text
A → B
```

is replaced by:

```text
A → event bus → B
```

but A still requires B's exact reaction for correctness.

Why it fails: semantic coupling remains, while delivery, ordering, replay, and debugging complexity increase.

## 6. Premature microservices

Symptom: service boundaries are created before logical/domain boundaries are stable.

Why it fails: distributed transactions, network failures, deployment coordination, schema synchronization, and observability are added on top of existing coupling.

## 7. God facade / god service

Symptom: many dependencies are hidden behind one giant “manager” so the graph appears simpler.

Why it fails: coupling is concentrated, not removed; responsibility becomes less coherent.

## 8. Dependency injection everywhere

Symptom: every object is injected through a container, including trivial stable helpers and value objects.

Why it fails: runtime wiring becomes harder to trace and the container becomes a hidden dependency graph.

Use DI where it supports real seams or composition boundaries.

## 9. Repository-pattern reflex

Symptom: repositories are introduced for every data access even when they simply mirror an ORM API.

Why it fails: duplication without information hiding.

A repository is useful when it expresses a meaningful domain/persistence boundary, hides volatile storage details, or constrains data access semantics.

## 10. Abstract-base-class inheritance tree

Symptom: shared code is forced into inheritance to avoid duplication.

Why it fails: subclasses inherit behavior and constraints they may not semantically share.

Prefer composition when responsibilities vary independently.

## 11. Mechanical single-responsibility splitting

Symptom: a cohesive module is split because it contains many methods.

Why it fails: high internal call traffic appears and changes still span all extracted pieces.

Responsibility means “reason for change”, not “one method per class”.

## 12. Fake cycle removal

Symptom: lazy imports, service locators, globals, reflection, or runtime lookup remove a static import cycle.

Why it fails: the semantic dependency cycle still exists and becomes harder to see.

## 13. Shared database denial

Symptom: code modules look separated but several modules directly write the same tables and depend on internal columns.

Why it fails: the database is acting as a hidden shared object.

Logical data ownership matters even when physical database separation is unnecessary.

## 14. Cleanup piggybacking

Symptom: architectural migration also renames unrelated files, re-formats the repository, changes APIs, upgrades dependencies, and rewrites tests.

Why it fails: review and rollback become difficult; failures are hard to attribute.

Separate unrelated cleanup from structural migration.

## 15. Big-bang rewrite

Symptom: old architecture is deleted before the new path has been proven with real callers.

Why it fails: migration risk and debugging surface become maximal.

Prefer seams, compatibility paths, gradual caller migration, and safe stopping points.

## 16. Pattern compliance as success criterion

Symptom: the agent reports success because the code now uses DDD/Clean Architecture/SOLID terminology.

Why it fails: architectural quality depends on actual ownership, information hiding, dependency direction, and change propagation.

Required question:

> Which concrete future change became more local because of this refactor?

If there is no convincing answer, the architecture improvement is unproven.
