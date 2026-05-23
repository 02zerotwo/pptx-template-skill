"""Text patch compilation."""

from __future__ import annotations

from typing import Any


def _paragraph_text(value: dict[str, Any]) -> str:
    parts = []
    for paragraph in value.get("paragraphs", []):
        if isinstance(paragraph, str):
            parts.append(paragraph)
        elif isinstance(paragraph, dict) and isinstance(paragraph.get("runs"), list):
            parts.append("".join(str(run.get("text", "")) for run in paragraph.get("runs", [])))
        elif isinstance(paragraph, dict):
            parts.append(str(paragraph.get("text", "")))
        else:
            parts.append(str(paragraph))
    return "\n".join(parts)


def _font_scale(content: str, slot: dict[str, Any]) -> int:
    max_chars = int(slot.get("capacity", {}).get("max_chars") or 0)
    if not max_chars or len(content) <= max_chars:
        return 100000
    return max(60000, min(100000, int(max_chars / len(content) * 100000)))


def compile_text_patch(target_slide: str, slot: dict[str, Any], value: dict[str, Any]) -> dict[str, Any]:
    content = _paragraph_text(value) if "paragraphs" in value else str(value.get("content", ""))
    font_scale = _font_scale(content, slot)
    operation = {
        "type": "replace_text",
        "target_slide": target_slide,
        "binding": {
            "shape_id": slot.get("binding", {}).get("shape_id"),
            "xpath": slot.get("binding", {}).get("xpath"),
        },
        "slot_id": slot.get("slot_id"),
        "content": content,
    }
    if "paragraphs" in value:
        operation["paragraphs"] = value.get("paragraphs", [])
    if font_scale < 100000:
        operation["autofit"] = {
            "enabled": True,
            "font_scale": font_scale,
        }
    return operation
