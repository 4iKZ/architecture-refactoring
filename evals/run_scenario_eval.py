"""Run one output scenario from evals.json against the claude CLI.

Handles Windows process-tree cleanup on timeout, snapshots outputs,
and runs the fixture test suite afterwards as a behavior check.

Usage:
    python evals/run_scenario_eval.py --scenario 1 --workspace <ws> \
        [--with-skill <path-to-skill-dir>] --out <run-dir> \
        [--timeout 900] [--max-turns 25]
"""

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def build_prompt(task_prompt, skill_name, with_skill):
    if not with_skill:
        return task_prompt
    # The skill is delivered by reading its file: on some hosts (verified
    # against this repo's gateway) the Skill tool only acknowledges the
    # invocation and never injects the SKILL.md body, and the follow-up
    # filesystem hunt wastes most of the run budget.
    return (
        "Before doing anything else, read the skill instructions at "
        ".claude/skills/%s/SKILL.md (relative to the current directory) and "
        "follow them for this task; read the reference files it points to "
        "when needed.\n\nTask: %s" % (skill_name, task_prompt)
    )


def run_claude(claude, workspace, prompt, timeout, max_turns, stream_path):
    # The prompt is sent over stdin: on Windows the `claude` launcher is a
    # .cmd shim, and cmd.exe truncates a multi-line argv at the first newline
    # (which also swallowed the flags that followed the prompt).
    cmd = [
        claude,
        "-p",
        "--output-format",
        "json",
        "--max-turns",
        str(max_turns),
    ]
    started = time.time()
    with stream_path.open("w", encoding="utf-8", errors="replace") as out_file:
        proc = subprocess.Popen(
            cmd,
            cwd=workspace,
            stdin=subprocess.PIPE,
            stdout=out_file,
            stderr=subprocess.STDOUT,
        )
        try:
            proc.communicate(input=prompt.encode("utf-8"), timeout=timeout)
            timed_out = False
        except subprocess.TimeoutExpired:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                    capture_output=True,
                )
            else:
                proc.kill()
            proc.communicate()
            timed_out = True
    return {
        "timed_out": timed_out,
        "duration_s": round(time.time() - started, 1),
        "returncode": proc.returncode,
    }


def extract_result(stream_path):
    raw = stream_path.read_text(encoding="utf-8", errors="replace")
    final_text = raw.strip()
    cost = None
    turns = None
    for line in raw.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "result":
            final_text = event.get("result") or ""
            cost = event.get("total_cost_usd")
            turns = event.get("num_turns")
    return final_text, cost, turns


def run_tests(fixture_dir):
    if not (fixture_dir / "tests").is_dir():
        return "no tests directory"
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=fixture_dir,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return "exit=%s\n%s\n%s" % (proc.returncode, proc.stdout, proc.stderr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True, help="scenario id or name")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--with-skill", default=None, help="path to a skill directory to install")
    parser.add_argument("--out", required=True)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--max-turns", type=int, default=25)
    args = parser.parse_args()

    data = json.loads((HERE / "evals.json").read_text(encoding="utf-8"))
    skill_name = data["skill_name"]
    scenario = next(
        (s for s in data["evals"] if str(s["id"]) == str(args.scenario) or s["name"] == args.scenario),
        None,
    )
    if scenario is None:
        sys.exit("scenario not found: %s" % args.scenario)

    workspace = Path(args.workspace).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    target = workspace / scenario["workspace_dir"]
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(HERE / "fixtures" / scenario["fixture"], target)

    if args.with_skill:
        skill_src = Path(args.with_skill).resolve()
        skill_dst = workspace / ".claude" / "skills" / skill_name
        if skill_dst.exists():
            shutil.rmtree(skill_dst)
        skill_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(skill_src, skill_dst)

    claude = shutil.which("claude")
    if not claude:
        sys.exit("claude CLI not found on PATH")

    prompt = build_prompt(scenario["prompt"], skill_name, args.with_skill)
    stream_path = out_dir / "stream.jsonl"
    print("running scenario %s (%s) ..." % (scenario["id"], scenario["name"]), flush=True)
    run_info = run_claude(claude, workspace, prompt, args.timeout, args.max_turns, stream_path)
    final_text, cost, turns = extract_result(stream_path)
    (out_dir / "transcript.md").write_text(final_text, encoding="utf-8")
    tests = run_tests(target)
    (out_dir / "tests.txt").write_text(tests, encoding="utf-8")
    outputs_dir = out_dir / "outputs"
    if outputs_dir.exists():
        shutil.rmtree(outputs_dir)
    shutil.copytree(target, outputs_dir, ignore=shutil.ignore_patterns("__pycache__", ".git"))

    meta = {
        "scenario": scenario["name"],
        "scenario_id": scenario["id"],
        "with_skill": bool(args.with_skill),
        "prompt": prompt,
        "timed_out": run_info["timed_out"],
        "duration_s": run_info["duration_s"],
        "num_turns": turns,
        "cost_usd": cost,
        "tests": tests.splitlines()[0] if tests else "",
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(meta, indent=2, ensure_ascii=False), flush=True)
    if run_info["timed_out"]:
        print("WARNING: run timed out", flush=True)


if __name__ == "__main__":
    main()
