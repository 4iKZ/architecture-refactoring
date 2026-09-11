# Evals

Lightweight evaluation setup for the `architecture-refactoring` skill.

## Layout

```
evals/
├── evals.json              # 4 output scenarios (prompt + expected output + assertions)
├── trigger_queries.json    # 20 trigger queries (should/shouldn't trigger, train/validation split)
├── run_trigger_eval.py     # runs trigger queries via the `claude` CLI and reports trigger rates
├── run_scenario_eval.py    # runs one output scenario and snapshots outputs/ + tests.txt
├── grade_scenario.py       # deterministic checks + grading.json (hybrid grader)
└── fixtures/
    ├── shop-cycle/               # orders<->billing cycle, duplicated pricing rule, stable ugly module
    └── inventory-shared-state/   # three writers for the same stock state
```

## Preparing a run workspace

Copy the fixture named by the scenario to the workspace directory the prompt expects:

- `shop-cycle` → `./shop`
- `inventory-shared-state` → `./inventory`

Optional, for change-frequency evidence in `shop-cycle` — run it **inside the
workspace copy**, not in the repository's fixture directory (it creates a local
`.git` there):

```bash
python shop/setup_history.py    # from the workspace root, after copying the fixture
```

The fixture tests are the behavior baseline:

```bash
python -m unittest discover -s <fixture>/tests   # run from the fixture root
```

## Running output evals

Run each scenario in a clean workspace (`with_skill` and `without_skill`, or `old_skill` vs `new_skill`).
Give the agent the scenario prompt from `evals.json` and save the transcript and resulting files.

Suggested workspace layout (gitignored):

```
evals/workspace/iteration-N/<scenario-name>/{with_skill,without_skill}/
├── outputs/        # files produced by the run
├── transcript.md   # the agent's final response
└── grading.json    # assertion results (text, passed, evidence)
```

Grade assertions with concrete evidence; for the "tests still pass" assertion, run the fixture test suite in `outputs/`.

## Grading outputs

Run the deterministic subset after a scenario finishes:

```bash
python evals/grade_scenario.py --run-dir <run-dir>
```

It writes `grading.json` in the run directory in the shape recommended by the
Agent Skills evaluation guide (`assertion_results` + `summary`). Assertions
that can be checked mechanically are graded automatically; the rest are
recorded with `"passed": null` and `mode: "manual"` for transcript review.
`pass_rate` covers only the auto-decided assertions.

Current automatic checks:

- Scenario 1 (`fix-import-cycle`): import cycle removed (module-level, and not
  hidden behind function-level imports), single writer of order state, single
  discount rule, fixture tests exit code from `tests.txt`.
- Scenario 2 (`audit-only-no-edit`): workspace tree byte-identical to the
  fixture (first assertion only).
- Scenarios 3 and 4: all assertions are semantic and stay manual.

## Harness notes

- Prompts are sent over stdin. On Windows the `claude` launcher is a `.cmd`
  shim, and cmd.exe truncates multi-line argv at the first newline, which
  silently drops the task text and every flag after it.
- With `--with-skill`, the prompt asks the agent to read
  `.claude/skills/<name>/SKILL.md` directly instead of calling the Skill tool:
  some gateways implement the Skill tool as a no-op acknowledgement that never
  injects the SKILL.md body, and the agent then spends the run budget
  searching for the skill.
- Use `--timeout 1500` on slow hosts; scenario 3 took ~22 minutes in the
  Iteration 2 runs (see [RESULTS.md](RESULTS.md)).

## Running trigger evals

**Host caveat:** skill discovery is model-dependent. On some hosts (for example
Claude Code routed to a third-party model) the agent may not consult skills
proactively even when the description matches; explicit invocation still works.
Trigger results from such hosts are noisy — re-run on the model you actually
deploy with. See [RESULTS.md](RESULTS.md) for an example run log.

1. Install the skill into a scratch workspace so the `claude` CLI can discover it:
   `<workspace>/.claude/skills/architecture-refactoring/` (copy of the skill directory).
2. Run:

```bash
python evals/run_trigger_eval.py \
  --workspace <workspace> \
  --output evals/workspace/trigger-baseline.json
```

Use `--split validation` to evaluate only the queries that must stay out of description tuning.
A should-trigger query passes at trigger rate >= 0.5; a should-not-trigger query passes below that.
For any reported result, use `--runs 3` or more: single runs are noisy (see
[RESULTS.md](RESULTS.md) for an example).
