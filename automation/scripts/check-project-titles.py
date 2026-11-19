#!/usr/bin/env python3
"""Check public Project titles for narrative hooks instead of subject-led names.

The editorial guide in docs/PROJECT-EDITORIAL-ROADMAP.md explains the policy.
This intentionally applies only to published Projects, not unpublished drafts,
research titles, or the independent systems-notes repository.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
PROJECTS = ROOT / "apps/web/src/content/projects"
FIELD = re.compile(r"^(?P<name>[A-Za-z][A-Za-z0-9]*):[ \t]*(?P<value>.*)$", re.M)
HOOKS = (
    re.compile(r"^(?:why|when|how)\b", re.I),
    re.compile(r"^(?:the|a|an)\s+.+\s+(?:was|were|did|needed|could|still|had|would)\b", re.I),
)

errors = []
checked = 0
titles = {}
for path in sorted(PROJECTS.glob("*.mdx")):
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        errors.append(f"{path.name}: missing frontmatter")
        continue
    fields = {m.group("name"): m.group("value").strip().strip('"') for m in FIELD.finditer(parts[1])}
    if fields.get("draft") == "true":
        continue
    checked += 1
    title = fields.get("title", "")
    if not title:
        errors.append(f"{path.name}: missing title")
        continue
    if any(p.search(title) for p in HOOKS):
        errors.append(f"{path.name}: narrative-hook title: {title}")
    if "?" in title or "!" in title or ". " in title or title.endswith("."):
        errors.append(f"{path.name}: sentence/question-style title: {title}")
    if len(title) > 100:
        errors.append(f"{path.name}: title exceeds 100 characters")
    if title in titles:
        errors.append(f"{path.name}: duplicate title also in {titles[title]}")
    titles[title] = path.name

if errors:
    print("Project title check FAILED:")
    for error in errors:
        print(" -", error)
    sys.exit(1)
print(f"Project editorial titles: {checked} published subject-led titles checked.")
