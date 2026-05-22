"""Apply shape style replacement patches."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from pptx_json.errors import BINDING_STALE, EngineError
from pptx_json.package.opc import write_xml
from pptx_json.xmlns import NS, qn


def _clean_color(value: str) -> str:
    return str(value).strip().lstrip("#").upper()


def _shape_by_id(root, shape_id: str):
    for shape in root.findall(".//p:sp", NS):
        c_nv_pr = shape.find("p:nvSpPr/p:cNvPr", NS)
        if c_nv_pr is not None and c_nv_pr.attrib.get("id") == shape_id:
            return shape
    return None


def _ensure(parent, path: list[tuple[str, dict | None]]):
    node = parent
    for tag, attrib in path:
        child = node.find(tag, NS)
        if child is None:
            child = ET.SubElement(node, qn(*tag.split(":", 1)), attrib or {})
        node = child
    return node


def _set_fill(sp_pr, color: str, opacity=None) -> None:
    srgb = _ensure(sp_pr, [("a:solidFill", None), ("a:srgbClr", None)])
    srgb.attrib["val"] = _clean_color(color)
    if opacity is not None:
        alpha = srgb.find("a:alpha", NS)
        if alpha is None:
            alpha = ET.SubElement(srgb, qn("a", "alpha"))
        alpha.attrib["val"] = str(max(0, min(100000, int(float(opacity) * 100000))))


def _set_line(sp_pr, color: str) -> None:
    srgb = _ensure(sp_pr, [("a:ln", None), ("a:solidFill", None), ("a:srgbClr", None)])
    srgb.attrib["val"] = _clean_color(color)


def apply_shape_patch(package_dir: Path, operation: dict) -> None:
    slide_path = package_dir / operation["target_slide"]
    tree = ET.parse(slide_path)
    root = tree.getroot()
    shape_id = str(operation.get("binding", {}).get("shape_id") or "")
    shape = _shape_by_id(root, shape_id)
    if shape is None:
        raise EngineError(BINDING_STALE, "Shape binding no longer exists.", shape_id=shape_id)
    sp_pr = shape.find("p:spPr", NS)
    if sp_pr is None:
        sp_pr = ET.SubElement(shape, qn("p", "spPr"))
    if "fill" in operation:
        _set_fill(sp_pr, operation["fill"], operation.get("opacity"))
    elif "opacity" in operation:
        fill = sp_pr.find("a:solidFill/a:srgbClr", NS)
        if fill is not None:
            alpha = fill.find("a:alpha", NS)
            if alpha is None:
                alpha = ET.SubElement(fill, qn("a", "alpha"))
            alpha.attrib["val"] = str(max(0, min(100000, int(float(operation["opacity"]) * 100000))))
    if "line" in operation:
        _set_line(sp_pr, operation["line"])
    if "geometry" in operation:
        geometry = sp_pr.find("a:prstGeom", NS)
        if geometry is None:
            geometry = ET.SubElement(sp_pr, qn("a", "prstGeom"))
            ET.SubElement(geometry, qn("a", "avLst"))
        geometry.attrib["prst"] = str(operation["geometry"])
    write_xml(slide_path, tree)
