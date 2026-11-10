#!/usr/bin/env python3
"""Validate the Bug Hunter Agent Skill and the repository's Markdown links.

Checks performed (rules from Anthropic's Agent Skills documentation):
  * SKILL.md exists and starts with YAML frontmatter delimited by '---'.
  * `name`: required, <= 64 chars, only lowercase letters, digits and hyphens,
    no XML tags, does not contain the reserved words "anthropic" or "claude",
    and matches the skill directory name.
  * `description`: required, non-empty, <= 1024 chars, no XML tags.
  * SKILL.md body is under 500 lines (best-practice guidance).
  * Every reference file is linked directly from SKILL.md (one level deep),
    and reference files do not link onward to other files.
  * Reference files longer than 100 lines have a "## Contents" section.
  * No backslashes in link targets (forward slashes only).
  * Every relative Markdown link in the repository resolves to a real file.

Uses PyYAML for frontmatter parsing when installed, otherwise a minimal
parser that supports single-line `key: value` pairs.

Usage:
    python scripts/validate_skill.py [--root PATH] [--skill NAME]
Exit status is 0 when all checks pass and 1 otherwise.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

NAME_MAX_CHARS = 64          # Agent Skills spec limit for `name`
DESCRIPTION_MAX_CHARS = 1024  # Agent Skills spec limit for `description`
BODY_MAX_LINES = 500          # best-practices guidance for SKILL.md body
TOC_THRESHOLD_LINES = 100     # best-practices: longer reference files need a TOC
RESERVED_WORDS = ("anthropic", "claude")

NAME_PATTERN = re.compile(r"^[a-z0-9-]+$")
XML_TAG_PATTERN = re.compile(r"<[^>]+>")
LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
INLINE_CODE_PATTERN = re.compile(r"`+[^`]*`+")
SKIP_DIRS = {".git", "dist", "node_modules", "__pycache__", ".venv", "venv"}


def strip_code(text: str) -> str:
    """Remove fenced code blocks and inline code so example links are ignored."""
    kept = []
    fence_char, fence_len = None, 0
    for line in text.splitlines():
        stripped = line.lstrip()
        match = re.match(r"^(`{3,}|~{3,})", stripped)
        if fence_char is None:
            if match:
                fence_char, fence_len = match.group(1)[0], len(match.group(1))
                continue
            kept.append(INLINE_CODE_PATTERN.sub("", line))
        else:
            if match and match.group(1)[0] == fence_char and len(match.group(1)) >= fence_len \
                    and stripped.rstrip() == match.group(1):
                fence_char, fence_len = None, 0
    return "\n".join(kept)


def extract_links(text: str) -> list[str]:
    return LINK_PATTERN.findall(strip_code(text))


def is_external(target: str) -> bool:
    return bool(re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target)) or target.startswith("#")


def split_frontmatter(text: str):
    """Return (frontmatter_text, body_text) or raise ValueError."""
    text = text.lstrip("﻿")
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md must start with a '---' frontmatter delimiter on line 1")
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "\n".join(lines[1:index]), "\n".join(lines[index + 1:])
    raise ValueError("SKILL.md frontmatter is missing its closing '---' delimiter")


def parse_frontmatter(frontmatter: str) -> dict:
    try:
        import yaml  # type: ignore
    except ImportError:
        yaml = None
    if yaml is not None:
        data = yaml.safe_load(frontmatter)
        if not isinstance(data, dict):
            raise ValueError("frontmatter must be a YAML mapping")
        return data
    data = {}
    for number, line in enumerate(frontmatter.splitlines(), start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[0] in " \t":
            raise ValueError(
                f"SKILL.md line {number}: multi-line YAML values need PyYAML "
                "(pip install pyyaml) to validate")
        key, sep, value = line.partition(":")
        if not sep:
            raise ValueError(f"SKILL.md line {number}: expected 'key: value'")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        data[key.strip()] = value
    return data


def validate_metadata(meta: dict, dir_name: str) -> list[str]:
    errors = []
    name = meta.get("name")
    description = meta.get("description")

    if not isinstance(name, str) or not name.strip():
        errors.append("frontmatter: 'name' is required and must be a non-empty string")
    else:
        if len(name) > NAME_MAX_CHARS:
            errors.append(f"frontmatter: 'name' is {len(name)} chars (max {NAME_MAX_CHARS})")
        if not NAME_PATTERN.match(name):
            errors.append("frontmatter: 'name' may contain only lowercase letters, numbers, and hyphens")
        if XML_TAG_PATTERN.search(name):
            errors.append("frontmatter: 'name' must not contain XML tags")
        for word in RESERVED_WORDS:
            if word in name.lower():
                errors.append(f"frontmatter: 'name' must not contain the reserved word '{word}'")
        if name != dir_name:
            errors.append(f"frontmatter: 'name' ({name}) should match the skill directory name ({dir_name})")

    if not isinstance(description, str) or not description.strip():
        errors.append("frontmatter: 'description' is required and must be non-empty")
    else:
        if len(description) > DESCRIPTION_MAX_CHARS:
            errors.append(
                f"frontmatter: 'description' is {len(description)} chars (max {DESCRIPTION_MAX_CHARS})")
        if XML_TAG_PATTERN.search(description):
            errors.append("frontmatter: 'description' must not contain XML tags")
    return errors


def validate_skill(skill_dir: pathlib.Path) -> list[str]:
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_dir.is_dir():
        return [f"skill directory not found: {skill_dir}"]
    if not skill_md.is_file():
        return [f"missing {skill_md.name} in {skill_dir}"]

    text = skill_md.read_text(encoding="utf-8")
    try:
        frontmatter, body = split_frontmatter(text)
        meta = parse_frontmatter(frontmatter)
    except ValueError as exc:
        return [str(exc)]
    except Exception as exc:  # YAML syntax errors
        return [f"frontmatter could not be parsed: {exc}"]

    errors += validate_metadata(meta, skill_dir.name)

    body_lines = body.strip("\n").count("\n") + 1 if body.strip() else 0
    if body_lines >= BODY_MAX_LINES:
        errors.append(f"SKILL.md body has {body_lines} lines (keep under {BODY_MAX_LINES})")

    linked = set()
    for target in extract_links(text):
        if "\\" in target:
            errors.append(f"SKILL.md: link '{target}' uses backslashes; use forward slashes")
            continue
        if is_external(target):
            continue
        path_part = target.split("#", 1)[0]
        resolved = (skill_dir / path_part).resolve()
        try:
            resolved.relative_to(skill_dir.resolve())
        except ValueError:
            errors.append(f"SKILL.md: link '{target}' points outside the skill directory")
            continue
        if not resolved.exists():
            errors.append(f"SKILL.md: link '{target}' does not resolve to a file")
        linked.add(resolved)

    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file() or path == skill_md:
            continue
        rel = path.relative_to(skill_dir).as_posix()
        if path.suffix == ".md":
            if path.resolve() not in linked:
                errors.append(f"{rel}: not linked directly from SKILL.md (keep references one level deep)")
            content = path.read_text(encoding="utf-8")
            onward = [t for t in extract_links(content) if not is_external(t)]
            if onward:
                errors.append(
                    f"{rel}: links to {onward}; reference files should not link onward "
                    "(keep references one level deep)")
            line_count = content.count("\n") + 1
            if line_count > TOC_THRESHOLD_LINES and not re.search(r"^##\s+Contents\s*$", content, re.M):
                errors.append(
                    f"{rel}: {line_count} lines but no '## Contents' section "
                    f"(required above {TOC_THRESHOLD_LINES} lines)")
        if "\\" in rel:
            errors.append(f"{rel}: file name contains a backslash")
    return errors


def iter_markdown(root: pathlib.Path):
    for path in sorted(root.rglob("*.md")):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        yield path


def validate_repo_links(root: pathlib.Path) -> list[str]:
    errors = []
    for path in iter_markdown(root):
        rel = path.relative_to(root).as_posix()
        for target in extract_links(path.read_text(encoding="utf-8")):
            if "\\" in target:
                errors.append(f"{rel}: link '{target}' uses backslashes")
                continue
            if is_external(target):
                continue
            path_part = target.split("#", 1)[0]
            if not path_part:
                continue
            resolved = (root / path_part.lstrip("/")) if path_part.startswith("/") else (path.parent / path_part)
            if not resolved.exists():
                errors.append(f"{rel}: broken link '{target}'")
    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=pathlib.Path(__file__).resolve().parent.parent, type=pathlib.Path)
    parser.add_argument("--skill", default="bug-hunter")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    skill_errors = validate_skill(root / args.skill)
    link_errors = validate_repo_links(root)

    for label, errors in (("Skill structure and metadata", skill_errors),
                          ("Repository Markdown links", link_errors)):
        status = "PASS" if not errors else f"FAIL ({len(errors)} problem(s))"
        print(f"{label}: {status}")
        for error in errors:
            print(f"  - {error}")
    return 1 if skill_errors or link_errors else 0


if __name__ == "__main__":
    sys.exit(main())
