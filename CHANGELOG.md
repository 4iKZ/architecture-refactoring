# Changelog

## [Unreleased]

- Add a when-to-use infographic to the README.
- Fix the scenario harness: send prompts over stdin and deliver the skill by a
  direct `SKILL.md` read (the gateway's Skill tool never injected the body).
- Record Iteration 2 output-scenario results for `main` in `evals/RESULTS.md`.
- Document installation via the open `skills` CLI
  (`npx skills add 4iKZ/architecture-refactoring`) in both READMEs.

## [0.1.1] - 2026-09-10

- Fold the `description` frontmatter into a `>-` block scalar for readability.
- Make the `skills-ref` spec check blocking and upgrade GitHub Actions to the
  Node 24 majors (`actions/checkout@v6`, `actions/setup-python@v6`).
- Document the Windows UTF-8 mode requirement for the reference validator.

## [0.1.0] - 2026-09-10

Initial public revision of the skill.

- `SKILL.md` workflow for evidence-based auditing, boundary definition,
  incremental migration, and separate behavior/architecture verification.
- `references/` guidance: principles, audit guide, refactoring playbook,
  examples, verification, tooling, and anti-patterns.
- `assets/` audit, plan, and report templates.
- `evals/`: four output scenarios with assertion rubrics, two synthetic
  fixtures, a 20-query trigger set, and a hybrid deterministic grader
  (`evals/grade_scenario.py`).
- Validation and CI: `evals/validate_skill.py` (YAML frontmatter, link, and
  budget checks) plus `.github/workflows/validate.yml`, including an optional
  `skills-ref` spec check.

### Notes

- Output scenarios have not yet been re-run against the current revision; see
  `evals/RESULTS.md` for the current status and historical runs.
