"""Chart patch compilation."""

from __future__ import annotations

from typing import Any


def compile_chart_patch(target_slide: str, slot: dict[str, Any], value: dict[str, Any]) -> dict[str, Any] | None:
    if "categories" not in value and "series" not in value:
        return None
    return {
        "type": "replace_chart_data",
        "target_slide": target_slide,
        "binding": {
            "shape_id": slot.get("binding", {}).get("shape_id"),
            "chart_part": slot.get("binding", {}).get("chart_part"),
        },
        "slot_id": slot.get("slot_id"),
        "categories": value.get("categories", []),
        "series": value.get("series", []),
    }
