"""Shape patch compilation."""

from __future__ import annotations

from typing import Any


def compile_shape_patch(target_slide: str, slot: dict[str, Any], value: dict[str, Any]) -> dict[str, Any] | None:
    fields = {key: value[key] for key in ("fill", "line", "opacity", "geometry") if key in value}
    if not fields:
        return None
    return {
        "type": "replace_shape_style",
        "target_slide": target_slide,
        "binding": {"shape_id": slot.get("binding", {}).get("shape_id")},
        "slot_id": slot.get("slot_id"),
        **fields,
    }
