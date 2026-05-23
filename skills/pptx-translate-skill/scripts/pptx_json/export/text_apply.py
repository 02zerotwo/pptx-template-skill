"""Apply text replacement patches."""

from __future__ import annotations

import copy
from pathlib import Path
from xml.etree import ElementTree as ET
from typing import Any

from pptx_json.errors import BINDING_STALE, EngineError
from pptx_json.package.opc import write_xml
from pptx_json.xmlns import NS, qn


def apply_text_patch(package_dir: Path, operation: dict) -> None:
    slide_path = package_dir / operation["target_slide"]
    tree = ET.parse(slide_path)
    shape_id = str(operation.get("binding", {}).get("shape_id") or "")
    shape = None
    for candidate in tree.findall(".//p:sp", NS):
        c_nv_pr = candidate.find("p:nvSpPr/p:cNvPr", NS)
        if c_nv_pr is not None and c_nv_pr.attrib.get("id") == shape_id:
            shape = candidate
            break
    if shape is None:
        raise EngineError(BINDING_STALE, "Text binding shape no longer exists.", shape_id=shape_id)
    tx_body = shape.find("p:txBody", NS)
    if tx_body is None:
        tx_body = ET.SubElement(shape, qn("p", "txBody"))
        ET.SubElement(tx_body, qn("a", "bodyPr"))
        ET.SubElement(tx_body, qn("a", "lstStyle"))
    _apply_autofit(tx_body, operation)
    if "paragraphs" in operation:
        _apply_paragraphs(tx_body, operation.get("paragraphs", []))
        write_xml(slide_path, tree)
        return
    texts = tx_body.findall(".//a:t", NS)
    if not texts:
        paragraph = tx_body.find("a:p", NS)
        if paragraph is None:
            paragraph = ET.SubElement(tx_body, qn("a", "p"))
        run = paragraph.find("a:r", NS)
        if run is None:
            run = ET.SubElement(paragraph, qn("a", "r"))
        texts = [ET.SubElement(run, qn("a", "t"))]
    texts[0].text = str(operation.get("content", ""))
    for extra in texts[1:]:
        extra.text = ""
    write_xml(slide_path, tree)


def _apply_autofit(tx_body, operation: dict) -> None:
    autofit = operation.get("autofit", {})
    if not autofit.get("enabled"):
        return
    body_pr = tx_body.find("a:bodyPr", NS)
    if body_pr is None:
        body_pr = ET.Element(qn("a", "bodyPr"))
        tx_body.insert(0, body_pr)
    for child in list(body_pr):
        if _local_name(child.tag) in {"noAutofit", "normAutofit", "spAutoFit"}:
            body_pr.remove(child)
    font_scale = str(int(autofit.get("font_scale") or 100000))
    ET.SubElement(body_pr, qn("a", "normAutofit"), {"fontScale": font_scale})


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _paragraph_runs(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, str):
        return [{"text": value}]
    if not isinstance(value, dict):
        return [{"text": str(value)}]
    if isinstance(value.get("runs"), list):
        return [run for run in value.get("runs", []) if isinstance(run, dict)]
    return [{"text": str(value.get("text", ""))}]


def _ensure_paragraph_props(paragraph) -> ET.Element:
    p_pr = paragraph.find("a:pPr", NS)
    if p_pr is None:
        p_pr = ET.Element(qn("a", "pPr"))
        paragraph.insert(0, p_pr)
    return p_pr


def _apply_bullet(paragraph, descriptor: Any) -> None:
    if not isinstance(descriptor, dict) or "bullet" not in descriptor:
        return
    p_pr = _ensure_paragraph_props(paragraph)
    for child in list(p_pr):
        if _local_name(child.tag).startswith("bu"):
            p_pr.remove(child)
    if descriptor.get("bullet"):
        ET.SubElement(p_pr, qn("a", "buChar"), {"char": "•"})


def _run_props(template_run, run_value: dict[str, Any]):
    template = template_run.find("a:rPr", NS) if template_run is not None else None
    r_pr = copy.deepcopy(template) if template is not None else ET.Element(qn("a", "rPr"))
    if "bold" in run_value:
        r_pr.attrib["b"] = "1" if run_value.get("bold") else "0"
    if "italic" in run_value:
        r_pr.attrib["i"] = "1" if run_value.get("italic") else "0"
    return r_pr


def _set_paragraph_text(paragraph, descriptor: Any) -> None:
    template_run = paragraph.find("a:r", NS)
    for child in list(paragraph):
        if _local_name(child.tag) in {"r", "br", "fld"}:
            paragraph.remove(child)
    for run_value in _paragraph_runs(descriptor):
        run = ET.SubElement(paragraph, qn("a", "r"))
        run.append(_run_props(template_run, run_value))
        text = ET.SubElement(run, qn("a", "t"))
        text.text = str(run_value.get("text", ""))


def _apply_paragraphs(tx_body, paragraphs: list[Any]) -> None:
    existing = tx_body.findall("a:p", NS)
    templates = existing or [ET.Element(qn("a", "p"))]
    for paragraph in existing:
        tx_body.remove(paragraph)
    for index, descriptor in enumerate(paragraphs):
        template = templates[min(index, len(templates) - 1)]
        paragraph = copy.deepcopy(template)
        _apply_bullet(paragraph, descriptor)
        _set_paragraph_text(paragraph, descriptor)
        tx_body.append(paragraph)
