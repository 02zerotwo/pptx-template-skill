"""Apply table cell replacement patches."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from pptx_json.errors import BINDING_STALE, EngineError
from pptx_json.package.opc import write_xml
from pptx_json.xmlns import NS, qn


def _frame_by_id(root, shape_id: str):
    for frame in root.findall(".//p:graphicFrame", NS):
        c_nv_pr = frame.find("p:nvGraphicFramePr/p:cNvPr", NS)
        if c_nv_pr is not None and c_nv_pr.attrib.get("id") == shape_id:
            return frame
    return None


def _set_cell_text(cell, text: str) -> None:
    texts = cell.findall(".//a:t", NS)
    if not texts:
        tx_body = cell.find("a:txBody", NS)
        if tx_body is None:
            tx_body = ET.SubElement(cell, qn("a", "txBody"))
        paragraph = tx_body.find("a:p", NS)
        if paragraph is None:
            paragraph = ET.SubElement(tx_body, qn("a", "p"))
        run = paragraph.find("a:r", NS)
        if run is None:
            run = ET.SubElement(paragraph, qn("a", "r"))
        texts = [ET.SubElement(run, qn("a", "t"))]
    texts[0].text = str(text)
    for extra in texts[1:]:
        extra.text = ""


def apply_table_patch(package_dir: Path, operation: dict) -> None:
    slide_path = package_dir / operation["target_slide"]
    tree = ET.parse(slide_path)
    root = tree.getroot()
    shape_id = str(operation.get("binding", {}).get("shape_id") or "")
    frame = _frame_by_id(root, shape_id)
    if frame is None:
        raise EngineError(BINDING_STALE, "Table binding shape no longer exists.", shape_id=shape_id)
    rows = frame.findall(".//a:tbl/a:tr", NS)
    for row_index, row_values in enumerate(operation.get("cells", [])):
        if row_index >= len(rows):
            break
        cells = rows[row_index].findall("a:tc", NS)
        for col_index, value in enumerate(row_values):
            if col_index >= len(cells):
                break
            _set_cell_text(cells[col_index], str(value))
    write_xml(slide_path, tree)
