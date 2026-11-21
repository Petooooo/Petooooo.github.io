#!/usr/bin/env python3
"""Refuse raster-in-SVG source figures that pretend to have more pixels than recorded."""
from __future__ import annotations

import base64
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
FIGURES = ROOT / "apps/web/public/figures"
CSS = ROOT / "apps/web/src/styles/global.css"
SVG_NS = "{http://www.w3.org/2000/svg}"
XLINK = "{http://www.w3.org/1999/xlink}"


def image_size(raw: bytes, media: str) -> tuple[int, int]:
    if media == "image/png":
        if raw[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError("invalid PNG signature")
        return int.from_bytes(raw[16:20], "big"), int.from_bytes(raw[20:24], "big")
    if media not in ("image/jpeg", "image/jpg") or raw[:2] != b"\xff\xd8":
        raise ValueError(f"unsupported or invalid embedded image: {media}")
    index = 2
    sof_markers = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    while index < len(raw) - 9:
        if raw[index] != 0xFF:
            index += 1
            continue
        while index < len(raw) and raw[index] == 0xFF:
            index += 1
        if index >= len(raw):
            break
        marker = raw[index]
        index += 1
        if marker == 0xD9 or marker == 0xDA:
            break
        if marker == 0xD8 or 0xD0 <= marker <= 0xD7 or marker == 0x01:
            continue
        if index + 2 > len(raw):
            break
        length = int.from_bytes(raw[index:index + 2], "big")
        if length < 2 or index + length > len(raw):
            break
        if marker in sof_markers:
            return (int.from_bytes(raw[index + 5:index + 7], "big"),
                    int.from_bytes(raw[index + 3:index + 5], "big"))
        index += length
    raise ValueError("JPEG dimensions unavailable")


def dimensions(attrs: dict[str, str], keys: tuple[str, str]) -> tuple[int, int]:
    width, height = (float(attrs[k]) for k in keys)
    if width <= 0 or height <= 0 or not width.is_integer() or not height.is_integer():
        raise ValueError(f"invalid dimensions: {width} x {height}")
    return int(width), int(height)


def validate(path: Path) -> None:
    root = ET.parse(path).getroot()
    children = root.findall(f"{SVG_NS}image")
    if len(children) != 1:
        raise ValueError(f"expected one embedded source screenshot, found {len(children)}")
    img = children[0]
    href = img.get("href") or img.get(f"{XLINK}href") or ""
    if not href.startswith("data:") or ";base64," not in href:
        raise ValueError("source image must be embedded, not external")
    media = href[5:].split(";", 1)[0]
    raw = base64.b64decode(href.split(",", 1)[1], validate=True)
    native = image_size(raw, media)
    actual_svg = dimensions(root.attrib, ("width", "height"))
    actual_img = dimensions(img.attrib, ("width", "height"))
    view_box = [float(n) for n in root.attrib.get("viewBox", "").split()]
    if len(view_box) != 4 or view_box[:2] != [0.0, 0.0]:
        raise ValueError("invalid or shifted viewBox")
    if actual_svg != native or actual_img != native or view_box[2:] != list(native):
        raise ValueError(
            f"raster {native} does not match SVG {actual_svg}, image {actual_img}, viewBox {view_box}"
        )
    if img.get("transform") or root.get("transform"):
        raise ValueError("source bitmap transform may silently upscale or distort the figure")


def main() -> int:
    files = sorted(FIGURES.rglob("*-source-figure-*.svg"))
    errors = []
    for file in files:
        try:
            validate(file)
        except (ValueError, ET.ParseError, KeyError) as exc:
            errors.append(f"{file.relative_to(ROOT)}: {exc}")
    css = CSS.read_text()
    if ".project-concept-figure.project-source-figure img {" not in css or "width: auto;" not in css:
        errors.append("source figure CSS must retain intrinsic raster width")
    if errors:
        print("Source figure resolution check FAILED:")
        print("\n".join(errors))
        return 1
    print(f"Source figure resolution check: {len(files)} original-sized embedded SVGs OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
