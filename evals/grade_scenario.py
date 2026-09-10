"""Deterministic grading for output scenarios (hybrid grader).

Grades the mechanically verifiable assertions from evals.json and marks the
semantic ones for human/LLM review, so every run produces a grading.json in
the schema recommended by the Agent Skills evaluation guide:

    https://agentskills.io/skill-creation/evaluating-skills

Only assertions that can be checked without judgment are automated; the rest
are recorded with "passed": null and mode "manual".

Usage:
    python evals/grade_scenario.py --run-dir <run-dir> [--scenario 1|fix-import-cycle]
"""

import argparse
import ast
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOCAL_MODULES = {"orders", "billing", "db", "notifier", "main"}
STATE_KEYS = {"status", "paid_amount"}
SKIP_PARTS = {"__pycache__", ".git"}


def load_evals():
    return json.loads((HERE / "evals.json").read_text(encoding="utf-8"))


def resolve_scenario(evals, meta, explicit):
    if explicit is None:
        explicit = meta.get("scenario_id") or meta.get("scenario")
    if explicit is None:
        return None
    for scenario in evals["evals"]:
        if str(scenario["id"]) == str(explicit) or scenario["name"] == str(explicit):
            return scenario
    return None


def parse_or_none(path):
    try:
        return ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return None


def shop_modules(root):
    modules = {}
    if not root.is_dir():
        return modules
    for path in sorted(root.rglob("*.py")):
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.stem in LOCAL_MODULES:
            modules[path.stem] = path
    return modules


def _imports_from_node(node):
    names = set()
    if isinstance(node, ast.Import):
        for alias in node.names:
            parts = alias.name.split(".")
            if parts[0] == "shop" and len(parts) > 1 and parts[1] in LOCAL_MODULES:
                names.add(parts[1])
            elif parts[0] in LOCAL_MODULES:
                names.add(parts[0])
    elif isinstance(node, ast.ImportFrom):
        if node.module == "shop":
            names.update(a.name for a in node.names if a.name in LOCAL_MODULES)
        elif node.module and node.module.split(".")[0] == "shop" and len(node.module.split(".")) > 1:
            if node.module.split(".")[1] in LOCAL_MODULES:
                names.add(node.module.split(".")[1])
        elif node.level == 1:
            names.update(a.name for a in node.names if a.name in LOCAL_MODULES)
    return names


def collect_imports(tree):
    """Return (module_level_imports, function_level_imports) of local modules."""
    top, lazy = set(), set()

    def visit(node):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for sub in ast.walk(child):
                    if isinstance(sub, (ast.Import, ast.ImportFrom)):
                        lazy.update(_imports_from_node(sub))
                continue
            if isinstance(child, (ast.Import, ast.ImportFrom)):
                top.update(_imports_from_node(child))
            visit(child)

    visit(tree)
    return top, lazy


def find_cycles(graph):
    """Return cycles (lists of module names) found by DFS."""
    cycles = []
    color = {}
    stack = []

    def dfs(node):
        color[node] = 1
        stack.append(node)
        for nxt in sorted(graph.get(node, ())):
            if nxt not in graph:
                continue
            if color.get(nxt) == 1:
                cycles.append(stack[stack.index(nxt):] + [nxt])
            elif color.get(nxt, 0) == 0:
                dfs(nxt)
        stack.pop()
        color[node] = 2

    for node in sorted(graph):
        if color.get(node, 0) == 0:
            dfs(node)
    return cycles


def format_cycles(cycles):
    return "; ".join(" -> ".join(cycle) for cycle in cycles)


def graph_edges_text(graph):
    return ", ".join(
        "%s -> %s" % (name, ",".join(sorted(targets)) or "-")
        for name, targets in sorted(graph.items())
    )


def is_state_subscript(node):
    return (
        isinstance(node, ast.Subscript)
        and isinstance(node.slice, ast.Constant)
        and isinstance(node.slice.value, str)
        and node.slice.value in STATE_KEYS
    )


def state_write_hits(path):
    tree = parse_or_none(path)
    if tree is None:
        return ["could not parse %s" % path.name]
    hits = []
    for node in ast.walk(tree):
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AugAssign):
            targets = [node.target]
        for target in targets:
            if is_state_subscript(target):
                hits.append("%s:%d writes %r" % (path.name, node.lineno, target.slice.value))
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr in {"append", "update", "pop"}:
                value = func.value
                if isinstance(value, ast.Attribute) and value.attr in {"PAYMENTS", "ORDERS"}:
                    hits.append("%s:%d calls db.%s.%s()" % (path.name, node.lineno, value.attr, func.attr))
    return hits


def has_discount_rule(node):
    for sub in ast.walk(node):
        if isinstance(sub, ast.BinOp) and isinstance(sub.op, ast.Mult):
            for side in (sub.left, sub.right):
                if (
                    isinstance(side, ast.Constant)
                    and isinstance(side.value, (int, float))
                    and abs(float(side.value) - 0.9) < 1e-9
                ):
                    return True
    return False


def discount_defs(modules):
    found = []
    for name, path in modules.items():
        tree = parse_or_none(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if "discount" in node.name.lower() or has_discount_rule(node):
                    found.append("%s.%s" % (name, node.name))
    return found


def tests_exit_code(run_dir):
    path = run_dir / "tests.txt"
    if not path.is_file():
        return None
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if lines and lines[0].startswith("exit="):
        try:
            return int(lines[0].split("=", 1)[1])
        except ValueError:
            return None
    return None


def grade_fix_import_cycle(run_dir, fixture_dir):
    """Auto-grade scenario 1 assertions; returns {index: (passed, evidence)}."""
    outputs = run_dir / "outputs"
    modules = shop_modules(outputs)
    if not modules:
        return {}, "outputs/ not found; cannot auto-grade"

    top_edges, lazy_edges = {}, {}
    for name, path in modules.items():
        tree = parse_or_none(path)
        if tree is None:
            return {}, "could not parse %s; cannot auto-grade" % path.name
        top, lazy = collect_imports(tree)
        top_edges[name] = top
        lazy_edges[name] = lazy

    graph = {name: {m for m in edges if m in modules} for name, edges in top_edges.items()}
    combined = {
        name: ({m for m in top_edges[name] if m in modules} | {m for m in lazy_edges[name] if m in modules})
        for name in modules
    }

    cycles = find_cycles(graph)
    if cycles:
        cycle_ok, cycle_evidence = False, "module-level import cycle remains: %s (edges: %s)" % (
            format_cycles(cycles),
            graph_edges_text(graph),
        )
    else:
        hidden = find_cycles(combined)
        if hidden:
            cycle_ok, cycle_evidence = False, "cycle hidden behind function-level import: %s" % format_cycles(hidden)
        else:
            cycle_ok, cycle_evidence = True, "module-level import graph is acyclic (edges: %s)" % graph_edges_text(graph)

    writer_hits = {}
    for name, path in modules.items():
        hits = state_write_hits(path)
        if hits:
            writer_hits[name] = hits
    if len(writer_hits) == 1:
        owner = next(iter(writer_hits))
        owner_ok = True
        owner_evidence = "single writer of order state: %s (%s)" % (owner, ", ".join(writer_hits[owner]))
    elif not writer_hits:
        owner_ok = False
        owner_evidence = "no module writes order state; the paid transition has no owner"
    else:
        owner_ok = False
        owner_evidence = "multiple writers of order state: %s" % "; ".join(
            "%s (%s)" % (name, ", ".join(hits)) for name, hits in sorted(writer_hits.items())
        )

    defs = discount_defs(modules)
    if len(defs) == 1:
        discount_ok, discount_evidence = True, "single discount rule definition: %s" % defs[0]
    elif not defs:
        discount_ok, discount_evidence = False, "no discount rule found; pricing logic may be missing"
    else:
        discount_ok, discount_evidence = False, "duplicated discount rules: %s" % ", ".join(defs)

    code = tests_exit_code(run_dir)
    if code is None:
        tests_ok, tests_evidence = None, "tests.txt not found; run the fixture test suite manually"
    elif code == 0:
        tests_ok, tests_evidence = True, "tests.txt reports exit=0"
    else:
        tests_ok, tests_evidence = False, "tests.txt reports exit=%d" % code

    auto = {1: (cycle_ok, cycle_evidence), 2: (owner_ok, owner_evidence), 3: (discount_ok, discount_evidence), 4: (tests_ok, tests_evidence)}
    return auto, None


def tree_hashes(root):
    hashes = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_PARTS for part in path.parts) or path.suffix == ".pyc":
            continue
        hashes[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def grade_audit_only(run_dir, fixture_dir):
    """Auto-grade scenario 2 assertion 0 (no workspace changes)."""
    outputs = run_dir / "outputs"
    if not outputs.is_dir() or not fixture_dir.is_dir():
        return {}, "outputs/ not found; cannot auto-grade"
    before = tree_hashes(fixture_dir)
    after = tree_hashes(outputs)
    changed = sorted(f for f in set(before) & set(after) if before[f] != after[f])
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    if changed or added or removed:
        parts = []
        if changed:
            parts.append("modified: %s" % ", ".join(changed))
        if added:
            parts.append("created: %s" % ", ".join(added))
        if removed:
            parts.append("deleted: %s" % ", ".join(removed))
        return {0: (False, "workspace changed (%s)" % "; ".join(parts))}, None
    return {0: (True, "workspace tree is byte-identical to the fixture")}, None


def auto_checks(scenario, run_dir):
    fixture_dir = HERE / "fixtures" / scenario["fixture"]
    if scenario["id"] == 1:
        return grade_fix_import_cycle(run_dir, fixture_dir)
    if scenario["id"] == 2:
        return grade_audit_only(run_dir, fixture_dir)
    return {}, None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, help="run directory containing outputs/, tests.txt, meta.json")
    parser.add_argument("--scenario", default=None, help="scenario id or name (default: from meta.json)")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    if not run_dir.is_dir():
        sys.exit("run directory not found: %s" % run_dir)

    evals = load_evals()
    meta = {}
    meta_path = run_dir / "meta.json"
    if meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    scenario = resolve_scenario(evals, meta, args.scenario)
    if scenario is None:
        sys.exit("cannot determine scenario; pass --scenario (run dir has no usable meta.json)")

    auto, note = auto_checks(scenario, run_dir)
    results = []
    for index, text in enumerate(scenario["assertions"]):
        if index in auto and auto[index][0] is not None:
            passed, evidence = auto[index]
            results.append({"text": text, "passed": passed, "mode": "auto", "evidence": evidence})
        else:
            evidence = (auto[index][1] if index in auto else None) or note or "semantic assertion; grade from transcript.md and outputs/"
            results.append({"text": text, "passed": None, "mode": "manual", "evidence": evidence})

    passed = sum(1 for r in results if r["passed"] is True)
    failed = sum(1 for r in results if r["passed"] is False)
    manual = sum(1 for r in results if r["passed"] is None)
    decided = passed + failed
    payload = {
        "scenario": scenario["name"],
        "scenario_id": scenario["id"],
        "run_dir": str(run_dir),
        "graded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "grader": "evals/grade_scenario.py (deterministic subset)",
        "assertion_results": results,
        "summary": {
            "passed": passed,
            "failed": failed,
            "manual": manual,
            "total": len(results),
            "decided": decided,
            "pass_rate": round(passed / decided, 3) if decided else None,
        },
    }
    out_path = run_dir / "grading.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print("scenario:", scenario["name"], "| run:", run_dir)
    for result in results:
        status = "PASS" if result["passed"] is True else "FAIL" if result["passed"] is False else "MANUAL"
        print("[%s] %s" % (status, result["text"]))
        print("        %s" % result["evidence"])
    print(
        "summary: %d passed, %d failed, %d manual (auto pass rate %s) -> %s"
        % (passed, failed, manual, payload["summary"]["pass_rate"], out_path)
    )


if __name__ == "__main__":
    main()
