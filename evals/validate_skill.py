"""Validate this skill against the Agent Skills specification.

Checks:
- frontmatter is valid YAML and name/description constraints hold, including
  the directory-name match
- SKILL.md length budget (< 500 lines)
- relative file references in all markdown files resolve
- no backslash paths in references
- reference files over 100 lines contain a "## Contents" section

Usage: python evals/validate_skill.py [skill-root]

Requires PyYAML (pip install PyYAML).
"""

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\]\(([^)]+)\)")


def parse_frontmatter(text):
    """Return (data, error) for the SKILL.md YAML frontmatter block.

    data is {} when the block is absent; error is a message when the block
    exists but is not a valid YAML mapping.
    """
    if not text.startswith("---"):
        return {}, None
    end = text.find("\n---", 3)
    if end == -1:
        return {}, "frontmatter: opening --- without a closing ---"
    block = text[3:end]
    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError as exc:
        return {}, "frontmatter: not valid YAML (%s)" % exc
    if data is None:
        return {}, "frontmatter: block is empty"
    if not isinstance(data, dict):
        return {}, "frontmatter: not a YAML mapping"
    return data, None


def main():
    if yaml is None:
        print("FAIL: PyYAML is required to parse frontmatter (pip install PyYAML)")
        return 1
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    errors = []
    warnings = []

    skill = root / "SKILL.md"
    if not skill.is_file():
        print("FAIL: SKILL.md not found at", root)
        return 1
    text = skill.read_text(encoding="utf-8")
    fm, fm_error = parse_frontmatter(text)
    if fm_error:
        errors.append(fm_error)
        name = ""
        description = ""
    else:
        name = fm.get("name")
        description = fm.get("description")
        if not isinstance(name, str) or not name:
            errors.append("frontmatter: missing or non-string name")
            name = ""
        else:
            if not NAME_RE.match(name) or len(name) > 64:
                errors.append("frontmatter: name breaks naming rules: %r" % name)
            if name != root.name:
                errors.append("frontmatter: name %r != directory %r" % (name, root.name))
        if not isinstance(description, str) or not description:
            errors.append("frontmatter: missing or non-string description")
            description = ""
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
