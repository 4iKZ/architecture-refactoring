<p align="center">
  <img src="assets/hero.jpg" alt="Architecture Refactoring Skill — from spaghetti and chaos to clear boundaries" width="100%">
</p>

# Architecture Refactoring Skill

**English** | [简体中文](README.zh-CN.md)

A tool-agnostic Agent Skill for refactoring an **existing** software system toward
higher cohesion, lower harmful coupling, clearer ownership, and a smaller change
blast radius.

> Optimize for change propagation — not just dependency count.

## Why this skill exists

Most "architecture" prompting makes agents apply patterns: Clean Architecture,
SOLID, DI, repositories, event buses. Those are techniques, not goals. Applying
them to a working system can leave the runtime coupling untouched while adding
folders, interfaces, and indirection.

This skill treats architecture as a **structure for containing change**:

- things that change together live together;
- things that change for different reasons are separated;
- cross-boundary knowledge stays narrow, explicit, and stable.

It is not a Clean Architecture generator. It does not force abstractions. When
the evidence says a stable module should be left alone, it says so.

## The workflow

The hero image distills the full [SKILL.md](SKILL.md) workflow into four moves:

1. **Audit first** — understand the current system, dependencies, and change
   hotspots before proposing anything.
2. **Define boundaries** — identify cohesive modules, explicit contracts, and
   clear ownership; every boundary must answer responsibility, invariants, data
   ownership, public contract, and allowed/forbidden dependencies.
3. **Refactor incrementally** — introduce a seam, migrate one caller, verify,
   then migrate the rest; never a big-bang rewrite.
4. **Verify behavior and architecture separately** — tests provide evidence that
   behavior is preserved; dependency direction, ownership, and blast radius
   provide evidence that the architecture improved.

On hosts that support proactive Agent Skill discovery, the description is
designed to trigger on both explicit architecture requests and symptom-style
ones. Discovery remains host- and model-dependent; when the host exposes the
skill, naming it explicitly ("use the architecture-refactoring skill") always
works. The skill enforces evidence over pattern compliance, including explicit
stop conditions and a list of common refactoring anti-patterns.

## What changes when the skill is used?

A generic "apply Clean Architecture" prompt tends to produce a prettier tree:

```text
src/
├── domain/
├── services/
├── repositories/
├── interfaces/
└── adapters/
```

This skill asks instead for the smallest change that reduces future coupling:

1. Trace who changes together.
2. Identify split ownership.
3. Show concrete dependency evidence.
4. Propose the smallest boundary change.
5. Migrate one caller.
6. Re-run behavioral and structural checks.

The goal is not a prettier directory tree. The goal is a smaller future change
surface.

## What's inside

```text
architecture-refactoring/
├── SKILL.md                      # Workflow, scope budgets, red flags, gotchas
├── references/
│   ├── PRINCIPLES.md             # Read when a boundary decision needs justification
│   ├── AUDIT_GUIDE.md            # Read before mapping a subsystem or repository
│   ├── REFACTORING_PLAYBOOK.md   # Read when choosing the smallest operation
│   ├── EXAMPLES.md               # Worked end-to-end cases, including "leave it alone"
│   ├── VERIFICATION.md           # Read before the first migration step
│   ├── TOOLING.md                # Dependency/cycle/enforcement tooling per ecosystem
│   └── ANTI_PATTERNS.md          # Read before large changes
├── assets/templates/             # Audit, plan, and report templates
└── evals/                        # Fixtures and eval harness (scenarios + triggers)
```

## Installation

The skill is a folder with a `SKILL.md`; any agent that supports the
[Agent Skills](https://agentskills.io) format can load it.

**Claude Code** (user-level):

```bash
git clone https://github.com/4iKZ/architecture-refactoring \
  ~/.claude/skills/architecture-refactoring
```

On Windows PowerShell, clone into `$HOME\.claude\skills\architecture-refactoring`.
For a per-project install, use `.claude/skills/architecture-refactoring/`.

**OpenCode**:

```bash
git clone https://github.com/4iKZ/architecture-refactoring \
  ~/.config/opencode/skills/architecture-refactoring
```

**Codex and other cross-client agents**:

```bash
git clone https://github.com/4iKZ/architecture-refactoring \
  ~/.agents/skills/architecture-refactoring
```

**Manual**: copy this directory into your client's skills folder. Keep the
folder name `architecture-refactoring` so the `name` in the frontmatter
matches.

## Usage

Audit first, without editing code:

```text
Use the architecture-refactoring skill to inspect this repository.
Do not edit code yet. Audit the architecture around <subsystem>, identify the
highest-value cohesion/coupling problems, and produce an audit plus a refactor
plan. Base every recommendation on concrete code/dependency/data-flow evidence.
```

Then execute the approved plan:

```text
Use the architecture-refactoring skill and execute the approved plan
incrementally. Preserve behavior, verify after each migration step, and stop if
new evidence invalidates the target boundary.
```

For a narrower task:

```text
Use the architecture-refactoring skill to refactor <module>.
Limit analysis to this module and its dependency neighborhood unless you find
evidence that the problem is systemic.
```

The description is also designed to match symptom-style requests that never say
"architecture" — "why does everything depend on everything", "I fix one bug and
break three tests", "where should we start cleaning up".

**Do not use it for**: greenfield design, mechanical renames, formatting,
dependency upgrades, or purely stylistic cleanup. Those are separate changes.

## Evaluation

The `evals/` directory contains four scenarios with assertion rubrics, two
synthetic fixtures (a dependency cycle and a shared-state ownership problem),
and a 20-query trigger set with a fixed train/validation split.

```bash
# Trigger evals (requires the claude CLI; install the skill into the workspace first)
python evals/run_trigger_eval.py --workspace <workspace> --output results.json --runs 3

# One output scenario
python evals/run_scenario_eval.py --scenario 1 --workspace <ws> \
  --with-skill . --out <run-dir>

# Repository-specific validation (requires PyYAML)
python evals/validate_skill.py .

# Official Agent Skills reference validator (optional; run from the repo root)
python -m pip install "git+https://github.com/agentskills/agentskills.git#subdirectory=skills-ref"
skills-ref validate "$PWD"
```

Windows note: the reference validator reads files as UTF-8; if your default
locale is not UTF-8, set `$env:PYTHONUTF8=1` before running it.

Skill discovery is host-dependent. If your agent does not auto-invoke skills,
name it explicitly: "use the architecture-refactoring skill". See
[evals/README.md](evals/README.md) and [evals/RESULTS.md](evals/RESULTS.md)
for details and observed runs.

## License

[Apache-2.0](LICENSE)
