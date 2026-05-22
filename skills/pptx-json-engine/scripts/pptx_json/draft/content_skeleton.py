"""Generate deck_content.json skeletons."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pptx_json.models.content import SCHEMA_VERSION
from pptx_json.models.manifest import load_manifest


def _slot_value(slot: dict[str, Any], *, mode: str) -> dict[str, Any] | None:
    slot_type = slot.get("type")
    source = slot.get("source", {})
    if slot_type == "text":
        content = source.get("current_text", "") if mode == "current" else ""
        return {"content": content}
    if slot_type == "table":
        cells = source.get("cells", []) if mode == "current" else []
        return {"cells": cells}
    if slot_type == "chart":
        if mode == "current":
            return {
                "categories": source.get("categories", []),
                "series": source.get("series", []),
            }
        return {"categories": [], "series": []}
    if slot_type == "shape":
        value: dict[str, Any] = {}
        for field in ("fill", "line", "opacity", "geometry"):
            if mode == "current" and source.get(field) is not None:
                value[field] = source[field]
        return value
    return None


def draft_content_skeleton(
    workspace: Path,
    *,
    title: str = "",
    slide_ids: list[str] | None = None,
    mode: str = "blank",
    include_optional_images: bool = False,
) -> dict[str, Any]:
    """Draft a valid-ish deck_content skeleton from a workspace manifest."""
    manifest = load_manifest(workspace)
    selected = set(slide_ids or [])
    slides = []
    for slide in manifest.get("slides", []):
        slide_id = slide.get("slide_id")
        if selected and slide_id not in selected:
            continue
        content: dict[str, Any] = {}
        for slot in slide.get("slots", []):
            if slot.get("type") == "image":
                if include_optional_images or slot.get("required"):
                    content[slot["slot_id"]] = {"src": "", "alt": ""}
                continue
            value = _slot_value(slot, mode=mode)
            if value is not None:
                content[slot["slot_id"]] = value
        slides.append({"template_slide": slide_id, "content": content})
    return {
        "schema_version": SCHEMA_VERSION,
        "title": title,
        "slides": slides,
    }
