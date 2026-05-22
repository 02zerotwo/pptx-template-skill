"""Slide discovery for PPTX templates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pptx_json.package.opc import parse_xml
from pptx_json.package.rels import load_relationships, resolve_target
from pptx_json.xmlns import NS


def iter_slides(package_dir: Path) -> list[dict[str, Any]]:
    """Return slides in presentation order."""
    presentation = package_dir / "ppt" / "presentation.xml"
    rels_file = package_dir / "ppt" / "_rels" / "presentation.xml.rels"
    tree = parse_xml(presentation)
    rels = {rel["Id"]: rel for rel in load_relationships(rels_file)}
    slides: list[dict[str, Any]] = []
    sld_ids = tree.getroot().find("p:sldIdLst", NS)
    if sld_ids is None:
        return slides
    total = len(list(sld_ids))
    for index, sld_id in enumerate(sld_ids, start=1):
        rel_id = sld_id.attrib.get(f"{{{NS['r']}}}id", "")
        rel = rels.get(rel_id)
        if not rel:
            continue
        source_part = resolve_target("ppt/presentation.xml", rel["Target"])
        if index == 1:
            role = "cover"
        elif index == total:
            role = "closing"
        else:
            role = "content"
        slides.append({
            "slide_id": f"template-slide-{index:03d}",
            "index": index,
            "source_part": source_part,
            "presentation_rel_id": rel_id,
            "presentation_slide_id": sld_id.attrib.get("id", str(255 + index)),
            "role": role,
        })
    return slides
