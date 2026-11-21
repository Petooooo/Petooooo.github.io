#!/usr/bin/env python3
"""Catch numeric range tildes that Markdown renders as strikethrough."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIRS = (
    ROOT / "apps/web/i18n/editorial/projects",
    ROOT / "apps/web/src/content/projects",
)
NUMERIC_TILDE = re.compile(r"(?<=\d)\s*~\s*(?=\d)")


def find_bad_ranges(source: str) -> list[tuple[int, str]]:
    bad = []
    fenced = False
    for n, line in enumerate(source.splitlines(), 1):
        text = line.strip()
        if text.startswith(("\x60\x60\x60", "~~~")):
            fenced = not fenced
            continue
        if fenced:
            continue
        prose = re.sub(r"\x60[^\x60]*\x60", "", line)
        if NUMERIC_TILDE.search(prose):
            bad.append((n, text))
    return bad


def main() -> int:
    failed = 0
    scanned = 0
    for folder in SOURCE_DIRS:
        for path in sorted(folder.glob("*.md*")):
            scanned += 1
            for line, content in find_bad_ranges(path.read_text(encoding="utf-8")):
                print(f"{path.relative_to(ROOT)}:{line}: use en dash (–) for ranges: {content[:170]}")
                failed += 1
    if failed:
        print(f"Editorial typography: {failed} tilde range errors")
        return 1
    print(f"Editorial typography: {scanned} English/Korean articles passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
