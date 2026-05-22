"""Table slot detection."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from pptx_json.package.opc import parse_xml
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


def _table_cells(table) -> list[list[str]]:
    rows = []
    for row in table.findall("a:tr", NS):
        values = []
        for cell in row.findall("a:tc", NS):
            values.append("".join(node.text or "" for node in cell.findall(".//a:t", NS)))
        rows.append(values)
    return rows


def detect_table_slots(package_dir: Path, slide: dict[str, Any]) -> list[dict[str, Any]]:
    slide_part = slide["source_part"]
    tree = parse_xml(package_dir / slide_part)
    slots: list[dict[str, Any]] = []
    for frame in tree.findall(".//p:graphicFrame", NS):
        table = frame.find(".//a:tbl", NS)
        if table is None:
            continue
        shape_id, name, descr = _frame_meta(frame)
        marker = " ".join([name, descr])
        match = SLOT_RE.search(marker)
        slot_id = (match.group(1) if match else f"table_{shape_id or len(slots) + 1}").replace("-", "_")
        cells = _table_cells(table)
        slots.append({
            "slot_id": slot_id,
            "type": "table",
            "required": False,
            "editable_fields": ["cells"],
            "capacity": {
                "rows": len(cells),
                "cols": max((len(row) for row in cells), default=0),
            },
            "binding": {
                "part": slide_part,
                "shape_id": shape_id,
            },
            "source": {
                "kind": "table",
                "shape_name": name,
                "description": descr,
                "cells": cells,
            },
        })
    return slots
