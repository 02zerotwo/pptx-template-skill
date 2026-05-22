"""Image slot detection."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from pptx_json.package.opc import parse_xml
from pptx_json.package.paths import rels_path_for_part
from pptx_json.package.rels import load_relationships, resolve_target
from pptx_json.xmlns import NS


SLOT_RE = re.compile(r"\{\{\s*([A-Za-z][A-Za-z0-9_-]*)\s*\}\}")


def _pic_meta(pic) -> tuple[str, str, str]:
    c_nv_pr = pic.find("p:nvPicPr/p:cNvPr", NS)
    if c_nv_pr is None:
        return "", "", ""
    return (
        c_nv_pr.attrib.get("id", ""),
        c_nv_pr.attrib.get("name", ""),
        c_nv_pr.attrib.get("descr", ""),
    )


def detect_image_slots(package_dir: Path, slide: dict[str, Any]) -> list[dict[str, Any]]:
    slide_part = slide["source_part"]
    tree = parse_xml(package_dir / slide_part)
    rels_file = package_dir / rels_path_for_part(slide_part)
    rels = {rel["Id"]: rel for rel in load_relationships(rels_file)}
    slots: list[dict[str, Any]] = []
    seen: set[str] = set()
    for pic in tree.findall(".//p:pic", NS):
        shape_id, name, descr = _pic_meta(pic)
        blip = pic.find(".//a:blip", NS)
        if blip is None:
            continue
        rel_id = blip.attrib.get(f"{{{NS['r']}}}embed", "")
        rel = rels.get(rel_id)
        if not rel:
            continue
        marker = " ".join([name, descr])
        match = SLOT_RE.search(marker)
        slot_id = match.group(1) if match else f"image_{shape_id or len(slots) + 1}"
        slot_id = slot_id.replace("-", "_")
        if slot_id in seen:
            slot_id = f"slide{slide['index']:03d}_{slot_id}"
        seen.add(slot_id)
        target_part = resolve_target(slide_part, rel["Target"])
        slots.append({
            "slot_id": slot_id,
            "type": "image",
            "required": False,
            "editable_fields": ["src", "alt"],
            "capacity": {"aspect_ratio": "preserve-template-crop"},
            "binding": {
                "part": slide_part,
                "shape_id": shape_id,
                "rel_id": rel_id,
                "rels_part": rels_path_for_part(slide_part),
            },
            "source": {
                "kind": "placeholder" if match else "existing-picture",
                "shape_name": name,
                "description": descr,
                "target": target_part,
            },
        })
    return slots
