"""Text patch compilation."""

from __future__ import annotations

from typing import Any


def compile_text_patch(target_slide: str, slot: dict[str, Any], value: dict[str, Any]) -> dict[str, Any]:
    operation = {
        "type": "replace_text",
        "target_slide": target_slide,
        "binding": {
            "shape_id": slot.get("binding", {}).get("shape_id"),
            "xpath": slot.get("binding", {}).get("xpath"),
        },
        "slot_id": slot.get("slot_id"),
        "content": str(value.get("content", "")),
    }
    if "paragraphs" in value:
        operation["paragraphs"] = value.get("paragraphs", [])
    return operation
