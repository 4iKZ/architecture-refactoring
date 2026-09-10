"""Validate this skill against the Agent Skills specification.

Checks:
- frontmatter name/description constraints and directory-name match
- SKILL.md length budget (< 500 lines)
- relative file references in all markdown files resolve
- no backslash paths in references
- reference files over 100 lines contain a "## Contents" section

Usage: python evals/validate_skill.py [skill-root]
"""

import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\]\(([^)]+)\)")


def parse_frontmatter(text):
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    block = text[3:end]
    data = {}
    current_key = None
    for line in block.splitlines():
        if not line.strip():
            continue
        if line[0] not in " \t" and ":" in line:
            key, _, value = line.partition(":")
            current_key = key.strip()
            data[current_key] = value.strip()
        elif current_key:
            data[current_key] += " " + line.strip()
    return data


def main():
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    errors = []
    warnings = []

    skill = root / "SKILL.md"
    if not skill.is_file():
        print("FAIL: SKILL.md not found at", root)
        return 1
    text = skill.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)

    name = fm.get("name", "")
    description = fm.get("description", "")
    if not name:
        errors.append("frontmatter: missing name")
    else:
        if not NAME_RE.match(name) or len(name) > 64:
            errors.append("frontmatter: name breaks naming rules: %r" % name)
        if name != root.name:
            errors.append("frontmatter: name %r != directory %r" % (name, root.name))
    if not description:
        errors.append("frontmatter: missing description")
    elif not (1 <= len(description) <= 1024):
        errors.append("frontmatter: description length %d out of 1..1024" % len(description))

    lines = len(text.splitlines())
    if lines >= 500:
        errors.append("SKILL.md has %d lines (>= 500)" % lines)

    md_files = [
        path
        for path in sorted(root.rglob("*.md"))
        if "evals/workspace" not in path.as_posix()
        and "evals\\workspace" not in str(path)
        and ".git" not in path.parts
    ]
    for path in md_files:
        body = path.read_text(encoding="utf-8")
        rel = path.relative_to(root)
        if (
            path.name != "SKILL.md"
            and path.parent.name == "references"
            and len(body.splitlines()) > 100
            and "## Contents" not in body
        ):
            warnings.append("%s is >100 lines without a Contents section" % rel)
        for target in LINK_RE.findall(body):
            target = target.strip()
            if (
                target.startswith(("http://", "https://", "#", "mailto:"))
                or not target
            ):
                continue
            if "\\" in target:
                errors.append("%s: backslash in reference %r" % (path.relative_to(root), target))
                continue
            clean = target.split("#", 1)[0]
            if not clean:
                continue
            resolved = (path.parent / clean).resolve()
            if not resolved.exists():
                errors.append("%s: dead reference %r" % (path.relative_to(root), target))

    print("skill root:", root)
    print("name:", name, "| description chars:", len(description), "| SKILL.md lines:", lines)
    print("markdown files scanned:", len(md_files))
    for warning in warnings:
        print("WARN:", warning)
    for error in errors:
        print("ERROR:", error)
    if errors:
        print("RESULT: FAIL (%d errors, %d warnings)" % (len(errors), len(warnings)))
        return 1
    print("RESULT: PASS (%d warnings)" % len(warnings))
    return 0


if __name__ == "__main__":
    sys.exit(main())
