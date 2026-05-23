"""Text slot detection."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from pptx_json.package.opc import parse_xml
from pptx_json.xmlns import NS


SLOT_RE = re.compile(r"\{\{\s*([A-Za-z][A-Za-z0-9_-]*)\s*\}\}")


def _shape_id(shape) -> str:
    c_nv_pr = shape.find("p:nvSpPr/p:cNvPr", NS)
    return c_nv_pr.attrib.get("id", "") if c_nv_pr is not None else ""


def _shape_name(shape) -> str:
    c_nv_pr = shape.find("p:nvSpPr/p:cNvPr", NS)
    return c_nv_pr.attrib.get("name", "") if c_nv_pr is not None else ""


def _placeholder_type(shape) -> str:
    ph = shape.find("p:nvSpPr/p:nvPr/p:ph", NS)
    return ph.attrib.get("type", "") if ph is not None else ""


def _text(shape) -> str:
    return "".join(t.text or "" for t in shape.findall(".//a:t", NS))


def _run_summary(run) -> dict[str, Any]:
    r_pr = run.find("a:rPr", NS)
    color = None
    if r_pr is not None:
        srgb = r_pr.find(".//a:srgbClr", NS)
        if srgb is not None:
            color = srgb.attrib.get("val")
    return {
        "text": "".join(t.text or "" for t in run.findall("a:t", NS)),
        "bold": r_pr is not None and r_pr.attrib.get("b") == "1",
        "italic": r_pr is not None and r_pr.attrib.get("i") == "1",
        "color": color,
    }


def _shape_box(shape) -> dict[str, int] | None:
    xfrm = shape.find("p:spPr/a:xfrm", NS)
    if xfrm is None:
        return None
    off = xfrm.find("a:off", NS)
    ext = xfrm.find("a:ext", NS)
    if off is None or ext is None:
        return None
    return {
        "x": int(off.attrib.get("x", "0")),
        "y": int(off.attrib.get("y", "0")),
        "cx": int(ext.attrib.get("cx", "0")),
        "cy": int(ext.attrib.get("cy", "0")),
    }


def _font_size(shape) -> int | None:
    for props in shape.findall(".//a:rPr", NS) + shape.findall(".//a:endParaRPr", NS):
        if props.attrib.get("sz"):
            return int(props.attrib["sz"])
    return None


def _paragraphs(shape) -> list[dict[str, Any]]:
    tx_body = shape.find("p:txBody", NS)
    if tx_body is None:
        return []
    result = []
    for paragraph in tx_body.findall("a:p", NS):
        p_pr = paragraph.find("a:pPr", NS)
        bullet = False
        if p_pr is not None:
            bullet = any(child.tag.rsplit("}", 1)[-1].startswith("bu") for child in list(p_pr))
        runs = [_run_summary(run) for run in paragraph.findall("a:r", NS)]
        result.append({
            "text": "".join(run.get("text", "") for run in runs),
            "bullet": bullet,
            "runs": runs,
        })
    return result


def _paragraph_count(shape) -> int:
    return max(1, len(shape.findall(".//a:p", NS)))


def _capacity(text: str, shape) -> dict[str, Any]:
    base = max(40, len(text.replace("{{", "").replace("}}", "")) * 2)
    capacity: dict[str, Any] = {"max_chars": min(max(base, 80), 500), "max_lines": _paragraph_count(shape)}
    box = _shape_box(shape)
    if box:
        capacity["box"] = box
    return capacity


def _unique(slot_id: str, seen: set[str], slide_index: int) -> str:
    cleaned = slot_id.replace("-", "_")
    if cleaned not in seen:
        seen.add(cleaned)
        return cleaned
    candidate = f"slide{slide_index:03d}_{cleaned}"
    i = 2
    while candidate in seen:
        candidate = f"slide{slide_index:03d}_{cleaned}_{i}"
        i += 1
    seen.add(candidate)
    return candidate


def detect_text_slots(package_dir: Path, slide: dict[str, Any]) -> list[dict[str, Any]]:
    slide_part = slide["source_part"]
    tree = parse_xml(package_dir / slide_part)
    slots: list[dict[str, Any]] = []
    seen: set[str] = set()
    for shape in tree.findall(".//p:sp", NS):
        tx_body = shape.find("p:txBody", NS)
        if tx_body is None:
            continue
        shape_text = _text(shape)
        if not shape_text.strip():
            continue
        shape_id = _shape_id(shape)
        name = _shape_name(shape)
        ph_type = _placeholder_type(shape)
        matches = SLOT_RE.findall(shape_text)
        slot_ids: list[tuple[str, bool, str]] = []
        if matches:
            slot_ids.extend((match, True, "placeholder") for match in matches)
        elif ph_type in {"title", "ctrTitle"} or "title" in name.lower():
            slot_ids.append(("title", True, "heuristic"))
        elif ph_type in {"subTitle"} or "subtitle" in name.lower():
            slot_ids.append(("subtitle", True, "heuristic"))
        elif ph_type in {"body"}:
            slot_ids.append(("body", True, "heuristic"))
        else:
            slot_ids.append((f"text_{shape_id or len(slots) + 1}", False, "text-shape"))
        for raw_slot_id, required, kind in slot_ids:
            slot_id = _unique(raw_slot_id, seen, slide["index"])
            slots.append({
                "slot_id": slot_id,
                "type": "text",
                "required": required,
                "editable_fields": ["content", "paragraphs"],
                "capacity": _capacity(shape_text, shape),
                "binding": {
                    "part": slide_part,
                    "shape_id": shape_id,
                    "xpath": f".//p:sp[p:nvSpPr/p:cNvPr/@id='{shape_id}']/p:txBody",
                },
                "source": {
                    "kind": kind,
                    "shape_name": name,
                    "placeholder_type": ph_type,
                    "current_text": shape_text,
                    "font_size": _font_size(shape),
                    "paragraphs": _paragraphs(shape),
                },
            })
    return slots
