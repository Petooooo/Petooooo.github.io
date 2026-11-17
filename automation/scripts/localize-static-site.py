#!/usr/bin/env python3
"""Create unpublished, opt-in /kr/ static pages without modifying English content.

Usage:
  python3 automation/scripts/localize-static-site.py translate  # local/offline Argos en->ko
  python3 automation/scripts/localize-static-site.py build      # CI: no model/network
  python3 automation/scripts/localize-static-site.py collect    # show missing translations

The source-of-truth is generated English HTML and SVGs. The checked-in Korean
catalog contains reviewed/editable source -> translation pairs. New English
strings make the CI build fail until the catalog is refreshed.
"""
from __future__ import annotations

import argparse
import hashlib
from html import escape, unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import sys
import time
from urllib.parse import urlsplit, urlunsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "apps" / "web"
DIST = WEB / "dist"
CATALOG = WEB / "i18n" / "ko.json"
OVERRIDE_FILE = WEB / "i18n" / "ko-overrides.json"
NOTES_ROOTS = [ROOT / ".external" / "systems-notes", ROOT.parent / "systems-notes"]
INTERNAL_HOSTS = {"petooooo.github.io", "www.petooooo.github.io"}
RAW_PREFIX = "https://raw.githubusercontent.com/Petooooo/systems-notes/main/assets/"
HTML_SKIP = {"script", "style", "pre", "code", "kbd", "samp", "textarea", "noscript", "svg", "math"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
        "param", "source", "track", "wbr"}
TECH_WORDS = {
    "GPU", "CPU", "VRAM", "RAM", "ROM", "SM", "MIG", "CI", "CD", "S3", "HTTP", "HTTPS",
    "API", "SQL", "HTML", "XML", "JSON", "YAML", "IP", "TCP", "UDP", "DNS", "TLS",
    "SSD", "HDD", "NVMe", "NAND", "PCIe", "I/O", "NFS", "VFS", "SLA", "SLO", "ZNS",
    "FPGA", "LUT", "PE", "IM2COL", "K3s", "K8s", "etcd", "Kaniko", "GitLab",
    "Argo", "ArgoCD", "ClickHouse", "Kubernetes", "Docker", "MinIO", "Nexus3",
    "Longhorn", "NodePort", "hostPort", "LoadBalancer", "GitOps", "CoreDNS", "Flannel",
    "RabbitMQ", "Langfuse", "Redis", "Valkey", "Prometheus", "Grafana", "Traefik",
    "MetalLB", "Kubectl", "TFLite", "TensorFlow", "OpenFGA", "OAuth2", "CNI"
}
OVERRIDES = {
    "Projects": "프로젝트", "Research": "연구", "Notes": "노트",
    "About": "소개", "CV": "이력서", "Archive": "보관함",
    "Back to Projects": "프로젝트 목록으로",
    "Back to Notes": "노트 목록으로",
    "Back to Research": "연구 목록으로",
    "Back to Archive": "보관함으로",
    "Published": "게시일", "Updated": "수정일", "Area": "분야",
    "Type": "유형", "Series": "시리즈", "Source": "출처",
    "Problem": "문제", "Category": "분류", "Uncategorized": "미분류",
    "Projects & engineering": "프로젝트 및 엔지니어링",
    "Selected work": "주요 작업", "Systems engineering records": "시스템 엔지니어링 기록",
    "Field notes & open questions": "현장 기록과 미해결 문제",
    "Technical notebook": "기술 노트", "Recent notes": "최근 노트",
    "Research interests": "연구 관심 분야", "Technical skills": "기술 역량",
    "Education": "학력", "Experience": "경력", "Selected projects": "주요 프로젝트",
    "Technical training": "기술 교육", "Foundation": "기초", "Toolkit": "기술 스택",
    "The copy finished. Did the objects arrive?": "복사는 끝났다. 객체는 제대로 도착했을까?",
    "A second Pod is not a second data replica": "Pod를 하나 더 만든다고 데이터 복제본이 생기지는 않는다",
    "One physical GPU, three different ownership models": "물리 GPU 하나, 세 가지 자원 할당 방식",
    "TIME-SLICING": "타임 슬라이싱", "WHOLE DEVICE": "GPU 전체 할당",
    "Shared device and VRAM": "GPU와 VRAM 공유",
    "Exclusive allocation": "단독 할당",
    "Hardware instances*": "하드웨어 인스턴스*",
    "PHYSICAL GPU": "물리 GPU", "SAME PHYSICAL GPU": "동일한 물리 GPU",
    "GPU memory": "GPU 메모리", "One shared memory pool": "하나의 공유 메모리 풀",
    "Compute / SMs": "연산 자원 / SM", "one allocated workload": "단독 할당된 워크로드",
    "A, B and C compete for VRAM": "A·B·C가 VRAM을 공유하며 경쟁",
    "No hard memory or fault isolation": "메모리·장애 영역의 하드 격리 없음",
    "Separated compute and memory paths": "연산·메모리 경로가 분리됨",
    "Multiple logical GPU requests": "여러 개의 논리 GPU 요청",
    "Partition profiles have fixed shapes": "미리 정의된 파티션 크기",
    "Decision boundary": "선택 기준",
    "available device memory": "사용 가능한 GPU 메모리",
    "cross-workload interference": "워크로드 간 간섭",
    "hardware eligibility": "하드웨어 지원 여부",
    "The registry recovery paradox": "레지스트리 복구의 역설",
    "Source-to-image provenance and GitOps desired/live convergence answer different questions":
      "이미지 출처 검증과 GitOps의 선언 상태·실제 상태 수렴은 서로 다른 문제다",
    "A healthy process does not prove that the stored data can still be read.":
      "프로세스가 정상적으로 실행 중이라고 해서 저장된 데이터를 읽을 수 있다는 뜻은 아니다.",
    "A successfully built container image is not a deployed service.":
      "컨테이너 이미지 빌드에 성공했다고 해서 서비스 배포까지 완료된 것은 아니다.",
}

def english_text(s: str) -> bool:
    text = unescape(s).strip()
    if len(text) < 2 or not re.search(r"[A-Za-z]", text):
        return False
    if re.search(r"[가-힣]", text):
        return False  # already Korean: preserve technical English inside Korean notes
    if text in TECH_WORDS:
        return False
    # Pure technical tokens, version identifiers, metrics, and URLs are not prose.
    if re.fullmatch(r"[A-Za-z_][A-Za-z_0-9/.:+#-]*", text):
        if text in TECH_WORDS or len(text) <= 3 or re.search(r"[/_.0-9]", text):
            return False
    if re.fullmatch(r"[\d .,:%+\-/—–→×()]+", text):
        return False
    if re.fullmatch(r"[\w.@/#:+-]+\.(?:com|org|io|svg|png|jpg)", text, re.I):
        return False
    return True

def local_string(source: str, catalog: dict[str, str], missing: set[str]) -> str:
    if not english_text(source):
        return source
    target = catalog.get(source, "").strip()
    if not target and source in OVERRIDES:
        target = OVERRIDES[source]
    if not target:
        missing.add(source)
        return source
    return target

def translate_part(data: str, catalog: dict[str, str], missing: set[str]) -> str:
    if not data or not data.strip():
        return data
    stripped = data.strip()
    translated = local_string(stripped, catalog, missing)
    if translated == stripped:
        return data
    prefix = data[:len(data)-len(data.lstrip())]
    suffix = data[len(data.rstrip()):]
    return prefix + translated + suffix

def note_root() -> Path | None:
    for p in NOTES_ROOTS:
        if p.is_dir() and (p / "assets").is_dir():
            return p
    return None

def svg_inputs(dist: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for p in (dist / "figures").rglob("*.svg"):
        rel = "/" + p.relative_to(dist).as_posix()
        if not rel.startswith("/figures/ko/"):
            files[rel] = p
    notes = note_root()
    if notes:
        for p in (notes / "assets").rglob("*.svg"):
            files[RAW_PREFIX + p.relative_to(notes / "assets").as_posix()] = p
    return files

def ko_svg_path(source: str) -> str:
    if source.startswith(RAW_PREFIX):
        return "/figures/ko/notes/" + source[len(RAW_PREFIX):]
    if source.startswith("/figures/"):
        return "/figures/ko/" + source[len("/figures/"):]
    return source

SVG_NS = "{http://www.w3.org/2000/svg}"

def iter_svg_strings(source: Path):
    try:
        root = ET.parse(source).getroot()
    except ET.ParseError as exc:
        raise RuntimeError(f"Invalid SVG {source}: {exc}") from exc
    for el in root.iter():
        if el.tag.rsplit("}", 1)[-1] in {"title", "desc", "text", "tspan"}:
            if el.text and english_text(el.text):
                yield el.text.strip()

def create_svg_ko(source: Path, output: Path, catalog: dict[str,str], missing: set[str]):
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    tree = ET.parse(source)
    for el in tree.iter():
        tag = el.tag.rsplit("}", 1)[-1]
        if tag in {"text","tspan","title","desc"} and el.text:
            original = el.text.strip()
            translated = local_string(original,catalog,missing)
            if translated != original:
                el.text = translate_part(el.text,catalog,missing)
                if tag in {"text","tspan"}:
                    # Retain the same geometry while ensuring glyph availability.
                    family=el.attrib.get("font-family","")
                    if "Noto Sans KR" not in family:
                        el.set("font-family","Inter, Noto Sans KR, Arial, sans-serif")
                    # Compact translated labels where needed; do not alter coordinates.
                    size=el.get("font-size")
                    if size:
                        try:
                            width_en = sum((1.0 if ord(c)>127 else .57) for c in original)
                            width_ko = sum((1.0 if ord(c)>127 else .57) for c in translated)
                            ratio = width_en/max(width_ko,0.01)
                            if ratio < .86:
                                el.set("font-size",str(round(max(float(size)*.74,float(size)*ratio),1)))
                        except ValueError:pass
        for attr in ("aria-label",):
            if attr in el.attrib:
                el.set(attr,local_string(el.attrib[attr],catalog,missing))
    if missing:
        return
    output.parent.mkdir(parents=True,exist_ok=True)
    tree.write(output, encoding="unicode", xml_declaration=True)
    ET.parse(output)

def html_pages(dist:Path)->list[Path]:
    return [p for p in sorted(dist.rglob("index.html"))
            if not any(part in {"kr","ko"} for part in p.relative_to(dist).parts)
            and "404" not in p.relative_to(dist).parts
            and not p.relative_to(dist).as_posix().startswith("projects/kdt-")]

def source_path_to_url(page:Path,dist:Path)->str:
    rel=page.relative_to(dist)
    if rel.as_posix()=="index.html":return "/"
    return "/"+rel.parent.as_posix()+"/"

def href_to_ko(value:str, possible:set[str], svg_map:dict[str,str])->str:
    if value in svg_map:return svg_map[value]
    # Raw GitHub source SVG: map only known references, never fetch arbitrary URLs.
    if value.startswith(RAW_PREFIX):
        path=value.split("?")[0].split("#")[0]
        if path in svg_map:return svg_map[path]
    parts=urlsplit(value)
    if parts.scheme and parts.netloc not in INTERNAL_HOSTS:return value
    if not parts.path.startswith("/") and parts.path!="":return value
    path=parts.path or "/"
    if path.endswith(".svg") and path in svg_map:
        path=svg_map[path]
    elif path in possible:
        path=path.rstrip("/")+"/kr/" if path!="/" else "/kr/"
    elif path.rstrip("/")+"/" in possible:
        path=path.rstrip("/")+"/kr/"
    else:return value
    if parts.netloc: return urlunsplit((parts.scheme,parts.netloc,path,parts.query,parts.fragment))
    return urlunsplit(("", "", path,parts.query,parts.fragment))

class KoHTML(HTMLParser):
    def __init__(self,source_url:str,possible:set[str],svg_map:dict[str,str],
                 catalog:dict[str,str],missing:set[str],mode:str):
        super().__init__(convert_charrefs=True)
        self.url=source_url
        self.possible=possible
        self.svg_map=svg_map
        self.catalog=catalog
        self.missing=missing
        self.mode=mode
        self.stack=[]
        self.output=[]
        self.skip_article=source_url.startswith("/notes/") and source_url!="/notes/"
        self.prose_depth=0
        self.doc_mode=False
    def eligible(self)->bool:
        if any(tag in self.stack for tag in HTML_SKIP):return False
        if self.skip_article and self.prose_depth and len(self.stack)>=self.prose_depth:
            return False  # Only the already-Korean note body is left untouched.
        return True
    def repl_attr(self,tag:str,raw:str)->str:
        if tag=="html":raw=re.sub(r'(?i)\blang=["\x27]en["\x27]', 'lang="ko"',raw,count=1)
        if tag in {"a","img"}:
            def url_repl(m):
                new=href_to_ko(unescape(m.group("val")),self.possible,self.svg_map)
                return m.group("pre")+escape(new,quote=True)+m.group("quote")
            raw=re.sub(r'(?P<pre>\b(?:href|src)\s*=\s*(?P<quote>["\x27]))(?P<val>.*?)(?P=quote)',url_repl,raw,flags=re.I)
        if tag in {"img","a","meta"} and self.eligible():
            def other_repl(m):
                k=m.group("key").lower()
                if tag=="meta" and k=="content":
                    low=raw.lower()
                    if not any(x in low for x in ('name="description"',"name='description'","property=\"og:description\"","property=\"og:title\"")):
                        return m.group(0)
                source=unescape(m.group("val"))
                target=local_string(source,self.catalog,self.missing)
                return m.group("pre")+escape(target,quote=True)+m.group("quote")
            raw=re.sub(r'(?P<pre>\b(?P<key>alt|aria-label|title|content)\s*=\s*(?P<quote>["\x27]))(?P<val>.*?)(?P=quote)',other_repl,raw,flags=re.I)
        return raw
    def handle_starttag(self,tag,attrs):
        raw=self.get_starttag_text()
        self.output.append(self.repl_attr(tag,raw))
        if tag=="head":
            self.output.append('<meta name="robots" content="noindex,nofollow" />')
        if tag not in VOID:
            self.stack.append(tag)
            if self.skip_article and tag=="div" and not self.prose_depth:
                if any(k=="class" and "prose-platform" in (v or "").split() for k,v in attrs):
                    self.prose_depth=len(self.stack)
    def handle_startendtag(self,tag,attrs):
        self.output.append(self.repl_attr(tag,self.get_starttag_text()))
    def handle_endtag(self,tag):
        self.output.append("</"+tag+">")
        if tag in self.stack:self.stack=self.stack[:len(self.stack)-1-self.stack[::-1].index(tag)]
        if self.prose_depth and len(self.stack)<self.prose_depth:self.prose_depth=0
    def handle_data(self,data):
        # Decode HTML entities together with adjacent prose so "Didn't" (whose
        # apostrophe Astro may emit as &#39;) translates as a whole sentence.
        # Re-escape textual content, but never escape JavaScript/CSS source.
        if "script" in self.stack or "style" in self.stack:
            self.output.append(data)
            return
        translated=translate_part(data,self.catalog,self.missing) if self.eligible() else data
        self.output.append(escape(translated,quote=False))
    def handle_entityref(self,name):self.output.append("&"+name+";")
    def handle_charref(self,name):self.output.append("&#"+name+";")
    def handle_comment(self,data):self.output.append("<!--"+data+"-->")
    def handle_decl(self,decl):self.output.append("<!"+decl+">")
    def handle_pi(self,data):self.output.append("<?"+data+">")
    def unknown_decl(self,data):self.output.append("<!["+data+"]>")

def load_catalog()->dict[str,str]:
    if not CATALOG.exists():return {}
    return json.loads(CATALOG.read_text(encoding="utf-8"))

def catalog_scan(dist:Path,catalog:dict[str,str])->tuple[set[str],list[Path],dict[str,Path],set[str]]:
    sources=html_pages(dist)
    possible={source_path_to_url(p,dist) for p in sources}
    svg=svg_inputs(dist)
    svg_map={key:ko_svg_path(key) for key in svg}
    missing:set[str]=set()
    for page in sources:
        original=page.read_text(encoding='utf-8')
        processor=KoHTML(source_path_to_url(page,dist),possible,svg_map,catalog,missing,"scan")
        processor.feed(original)
        processor.close()
    for image in svg.values():
        for s in iter_svg_strings(image):
            local_string(s,catalog,missing)
    return missing,sources,svg,possible

def run_ko(dist:Path,catalog:dict[str,str],missing:set[str],
           sources:list[Path],svg:dict[str,Path],possible:set[str]):
    svg_map={key:ko_svg_path(key) for key in svg}
    for src,source in svg.items():
        dest=dist/svg_map[src].lstrip("/")
        create_svg_ko(source,dest,catalog,missing)
    if missing:raise RuntimeError(f"Missing SVG translations: {len(missing)}")
    for page in sources:
        url=source_path_to_url(page,dist)
        target=dist/("kr/index.html" if url=="/" else url.strip("/")+"/kr/index.html")
        processor=KoHTML(url,possible,svg_map,catalog,missing,"build")
        processor.feed(page.read_text(encoding="utf-8"))
        processor.close()
        if missing:raise RuntimeError(f"Missing translations on {url}: {len(missing)}")
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text("".join(processor.output),encoding="utf-8")
    print(f"Generated {len(sources)} opt-in /kr/ pages and {len(svg)} translated SVGs.")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode",choices=["collect","translate","build"])
    ap.add_argument("--dist",type=Path,default=DIST)
    ap.add_argument("--limit",type=int,default=0,help="translate at most N new strings in this pass")
    args=ap.parse_args()
    catalog=load_catalog()
    # Human-edited exact-string overrides take precedence over offline MT.
    catalog.update(OVERRIDES)
    if OVERRIDE_FILE.exists():
        catalog.update(json.loads(OVERRIDE_FILE.read_text(encoding="utf-8")))
    start=time.monotonic()
    missing,sources,svg,possible=catalog_scan(args.dist,catalog)
    print(f"Found {len(sources)} HTML pages and {len(svg)} SVGs; {len(missing)} uncatalogued English strings.")
    if args.mode=="collect":
        report=WEB/"i18n"/"missing-ko.json"
        report.parent.mkdir(parents=True,exist_ok=True)
        report.write_text(json.dumps(sorted(missing),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("Missing-string report",report)
        return 0
    if args.mode=="translate":
        import argostranslate.translate
        pending=sorted(missing,key=lambda x:(len(x),x))
        if args.limit:pending=pending[:args.limit]
        count=0
        for source in pending:
            translated=argostranslate.translate.translate(source,"en","ko").strip()
            if not translated:
                print("Empty translation",repr(source[:140]),file=sys.stderr)
                return 2
            if translated==source and len(source)>35 and not all(
                token in TECH_WORDS or token in {"·","/","&","+"}
                for token in source.split()
            ):
                print("WARN: source remained English:",repr(source[:140]),file=sys.stderr)
            catalog[source]=translated
            count+=1
            if count%100==0:
                CATALOG.parent.mkdir(parents=True,exist_ok=True)
                CATALOG.write_text(json.dumps(catalog,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
                print(f"translated {count}/{len(pending)} in {round(time.monotonic()-start,1)}s",flush=True)
        CATALOG.parent.mkdir(parents=True,exist_ok=True)
        CATALOG.write_text(json.dumps(catalog,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print(f"Catalog now has {len(catalog)} strings; translated {count} new entries in {round(time.monotonic()-start,1)}s.")
        if args.limit:return 0
        missing,sources,svg,possible=catalog_scan(args.dist,catalog)
    if missing:
        for item in sorted(missing)[:10]:print("MISSING:",repr(item[:160]),file=sys.stderr)
        print(f"{len(missing)} untranslated strings. Run local translation sync and commit the reviewed catalog.",file=sys.stderr)
        return 1
    run_ko(args.dist,catalog,missing,sources,svg,possible)
    print(f"Completed in {round(time.monotonic()-start,1)}s.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
