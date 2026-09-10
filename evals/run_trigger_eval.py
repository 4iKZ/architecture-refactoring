"""Run trigger evals for the architecture-refactoring skill.

Spawns the `claude` CLI once per query in a scratch workspace that has the
skill installed at <workspace>/.claude/skills/architecture-refactoring/ and
records whether the Skill tool was invoked.

Usage:
    python evals/run_trigger_eval.py --workspace <dir> --output <results.json> \
        [--split all|train|validation] [--runs 1] [--timeout 240]
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def find_claude():
    exe = shutil.which("claude")
    if not exe:
        sys.exit("claude CLI not found on PATH")
    return exe


def triggered_in_stream(stdout, skill_name):
    """Return True if the transcript shows our skill being loaded."""
    marker = ".claude/skills/%s/SKILL.md" % skill_name
    for line in stdout.splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = event.get("message") or {}
        for block in msg.get("content") or []:
            if not isinstance(block, dict):
                continue
            if block.get("type") != "tool_use":
                continue
            name = block.get("name", "")
            payload = json.dumps(block.get("input") or {}, ensure_ascii=False)
            if name == "Skill" and skill_name in payload:
                return True
            if name in ("Read", "Glob", "Grep") and marker in payload:
                return True
    return False


def run_query(claude, workspace, query, skill_name, timeout, max_turns):
    cmd = [
        claude,
        "-p",
        query,
        "--output-format",
        "stream-json",
        "--verbose",
        "--max-turns",
        str(max_turns),
    ]
    started = time.time()
    with tempfile.TemporaryFile("w+", encoding="utf-8", errors="replace") as out_file:
        proc = subprocess.Popen(
            cmd,
            cwd=workspace,
            stdout=out_file,
            stderr=subprocess.STDOUT,
        )
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                    capture_output=True,
                )
            else:
                proc.kill()
            proc.wait()
        out_file.seek(0)
        stdout = out_file.read()
    return {
        "triggered": triggered_in_stream(stdout, skill_name),
        "returncode_ok": proc.returncode == 0,
        "duration_s": round(time.time() - started, 1),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--queries", default=str(HERE / "trigger_queries.json"))
    parser.add_argument("--output", required=True)
    parser.add_argument("--split", choices=["all", "train", "validation"], default="all")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--max-turns", type=int, default=5)
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    if not workspace.is_dir():
        sys.exit("workspace not found: %s" % workspace)

    data = json.loads(Path(args.queries).read_text(encoding="utf-8"))
    skill_name = data["skill_name"]
    queries = data["queries"]
    if args.split != "all":
        queries = [q for q in queries if q.get("split") == args.split]

    claude = find_claude()
    results = []
    for item in queries:
        runs = []
        for _ in range(args.runs):
            runs.append(run_query(claude, workspace, item["query"], skill_name, args.timeout, args.max_turns))
            status = "TRIGGERED" if runs[-1]["triggered"] else "not triggered"
            print("  run -> %s (%.1fs)" % (status, runs[-1]["duration_s"]), flush=True)
        rate = sum(1 for r in runs if r["triggered"]) / len(runs)
        threshold = 0.5
        passed = rate >= threshold if item["should_trigger"] else rate < threshold
        results.append(
            {
                "id": item["id"],
                "split": item.get("split", "all"),
                "should_trigger": item["should_trigger"],
                "trigger_rate": rate,
                "passed": passed,
                "query": item["query"],
            }
        )
        print(
            "[%s] id=%s should_trigger=%s rate=%.2f"
            % ("PASS" if passed else "FAIL", item["id"], item["should_trigger"], rate),
            flush=True,
        )

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    summary = {
        "skill_name": skill_name,
        "split": args.split,
        "runs_per_query": args.runs,
        "total": total,
        "passed": passed,
        "pass_rate": round(passed / total, 3) if total else 0.0,
        "results": results,
    }
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("summary: %d/%d passed (%.0f%%) -> %s" % (passed, total, 100 * summary["pass_rate"], out_path))


if __name__ == "__main__":
    main()
