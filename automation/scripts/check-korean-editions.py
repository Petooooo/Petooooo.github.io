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
EDITORIALS = ROOT / "apps/web/i18n/editorial/projects"
PUBLIC_PROJECTS = ROOT / "apps/web/src/content/projects"
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
        parts=p.relative_to(DIST).parts
        is_project=len(parts)==3 and parts[0]=="projects"
        editorial_slug=parts[1] if is_project and (EDITORIALS/(parts[1]+".md")).exists() else None
        if editorial_slug:
            if f"hand-edited Korean editorial: {editorial_slug}" not in ko:
                errors.append(f"Human-written editorial not injected: {editorial_slug}")
            body=ko.split(f"hand-edited Korean editorial: {editorial_slug}",1)[-1]
            if len(re.findall(r"[가-힣]",body))<450:
                errors.append(f"Human-written article too short or missing: {editorial_slug}")
            if chr(92)+chr(96) in body:
                errors.append(f"Literal escaped inline backtick: {editorial_slug}")
            if "<h2>" not in body or "<p>" not in body:
                errors.append(f"Missing Korean prose headings/paragraphs: {editorial_slug}")
        elif codes(en)!=codes(ko):
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

    all_published=[
        p for p in sorted(PUBLIC_PROJECTS.glob("*.mdx"))
        if not re.search(r"^draft:\s*true\s*$",p.read_text(),re.M)
    ]
    for source_file in all_published:
        slug=source_file.stem
        handwritten=EDITORIALS/(slug+".md")
        html_file=DIST/"projects"/slug/"kr/index.html"
        if not handwritten.is_file():
            errors.append(f"Published project lacks human Korean prose: {slug}")
            continue
        if not html_file.exists():
            errors.append(f"Published project missing Korean page: {slug}")
            continue
        translated=handwritten.read_text()
        if len(re.findall(r"[가-힣]",translated))<600:
            errors.append(f"Human Korean prose too short: {slug}")
        original=source_file.read_text()
        source_figures=set(re.findall(r'<img\s+src="(\/figures\/[^"]+\.svg)"',original))
        translated_figures=set(re.findall(r'\{\{figure\s+(\/figures\/[^\s|]+\.svg)',translated))
        if source_figures!=translated_figures:
            errors.append(f"Figure mismatch: {slug}, missing={source_figures-translated_figures}, extra={translated_figures-source_figures}")
        rendered=html_file.read_text()
        if "hand-edited Korean editorial: "+slug not in rendered:
            errors.append(f"Expected curated Korean article body: {slug}")
        for figure in source_figures:
            localized=figure.replace("/figures/","/figures/ko/",1)
            if f'src="{localized}"' not in rendered:
                errors.append(f"Localized image not linked: {slug}: {localized}")
    svg_files=list((DIST/"figures/ko").rglob("*.svg"))
    for p in svg_files:
        try:ET.parse(p)
        except ET.ParseError as e:errors.append(f"Invalid translated SVG: {p} ({e})")

    # Catch known machine-translation artifacts in published diagram captions.
    # Unpublished draft SVGs in a working tree do not count in this audit.
    referenced=set()
    for source_page in source:
        loc=source_page.parent/"kr/index.html" if source_page!=DIST/"index.html" else DIST/"kr/index.html"
        if not loc.is_file():
            continue
        html=loc.read_text(encoding="utf-8")
        referenced.update(re.findall(r'(?:src|href)="(/figures/ko/[^"]+[.]svg)"',html))

    mistranslations=(
        "회사연혁", "제품정보", "팟캐스트", "자주 묻는 질문",
        "사이트맵", "본문 바로가기", "회사 소개", "구매하기",
        "로그인 해주세요", "고객 검증", "일러스트레이션",
    )
    for figure in sorted(referenced):
        svg=DIST/figure.lstrip("/")
        if not svg.is_file():
            errors.append(f"Missing SVG referenced by Korean page: {figure}")
            continue
        try:root=ET.parse(svg).getroot()
        except ET.ParseError:continue
        for el in root.iter():
            if el.tag.rsplit("}",1)[-1] not in {"text","tspan"}:
                continue
            label=(el.text or "").strip()
            if any(term in label for term in mistranslations):
                errors.append(f"Unnatural SVG label: {figure}: {label[:120]}")
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
