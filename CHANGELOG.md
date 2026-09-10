# Changelog

## [Unreleased]

- Add a when-to-use infographic to the README.

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
