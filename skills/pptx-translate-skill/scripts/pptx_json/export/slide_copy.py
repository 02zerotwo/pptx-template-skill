"""Slide copy and presentation relationship updates."""

from __future__ import annotations

from pathlib import Path
import re
from xml.etree import ElementTree as ET

from pptx_json.package.content_types import SLIDE_CONTENT_TYPE, add_override
from pptx_json.package.paths import rels_path_for_part
from pptx_json.package.rels import load_relationships, resolve_target, save_relationships, target_from_part
from pptx_json.xmlns import NS, REL_TYPES, qn

CHART_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.drawingml.chart+xml"


def apply_slide_copies(package_dir: Path, operations: list[dict]) -> None:
    copy_ops = [op for op in operations if op.get("type") == "copy_slide"]
    if not copy_ops:
        return

    slide_bytes: dict[str, bytes] = {}
    rel_bytes: dict[str, bytes | None] = {}
    for op in copy_ops:
        source_slide = op["source_slide"]
        slide_bytes[source_slide] = (package_dir / source_slide).read_bytes()
        source_rels = package_dir / rels_path_for_part(source_slide)
        rel_bytes[source_slide] = source_rels.read_bytes() if source_rels.exists() else None

    content_types_path = package_dir / "[Content_Types].xml"
    for op in copy_ops:
        target_slide = op["target_slide"]
        source_slide = op["source_slide"]
        target_path = package_dir / target_slide
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(slide_bytes[source_slide])
        target_rels = package_dir / rels_path_for_part(target_slide)
        if rel_bytes[source_slide] is not None:
            target_rels.parent.mkdir(parents=True, exist_ok=True)
            target_rels.write_bytes(rel_bytes[source_slide] or b"")
            if target_slide != source_slide:
                _clone_related_chart_parts(package_dir, target_slide, target_rels)
        add_override(content_types_path, target_slide, SLIDE_CONTENT_TYPE)

    _update_presentation_xml(package_dir, copy_ops)
    _update_presentation_rels(package_dir, copy_ops)


def _update_presentation_xml(package_dir: Path, copy_ops: list[dict]) -> None:
    path = package_dir / "ppt" / "presentation.xml"
    tree = ET.parse(path)
    root = tree.getroot()
    sld_id_lst = root.find("p:sldIdLst", NS)
    if sld_id_lst is None:
        sld_id_lst = ET.SubElement(root, qn("p", "sldIdLst"))
    for child in list(sld_id_lst):
        sld_id_lst.remove(child)
    for op in copy_ops:
        attrib = {
            "id": str(op["new_slide_id"]),
            qn("r", "id"): op["presentation_rel_id"],
        }
        ET.SubElement(sld_id_lst, qn("p", "sldId"), attrib)
    ET.register_namespace("p", NS["p"])
    ET.register_namespace("r", NS["r"])
    tree.write(path, encoding="utf-8", xml_declaration=True)


def _update_presentation_rels(package_dir: Path, copy_ops: list[dict]) -> None:
    path = package_dir / "ppt" / "_rels" / "presentation.xml.rels"
    rels = [
        rel for rel in load_relationships(path)
        if rel.get("Type") != REL_TYPES["slide"]
    ]
    for op in copy_ops:
        rels.append({
            "Id": op["presentation_rel_id"],
            "Type": REL_TYPES["slide"],
            "Target": target_from_part("ppt/presentation.xml", op["target_slide"]),
            "TargetMode": None,
        })
    save_relationships(path, rels)


def _next_chart_part(package_dir: Path) -> str:
    used: set[int] = set()
    for path in (package_dir / "ppt" / "charts").glob("chart*.xml"):
        match = re.fullmatch(r"chart(\d+)\.xml", path.name)
        if match:
            used.add(int(match.group(1)))
    index = 1
    while index in used:
        index += 1
    return f"ppt/charts/chart{index}.xml"


def _clone_related_chart_parts(package_dir: Path, target_slide: str, target_rels: Path) -> None:
    rels = load_relationships(target_rels)
    changed = False
    for rel in rels:
        if rel.get("Type") != REL_TYPES["chart"]:
            continue
        source_chart = resolve_target(target_slide, str(rel.get("Target") or ""))
        source_path = package_dir / source_chart
        if not source_path.exists():
            continue
        cloned_chart = _next_chart_part(package_dir)
        cloned_path = package_dir / cloned_chart
        cloned_path.parent.mkdir(parents=True, exist_ok=True)
        cloned_path.write_bytes(source_path.read_bytes())
        rel["Target"] = target_from_part(target_slide, cloned_chart)
        add_override(package_dir / "[Content_Types].xml", cloned_chart, CHART_CONTENT_TYPE)
        changed = True
    if changed:
        save_relationships(target_rels, rels)
