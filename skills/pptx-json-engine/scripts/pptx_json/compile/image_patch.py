"""Image patch compilation."""

from __future__ import annotations

from typing import Any


def compile_image_patch(target_slide: str, slot: dict[str, Any], value: dict[str, Any]) -> dict[str, Any] | None:
    if not value.get("src") and value.get("alt") is None:
        return None
    return {
        "type": "replace_image",
        "target_slide": target_slide,
        "binding": {
            "shape_id": slot.get("binding", {}).get("shape_id"),
            "rel_id": slot.get("binding", {}).get("rel_id"),
        },
        "slot_id": slot.get("slot_id"),
        "src": value["src"],
        "alt": value.get("alt"),
    }
