"""Shape and simple vector slot detection."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from pptx_json.package.opc import parse_xml
from pptx_json.xmlns import NS


SLOT_RE = re.compile(r"\{\{\s*([A-Za-z][A-Za-z0-9_-]*)\s*\}\}")


def _shape_meta(shape) -> tuple[str, str, str]:
    c_nv_pr = shape.find("p:nvSpPr/p:cNvPr", NS)
    if c_nv_pr is None:
        return "", "", ""
    return (
        c_nv_pr.attrib.get("id", ""),
        c_nv_pr.attrib.get("name", ""),
        c_nv_pr.attrib.get("descr", ""),
    )


def _srgb(parent, path: str) -> str | None:
    node = parent.find(path, NS)
    return node.attrib.get("val") if node is not None else None


def detect_shape_slots(package_dir: Path, slide: dict[str, Any]) -> list[dict[str, Any]]:
    slide_part = slide["source_part"]
    tree = parse_xml(package_dir / slide_part)
    slots: list[dict[str, Any]] = []
    for shape in tree.findall(".//p:sp", NS):
        shape_id, name, descr = _shape_meta(shape)
        marker = " ".join([name, descr])
        match = SLOT_RE.search(marker)
        if not match:
            continue
        sp_pr = shape.find("p:spPr", NS)
        if sp_pr is None:
            continue
        geometry = sp_pr.find("a:prstGeom", NS)
        slot_id = match.group(1).replace("-", "_")
        slots.append({
            "slot_id": slot_id,
            "type": "shape",
            "required": False,
            "editable_fields": ["fill", "line", "opacity", "geometry"],
            "capacity": {"kind": "simple-shape"},
            "binding": {
                "part": slide_part,
                "shape_id": shape_id,
            },
            "source": {
                "kind": "shape",
                "shape_name": name,
                "description": descr,
                "fill": _srgb(sp_pr, "a:solidFill/a:srgbClr"),
                "line": _srgb(sp_pr, "a:ln/a:solidFill/a:srgbClr"),
                "geometry": geometry.attrib.get("prst") if geometry is not None else None,
            },
        })
    return slots
