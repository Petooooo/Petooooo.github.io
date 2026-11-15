#!/usr/bin/env python3
"""Import reviewed public notes from Petooooo/systems-notes at build time.

The source repo is checked out separately by GitHub Actions. Only validated,
explicitly published Markdown/MDX files enter the Astro content collection.
Generated copies stay untracked; source files stay in systems-notes.
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "apps/web/src/content/notes/external-study"
VALID_SLUG = re.compile(r"^study-[a-z0-9]+(?:-[a-z0-9]+)*$")
FIELD = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*?)\s*$")


def metadata(text: str) -> dict[str, str]:
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise ValueError("Missing YAML frontmatter")
    front = text[4:].split("\n---\n", 1)[0]
    result: dict[str, str] = {}
    for line in front.splitlines():
        match = FIELD.match(line)
        if match:
            result[match.group(1)] = match.group(2).strip().strip("'\"")
    return result


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 automation/scripts/sync-systems-notes.py <source-repository>", file=sys.stderr)
        return 2

    source = Path(sys.argv[1]).resolve() / "notes"
    if not source.is_dir():
        print(f"Study notes folder not found: {source}", file=sys.stderr)
        return 2

    # Stage in memory first; fail without altering the generated site content.
    selected: list[tuple[Path, str]] = []
    known_slugs: set[str] = set()
    for file in sorted(source.rglob("*")):
        if not file.is_file() or file.suffix.lower() not in (".md", ".mdx"):
            continue
        relative = file.relative_to(source)
        if file.name.lower() == "readme.md" or any(part.startswith("_") for part in relative.parts):
            continue
        if file.is_symlink():
            raise ValueError(f"Symlink note not accepted: {relative}")
        text = file.read_text(encoding="utf-8")
        info = metadata(text)
        if info.get("draft") != "false":
            continue
        if info.get("reviewed") != "true" or info.get("sensitivity") != "public":
            raise ValueError(f"Unreviewed or nonpublic note cannot be published: {relative}")
        slug = info.get("slug", "")
        if not VALID_SLUG.fullmatch(slug):
            raise ValueError(f"Invalid study slug: {relative}")
        if slug in known_slugs:
            raise ValueError(f"Duplicate published study slug: {slug}")
        known_slugs.add(slug)
        selected.append((relative, text))

    if TARGET.is_symlink():
        raise ValueError("Generated notes directory must not be a symlink")
    if TARGET.exists():
        shutil.rmtree(TARGET)
    TARGET.mkdir(parents=True)

    for relative, text in selected:
        destination = TARGET / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding="utf-8")
        print(f"Imported: {relative}")

    print(f"Imported {len(selected)} reviewed public study note(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
