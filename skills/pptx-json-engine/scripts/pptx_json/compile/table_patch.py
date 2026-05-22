"""Table patch compilation."""

from __future__ import annotations

from typing import Any


def compile_table_patch(target_slide: str, slot: dict[str, Any], value: dict[str, Any]) -> dict[str, Any] | None:
    if "cells" not in value:
        return None
    return {
        "type": "replace_table_cells",
        "target_slide": target_slide,
        "binding": {"shape_id": slot.get("binding", {}).get("shape_id")},
        "slot_id": slot.get("slot_id"),
        "cells": value.get("cells", []),
    }
