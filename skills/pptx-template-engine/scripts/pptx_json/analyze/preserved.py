"""Preserved object summaries."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pptx_json.package.opc import parse_xml
from pptx_json.xmlns import NS


def summarize_preserved_objects(package_dir: Path, slide: dict[str, Any]) -> list[dict[str, Any]]:
    slide_part = slide["source_part"]
    tree = parse_xml(package_dir / slide_part)
    root = tree.getroot()
    preserved: list[dict[str, Any]] = []
    if root.find(".//p:timing", NS) is not None:
        preserved.append({"type": "animation", "part": slide_part, "strategy": "preserve"})
    for graphic_data in root.findall(".//a:graphicData", NS):
        uri = graphic_data.attrib.get("uri", "")
        if "diagram" in uri:
            preserved.append({"type": "smart_art", "part": slide_part, "strategy": "preserve"})
        elif "chart" in uri:
            preserved.append({"type": "chart", "part": slide_part, "strategy": "summary-only"})
        elif "table" in uri:
            preserved.append({"type": "table", "part": slide_part, "strategy": "summary-only"})
    for tag_name in ("oleObj", "controls"):
        if root.find(f".//p:{tag_name}", NS) is not None:
            preserved.append({"type": tag_name, "part": slide_part, "strategy": "preserve"})
    return preserved
