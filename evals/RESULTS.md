# Evaluation Results

## Current status

- Iteration 2 (2026-09-11) evaluated `main` at commit `052503e` on scenarios
  1–3. This is the first run against the structural-verification fix (SKILL.md
  step 9, `references/VERIFICATION.md`), and the first run of scenarios 2 and
  3 at all.
- Scenario 1: 5/6 — the import cycle was removed **and** verified with the
  dependency graph, so the fix held; the remaining miss is a duplicated
  discount rule inlined in `checkout`.
- Scenario 2: 5/5 — read-only audit, zero file changes.
- Scenario 3: 4/4 — refused the big-bang rewrite and proposed an incremental,
  verifiable plan.
- Scenario 4 (`should-not-refactor`) is still unrun: both historical attempts
  timed out. It should be re-run on a faster host.
- The results below are single-run observations on one host/model, not a
  statistical benchmark.

### Iteration 2 — current main (2026-09-11)

Environment: Claude Code CLI 2.1.142 through a third-party gateway
(`http://101.6.160.131:3000`), model `deepseek-ai/DeepSeek-V4-Flash`
(reported cost $0 per run). Skill revision: `052503e` (snapshot
`evals/workspace/iteration-2/skill-snapshot-main`). Runs per scenario: 1.

| Scenario | Auto | Manual | Total | Outcome |
|---|---|---:|---:|---|
| 1. fix-import-cycle | 3/4 | 2/2 | 5/6 | **PARTIAL** |
| 2. audit-only-no-edit | 1/1 | 4/4 | 5/5 | **PASS** |
| 3. big-bang-pressure | all manual | 4/4 | 4/4 | **PASS** |

#### Scenario 1 — fix-import-cycle (881s, 28 turns, tests exit=0)

- Auto PASS: import cycle removed (`billing -> -`, `orders -> billing,db,notifier`);
  single writer of order state (`orders`); fixture tests exit=0.
- Auto FAIL: duplicated discount rule — `checkout` inlines
  `order["total"] * 0.9` next to `orders.apply_discount`.
- Reviewer note: the inline `* 0.9` also ignores the `>= 100` threshold, so
  `paid_amount` changes for orders below 100 (e.g. 25 -> 22.5) even though the
  smoke tests still pass; the run's `REFACTOR_REPORT.md` claims it used
  `apply_discount`, which the code does not.
- Manual PASS: callers/callees were traced with file:line references before
  editing; the report states coupling removed/introduced and why the new shape
  is preferable.

#### Scenario 2 — audit-only-no-edit (200s, 13 turns, zero file changes)

- Auto PASS: workspace tree byte-identical to the fixture.
- Manual PASS: identifies `warehouse`/`checkout`/`restock`/`main` as competing
  stock-state writers, with a target single-owner design (`stock.py`), a
  migrated ownership view, a behavior-preserving migration sequence, and a
  value ranking that covers both the quick correctness fixes and the
  structural fix.

#### Scenario 3 — big-bang-pressure (1297s, 35 turns, zero file changes)

- Manual PASS: explicitly refused the one-shot layered rewrite with concrete
  reasons; proposed a stepped migration (characterization tests first, seam,
  single state owner, single discount rule) with a rollback/verification gate
  per step; refused blanket interface extraction, justifying only the payment
  gateway seam.

### Harness notes (iteration 2)

- Prompts are now passed over stdin. On Windows the `claude` launcher is a
  `.cmd` shim and cmd.exe truncates multi-line argv at the first newline,
  which silently dropped the task text and every flag after it.
- The skill is delivered by asking the agent to read
  `.claude/skills/architecture-refactoring/SKILL.md` directly. This gateway's
  Skill tool only acknowledges the invocation (`Execute skill: ...`) and never
  injects the SKILL.md body; without the direct read the agent spends most of
  the run budget searching the filesystem for the skill.
- `--timeout 1500` was needed: scenario 1 ran 881s and scenario 3 ran 1297s.

### Re-running

```bash
# Workspace: install the skill at <ws>/.claude/skills/architecture-refactoring/
python evals/run_scenario_eval.py --scenario 1 --workspace <ws> --with-skill . --out <run-dir> --timeout 1500
python evals/grade_scenario.py --run-dir <run-dir>

# Trigger eval: per-query trigger rates (a should-trigger query passes at
# trigger rate >= 0.5); use >= 3 runs per query for any reported result
python evals/run_trigger_eval.py --workspace <ws> --output <results.json> --runs 3
```

Record for every reported run: skill commit, host, model, CLI version, runs per
scenario, date.

## Historical runs

### 2026-09-10 — output scenarios

Environment: Claude Code CLI 2.1.142 routed to a third-party model (DeepSeek V4
family). Single-run observations, not a statistical benchmark.

Skill revisions: the runs below used uncommitted snapshots, so no commit hash
exists for them.

- baseline runs: `evals/workspace/skill-snapshot-baseline` (original skill)
- iteration 1 runs: `evals/workspace/skill-snapshot-new` (reworked skill,
  before the verification fix)
- the fix itself: commit `723ef78`, evaluated later in Iteration 2

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

Not run in this iteration; first run in Iteration 2.

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
