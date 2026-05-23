"""Text patch compilation."""

from __future__ import annotations

from typing import Any


EMU_PER_POINT = 12700


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


def _estimated_text_width_emu(content: str, font_size: int) -> float:
    ascii_count = sum(1 for char in content if ord(char) < 128)
    wide_count = len(content) - ascii_count
    point_size = font_size / 100
    estimated_points = (ascii_count * 0.55 + wide_count) * point_size
    return estimated_points * EMU_PER_POINT


def _layout(content: str, slot: dict[str, Any], font_scale: int) -> dict[str, Any] | None:
    box = slot.get("capacity", {}).get("box")
    font_size = slot.get("source", {}).get("font_size")
    if not box or not font_size or not box.get("cx"):
        return None
    estimated_width = _estimated_text_width_emu(content, int(font_size))
    available_width = int(box["cx"])
    max_expansion = int(available_width * 0.15)
    expand_cx = min(max_expansion, max(0, int(estimated_width - available_width)))
    effective_width = available_width + expand_cx
    width_scale = int(effective_width / estimated_width * 100000) if estimated_width > effective_width else 100000
    layout_scale = max(55000, min(font_scale, width_scale, 100000))
    if expand_cx <= 0 and layout_scale >= 100000:
        return None
    return {
        "font_scale": layout_scale,
        "expand_cx": expand_cx,
    }


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
    operation["autofit"] = {
        "enabled": True,
        "font_scale": font_scale,
    }
    layout = _layout(content, slot, font_scale)
    if layout:
        operation["layout"] = layout
    return operation
