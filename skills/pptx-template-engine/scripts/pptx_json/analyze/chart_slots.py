"""Chart slot detection."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from pptx_json.package.opc import parse_xml
from pptx_json.package.paths import rels_path_for_part
from pptx_json.package.rels import load_relationships, resolve_target
from pptx_json.xmlns import NS


SLOT_RE = re.compile(r"\{\{\s*([A-Za-z][A-Za-z0-9_-]*)\s*\}\}")


def _frame_meta(frame) -> tuple[str, str, str]:
    c_nv_pr = frame.find("p:nvGraphicFramePr/p:cNvPr", NS)
    if c_nv_pr is None:
        return "", "", ""
    return (
        c_nv_pr.attrib.get("id", ""),
        c_nv_pr.attrib.get("name", ""),
        c_nv_pr.attrib.get("descr", ""),
    )


def _cache_values(root, path: str) -> list[str]:
    cache = root.find(path, NS)
    if cache is None:
        return []
    return [node.text or "" for node in cache.findall("c:pt/c:v", NS)]


def _chart_source(package_dir: Path, chart_part: str) -> dict[str, Any]:
    root = parse_xml(package_dir / chart_part).getroot()
    first_ser = root.find(".//c:ser", NS)
    categories = _cache_values(first_ser, "c:cat/c:strRef/c:strCache") if first_ser is not None else []
    series = []
    for ser in root.findall(".//c:ser", NS):
        names = _cache_values(ser, "c:tx/c:strRef/c:strCache")
        values = _cache_values(ser, "c:val/c:numRef/c:numCache")
        series.append({"name": names[0] if names else "", "values": values})
    return {"categories": categories, "series": series}


def detect_chart_slots(package_dir: Path, slide: dict[str, Any]) -> list[dict[str, Any]]:
    slide_part = slide["source_part"]
    tree = parse_xml(package_dir / slide_part)
    rels = {
        rel["Id"]: rel
        for rel in load_relationships(package_dir / rels_path_for_part(slide_part))
    }
    slots: list[dict[str, Any]] = []
    for frame in tree.findall(".//p:graphicFrame", NS):
        chart = frame.find(".//c:chart", NS)
        if chart is None:
            continue
        rel_id = chart.attrib.get(f"{{{NS['r']}}}id", "")
        rel = rels.get(rel_id)
        if rel is None:
            continue
        chart_part = resolve_target(slide_part, rel["Target"])
        shape_id, name, descr = _frame_meta(frame)
        marker = " ".join([name, descr])
        match = SLOT_RE.search(marker)
        slot_id = (match.group(1) if match else f"chart_{shape_id or len(slots) + 1}").replace("-", "_")
        source = _chart_source(package_dir, chart_part)
        slots.append({
            "slot_id": slot_id,
            "type": "chart",
            "required": False,
            "editable_fields": ["categories", "series"],
            "capacity": {
                "series": len(source["series"]),
                "categories": len(source["categories"]),
            },
            "binding": {
                "part": slide_part,
                "shape_id": shape_id,
                "rel_id": rel_id,
                "chart_part": chart_part,
            },
            "source": {
                "kind": "chart",
                "shape_name": name,
                "description": descr,
                "categories": source["categories"],
                "series": source["series"],
            },
        })
    return slots
