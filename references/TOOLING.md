# Tooling for Dependency and Boundary Checks

## Contents

- [Finding dependencies and cycles](#finding-dependencies-and-cycles)
- [Encoding architecture rules as tests](#encoding-architecture-rules-as-tests)
- [Change-frequency evidence from git](#change-frequency-evidence-from-git)
- [The CI ratchet pattern](#the-ci-ratchet-pattern)

Use these tools to make the audit evidence-based and the new boundary durable.
These are examples, not required dependencies: prefer tooling already present in
the repository, and do not add architecture tooling merely because it appears
in this reference. Pick the project's existing ecosystem first; do not add a
second toolchain for a one-time refactor.

## Finding dependencies and cycles

| Ecosystem | Dependency / cycle analysis | Notes |
|---|---|---|
| Java / Kotlin | `jdeps -summary`, jdepend, [ArchUnit](https://www.archunit.org/) | `jdeps` ships with the JDK; ArchUnit doubles as a test library |
| .NET / C# | [ArchUnitNET](https://github.com/TNG/ArchUnitNET), [NetArchTest](https://github.com/BenMorris/NetArchTest) | Both assert rules in ordinary unit tests |
| Python | [pydeps](https://github.com/thebjorn/pydeps), [import-linter](https://import-linter.readthedocs.io/), [pytestarch](https://pytestarch.readthedocs.io/), grimp | `import-linter` handles layers and independence contracts |
| JavaScript / TypeScript | [dependency-cruiser](https://github.com/sverweij/dependency-cruiser), madge (`madge --circular`), `eslint-plugin-import` (`import/no-cycle`), `eslint-plugin-boundaries` | dependency-cruiser has the richest rule set |
| Go | `go mod graph`, `golangci-lint` with `depguard`, `go-callvis` | Package-level cycles are compile errors; depguard adds direction rules |
| Rust | `cargo-modules` (graph), `cargo-deny` (dependency policy) | |
| PHP | [Deptrac](https://github.com/deptrac/deptrac), PHPArkitect | Deptrac is layer-oriented |
| Ruby | [Packwerk](https://github.com/Shopify/packwerk) | Package boundaries and violation reporting |
| Any language | [archfit](https://github.com/alexei-led/archfit) (meta-linter over several of the above), CodeScene (commercial, hotspots + co-change) | archfit aggregates facts across ecosystems |

Quick checks that need no new dependency:

```bash
# Python: import graph from module names
grep -rn "^from \|^import " --include="*.py" src/ | head -50

# JavaScript/TypeScript: circular imports via npx
npx --yes madge --circular src/

# Java: package summary with the built-in tool
jdeps -summary build/classes/java/main
```

## Encoding architecture rules as tests

A rule that lives only in a document will drift. Put the one or two rules that
matter most into the existing test suite or linter.

ArchUnit (Java):

```java
classes().that().resideInAPackage("..domain..")
    .should().onlyDependOnClassesThat().resideInAnyPackage("..domain..", "java..")
    .check(importedClasses);
```

import-linter (Python, `setup.cfg` / `pyproject.toml`):

```ini
[importlinter]
root_package = myapp

[importlinter:contract:layers]
name = layers
type = layers
layers =
    myapp.api
    myapp.domain
    myapp.infrastructure
```

dependency-cruiser (JS/TS, `.dependency-cruiser.js`):

```js
{
  name: 'no-domain-to-infra',
  severity: 'error',
  from: { path: '^src/domain' },
  to: { path: '^src/infra' }
}
```

Keep the rule set small. Every enforced rule is a constraint future changes
must satisfy; add one when it protects a boundary that just cost real work.

## Change-frequency evidence from git

Before refactoring, check how often the target actually changes:

```bash
# Hotspots: files changed most often in the last 6 months
git log --since="6 months ago" --name-only --pretty=format: \
  | sort | uniq -c | sort -rn | head -20

# History of one module
git log --oneline --follow -- src/billing/
```

High churn plus high blast radius is a strong refactor candidate. Low churn
plus a small dependency neighborhood is usually an argument to leave the code
alone.

## The CI ratchet pattern

For codebases with existing violations, "fail on any violation" blocks all
work; "warn only" is ignored. Use a ratchet:

1. Record current violations as a baseline (file, count, or score).
2. CI fails only when the number of new violations increases.
3. Shrink the baseline as violations are fixed, and add directional rules so
   the same violation cannot return.

Tools with built-in baseline support: dependency-cruiser (`--baseline`),
archfit (baseline files). For the rest, snapshot the tool's report and compare
counts in CI, or scope the rule to new/changed files first.

Enforcement should match what the team can maintain; a rule that is disabled
in a week taught the codebase that rules do not matter.
