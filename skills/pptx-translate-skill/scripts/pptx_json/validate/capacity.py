"""Slot capacity validation."""

from __future__ import annotations

from typing import Any

from pptx_json.errors import CAPACITY_EXCEEDED
from pptx_json.models.reports import Report


def _paragraph_text(value: dict[str, Any]) -> str:
    parts = []
    for paragraph in value.get("paragraphs", []):
        if isinstance(paragraph, str):
            parts.append(paragraph)
        elif isinstance(paragraph, dict) and isinstance(paragraph.get("runs"), list):
            parts.append("".join(str(run.get("text", "")) for run in paragraph.get("runs", [])))
        elif isinstance(paragraph, dict):
            parts.append(str(paragraph.get("text", "")))
    return "\n".join(parts)


def validate_capacity(report: Report, slide_id: str, slot: dict[str, Any], value: dict[str, Any]) -> None:
    slot_type = slot.get("type")
    if slot_type == "table":
        _validate_table_capacity(report, slide_id, slot, value)
        return
    if slot_type == "chart":
        _validate_chart_capacity(report, slide_id, slot, value)
        return
    if slot_type != "text":
        return

    content = _paragraph_text(value) if "paragraphs" in value else str(value.get("content", ""))
    max_chars = slot.get("capacity", {}).get("max_chars")
    if max_chars and len(content) > int(max_chars):
        report.add_warning(
            CAPACITY_EXCEEDED,
            "Text content exceeds the slot capacity; export will enable text autofit.",
            slide=slide_id,
            slot_id=slot.get("slot_id"),
            max_chars=max_chars,
            actual_chars=len(content),
        )


def _validate_table_capacity(report: Report, slide_id: str, slot: dict[str, Any], value: dict[str, Any]) -> None:
    cells = value.get("cells", [])
    if not isinstance(cells, list):
        return
    max_rows = int(slot.get("capacity", {}).get("rows") or 0)
    max_cols = int(slot.get("capacity", {}).get("cols") or 0)
    actual_rows = len(cells)
    actual_cols = max((len(row) for row in cells if isinstance(row, list)), default=0)
    if (max_rows and actual_rows > max_rows) or (max_cols and actual_cols > max_cols):
        report.add_error(
            CAPACITY_EXCEEDED,
            "Table content exceeds the template row or column capacity.",
            slide=slide_id,
            slot_id=slot.get("slot_id"),
            max_rows=max_rows,
            max_cols=max_cols,
            actual_rows=actual_rows,
            actual_cols=actual_cols,
        )


def _validate_chart_capacity(report: Report, slide_id: str, slot: dict[str, Any], value: dict[str, Any]) -> None:
    max_categories = int(slot.get("capacity", {}).get("categories") or 0)
    max_series = int(slot.get("capacity", {}).get("series") or 0)
    categories = value.get("categories", [])
    series = value.get("series", [])
    actual_categories = len(categories) if isinstance(categories, list) else 0
    actual_series = len(series) if isinstance(series, list) else 0
    if (max_categories and actual_categories > max_categories) or (max_series and actual_series > max_series):
        report.add_error(
            CAPACITY_EXCEEDED,
            "Chart content exceeds the template category or series capacity.",
            slide=slide_id,
            slot_id=slot.get("slot_id"),
            max_categories=max_categories,
            max_series=max_series,
            actual_categories=actual_categories,
            actual_series=actual_series,
        )
