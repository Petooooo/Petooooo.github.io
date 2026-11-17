#!/usr/bin/env python3
"""Sanity checks for opt-in Korean static pages and diagram variants."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import json
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "apps/web/dist"
CORE_PROJECTS = [
    "rokaf-offline-gitops-delivery",
    "rokaf-service-lb-hostport-conflict",
    "rokaf-object-storage-migration",
    "rokaf-clickhouse-replication-migration",
    "rokaf-gpu-scheduling-and-capacity",
]


class CodeText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth=0
        self.acc=[]
        self.values=[]

    def handle_starttag(self,tag,attrs):
        if tag=="code":
            self.depth+=1
            if self.depth==1:self.acc=[]

    def handle_endtag(self,tag):
        if tag=="code" and self.depth:
            self.depth-=1
            if self.depth==0:self.values.append("".join(self.acc))

    def handle_data(self,data):
        if self.depth:self.acc.append(data)


def codes(s:str)->list[str]:
    p=CodeText()
    p.feed(s)
    p.close()
    return p.values


def main():
    source=[
        p for p in sorted(DIST.rglob("index.html"))
        if "kr" not in p.relative_to(DIST).parts
        and "404" not in p.relative_to(DIST).parts
        and not p.relative_to(DIST).as_posix().startswith("projects/kdt-")
    ]
    errors=[]
    count=0
    for p in source:
        loc=p.parent/"kr/index.html" if p!=DIST/"index.html" else DIST/"kr/index.html"
        if not loc.exists():
            errors.append(f"Missing Korean route: {loc.relative_to(DIST)}")
            continue
        en=p.read_text(encoding="utf-8")
        ko=loc.read_text(encoding="utf-8")
        if not re.search(r'<html[^>]*lang="en"',en):
            errors.append(f"Original lost English lang: {p}")
        if re.search(r'<meta name="robots" content="noindex,nofollow"',en):
            errors.append(f"Original incorrectly hidden: {p}")
        if not re.search(r'<html[^>]*lang="ko"',ko):
            errors.append(f"Missing Korean lang: {loc}")
        if '<meta name="robots" content="noindex,nofollow"' not in ko:
            errors.append(f"Missing noindex: {loc}")
        if codes(en)!=codes(ko):
            errors.append(f"Code span changed during translation: {loc}")
        for m in re.finditer(r'<(?:a|img)\s+[^>]*(?:href|src)="([^"]+\.svg)"',ko):
            href=m.group(1)
            if href.startswith("https://raw.githubusercontent.com/Petooooo/systems-notes/main/assets/"):
                errors.append(f"Raw SVG not localized: {loc} -> {href}")
            elif href.startswith("/figures/") and not (DIST/href.lstrip("/")).exists():
                errors.append(f"Broken Korean SVG link: {loc} -> {href}")
        count+=1

    for slug in CORE_PROJECTS:
        article=DIST/"projects"/slug/"kr/index.html"
        if not article.is_file():
            errors.append(f"Missing key project: {slug}")
        elif len(re.findall(r'[가-힣]',article.read_text()))<100:
            errors.append(f"Article text appears untranslated: {slug}")

    svg_files=list((DIST/"figures/ko").rglob("*.svg"))
    for p in svg_files:
        try:ET.parse(p)
        except ET.ParseError as e:errors.append(f"Invalid translated SVG: {p} ({e})")
    if len(svg_files)<60:errors.append(f"Too few localized SVGs: {len(svg_files)}")
    sitemap=" ".join(p.read_text() for p in DIST.glob("sitemap*.xml"))
    if re.search(r'/kr(?:/|<)',sitemap):errors.append("Hidden /kr editions leaked into sitemap")
    if re.search(r'[/]kr[/]',(DIST/"projects/index.html").read_text()):
        errors.append("Korean URL appears in English Projects HTML")

    summary={"english_pages":len(source),"korean_pages_checked":count,
             "localized_svgs":len(svg_files),"errors":errors}
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    return 1 if errors else 0


if __name__=="__main__":
    sys.exit(main())
