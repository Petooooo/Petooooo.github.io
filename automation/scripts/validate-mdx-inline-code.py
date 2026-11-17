#!/usr/bin/env python3
"""Reject escaped inline-code delimiters in MDX prose.

A backslash before an inline Markdown delimiter turns code spans into literal
backtick characters in the published page. Fenced code blocks are excluded
because they may legitimately demonstrate Markdown escape syntax.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTENT = REPO_ROOT / "apps/web/src/content"


def find_escaped_delimiters(content_root: Path) -> list[str]:
    escaped_tick = chr(92) + chr(96)
    tick_fence = chr(96) * 3
    findings: list[str] = []

    for path in sorted(content_root.rglob("*")):
        if not path.is_file() or path.suffix not in {".md", ".mdx"}:
            continue
        fence_char = None
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.lstrip()
            current = (
                chr(96) if stripped.startswith(tick_fence)
                else "~" if stripped.startswith("~~~")
                else None
            )
            if current:
                if fence_char is None:
                    fence_char = current
                elif fence_char == current:
                    fence_char = None
                continue
            if fence_char is not None:
                continue
            if escaped_tick in line:
                display_path = path.relative_to(content_root)
                findings.append(f"{display_path}:{lineno}: escaped inline-code backtick (backslash + backtick)")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_CONTENT)
    args = parser.parse_args()
    if not args.root.is_dir():
        parser.error(f"Content directory does not exist: {args.root}")
    findings = find_escaped_delimiters(args.root)
    if findings:
        print("ERROR: Markdown inline-code delimiters are unnecessarily escaped:")
        print("\n".join("  " + issue for issue in findings))
        print("Remove the preceding backslash in prose, or use a fenced code block for literal examples.")
        return 1
    print("MDX inline-code delimiters: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
