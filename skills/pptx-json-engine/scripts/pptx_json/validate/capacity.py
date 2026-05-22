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
    if slot.get("type") != "text":
        return
    content = _paragraph_text(value) if "paragraphs" in value else str(value.get("content", ""))
    max_chars = slot.get("capacity", {}).get("max_chars")
    if max_chars and len(content) > int(max_chars):
        report.add_error(
            CAPACITY_EXCEEDED,
            "Text content exceeds the slot hard capacity.",
            slide=slide_id,
            slot_id=slot.get("slot_id"),
            max_chars=max_chars,
            actual_chars=len(content),
        )
