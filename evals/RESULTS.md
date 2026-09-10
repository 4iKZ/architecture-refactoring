# Evaluation Results

## Current status

- The structural-verification fix written after Iteration 1 is present on
  `main` (`SKILL.md` step 9, `references/VERIFICATION.md`): re-run the
  dependency check and include its raw output; an asserted removal is a
  hypothesis, not verification.
- **No scenario run has evaluated that revision yet.** Everything under
  "Historical runs" predates the fix. Iteration 1's single failed assertion is
  exactly the miss the fix targets.
- Scenarios 2 (`audit-only-no-edit`) and 3 (`big-bang-pressure`) have not been
  run at all.
- `evals/grade_scenario.py` (hybrid grader) was replayed against the historical
  artifacts and reproduces the human grading: Iteration 0 passes all
  deterministic checks; Iteration 1 fails only the import-cycle check.
- Until the scenarios are re-run on the current revision, treat every number
  below as a historical observation about older skill snapshots, not as a claim
  about `main`.

### Re-running

```bash
# Workspace: install the skill at <ws>/.claude/skills/architecture-refactoring/
python evals/run_scenario_eval.py --scenario 1 --workspace <ws> --with-skill . --out <run-dir>
python evals/grade_scenario.py --run-dir <run-dir>

# Trigger eval: per-query trigger rates (a should-trigger query passes at
# trigger rate >= 0.5); use >= 3 runs per query for any reported result
python evals/run_trigger_eval.py --workspace <ws> --output <results.json> --runs 3
```

Record for every reported run: skill commit, host, model, CLI version, runs per
scenario, date. The historical runs below predate that convention.

## Historical runs

### 2026-09-10 — output scenarios

Environment: Claude Code CLI 2.1.142 routed to a third-party model (DeepSeek V4
family). Single-run observations, not a statistical benchmark.

Skill revisions: the runs below used uncommitted snapshots, so no commit hash
exists for them.

- baseline runs: `evals/workspace/skill-snapshot-baseline` (original skill)
- iteration 1 runs: `evals/workspace/skill-snapshot-new` (reworked skill,
  before the verification fix)
- the fix itself: commit `723ef78`, not yet evaluated

Runs per scenario: 1.

#### Scenario 1 — fix-import-cycle

**Baseline (original skill): PASS (6/6 assertions), 274s, tests pass.**

- Traced the cycle and removed it: `billing` became a pure gateway with no
  project imports; `orders.checkout` orchestrates `billing.charge` then the
  owned transition `orders.mark_paid`.
- Removed the duplicated discount rule; reported coupling removed/introduced.

**Iteration 1 (reworked skill): PARTIAL (5/6 assertions), 645s, tests pass.**

- Improved: state writes routed through `orders.mark_paid`; `db` and the
  duplicated pricing rule removed from `billing`.
- Missed: `billing` still imports `orders` while `orders` still imports
  `billing` — the static import cycle remains.
- The final report claimed the cycle was eliminated without showing the
  dependency check output.
- Action taken: `SKILL.md` step 9 and `references/VERIFICATION.md` now require
  re-running the dependency check and including its raw output for structural
  claims (asserted removals are hypotheses, not verification).

#### Scenario 4 — should-not-refactor (notifier.py trap)

- Baseline: **inconclusive** — timed out at 600s with zero file changes.
- Iteration 1: **inconclusive** — run aborted around 900s with zero file
  changes.
- In both runs the agent made no destructive edits to the stable module, but
  the transcript did not survive the timeout, so the recommendation itself
  could not be graded. Re-run on a faster host model.

#### Scenarios 2 and 3

Not run yet.

### Trigger evals

Single-run observations (see `trigger_queries.json` for ids):

| Query | Expectation | Observed |
|---|---|---|
| 1, 2, 7, 8 | should trigger | not triggered (0/4) |
| 13, 19 | should not trigger | not triggered (correct) |
| 17 (near-miss rename) | should not trigger | triggered once, not triggered on repeat — noisy |

Conclusion: proactive skill discovery is unreliable with this harness/model.
The 20-query set with its fixed train/validation split is ready to re-run on
Claude- or GPT-based hosts, which is where description tuning should happen.
