# Evaluation Results

Date: 2026-09-10

Environment: Claude Code CLI 2.1.142 routed to a third-party model (DeepSeek V4
family). Skill discovery and behavior are model-dependent; the results below are
single-run snapshots, not a statistical benchmark.

## Output scenarios

### Scenario 1 — fix-import-cycle

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

### Scenario 4 — should-not-refactor (notifier.py trap)

- Baseline: **inconclusive** — timed out at 600s with zero file changes.
- Iteration 1: **inconclusive** — run aborted around 900s with zero file
  changes.
- In both runs the agent made no destructive edits to the stable module, but
  the transcript did not survive the timeout, so the recommendation itself
  could not be graded. Re-run on a faster host model.

## Trigger evals

Single-run observations (see `trigger_queries.json` for ids):

| Query | Expectation | Observed |
|---|---|---|
| 1, 2, 7, 8 | should trigger | not triggered (0/4) |
| 13, 19 | should not trigger | not triggered (correct) |
| 17 (near-miss rename) | should not trigger | triggered once, not triggered on repeat — noisy |

Conclusion: proactive skill discovery is unreliable with this harness/model.
The 20-query set with its fixed train/validation split is ready to re-run on
Claude- or GPT-based hosts, which is where description tuning should happen.

## Reproduce

```bash
# Prepare a workspace and install the skill at <ws>/.claude/skills/architecture-refactoring/
python evals/run_trigger_eval.py --workspace <ws> --output <results.json>
python evals/run_scenario_eval.py --scenario 1 --workspace <ws> --with-skill . --out <run-dir>
```
