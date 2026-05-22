"""AI-oriented manifest summaries."""

from __future__ import annotations

from typing import Any


def _preview(text: str, limit: int = 120) -> str:
    compact = " ".join(str(text or "").split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1] + "…"


def _suggest_text_use(slot: dict[str, Any]) -> str:
    slot_id = str(slot.get("slot_id", "")).lower()
    source = slot.get("source", {})
    kind = source.get("kind")
    placeholder_type = str(source.get("placeholder_type", "")).lower()
    if "title" in slot_id or placeholder_type in {"title", "ctrtitle"}:
        return "title"
    if "subtitle" in slot_id or placeholder_type == "subtitle":
        return "subtitle"
    if kind == "text-shape":
        return "template_text"
    return "body"


def _summarize_text_slot(slot: dict[str, Any]) -> dict[str, Any]:
    source = slot.get("source", {})
    capacity = slot.get("capacity", {})
    return {
        "slot_id": slot.get("slot_id"),
        "required": bool(slot.get("required")),
        "current_text": _preview(source.get("current_text", "")),
        "max_chars": capacity.get("max_chars"),
        "max_lines": capacity.get("max_lines"),
        "suggested_use": _suggest_text_use(slot),
    }


def _summarize_image_slot(slot: dict[str, Any]) -> dict[str, Any]:
    source = slot.get("source", {})
    return {
        "slot_id": slot.get("slot_id"),
        "required": bool(slot.get("required")),
        "current_target": source.get("target"),
        "description": _preview(source.get("description", "")),
        "suggested_use": "image",
    }


def _summarize_generic_slot(slot: dict[str, Any]) -> dict[str, Any]:
    source = slot.get("source", {})
    return {
        "slot_id": slot.get("slot_id"),
        "type": slot.get("type"),
        "required": bool(slot.get("required")),
        "editable_fields": list(slot.get("editable_fields", [])),
        "source": source,
        "capacity": slot.get("capacity", {}),
    }


def summarize_for_ai(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Return a compact slide-by-slide summary for AI content drafting."""
    summary: list[dict[str, Any]] = []
    for slide in manifest.get("slides", []):
        text_slots = []
        image_slots = []
        other_slots = []
        for slot in slide.get("slots", []):
            slot_type = slot.get("type")
            if slot_type == "text":
                text_slots.append(_summarize_text_slot(slot))
            elif slot_type == "image":
                image_slots.append(_summarize_image_slot(slot))
            else:
                other_slots.append(_summarize_generic_slot(slot))
        summary.append({
            "slide_id": slide.get("slide_id"),
            "index": slide.get("index"),
            "role": slide.get("role"),
            "text_slots": text_slots,
            "image_slots": image_slots,
            "other_slots": other_slots,
            "preserved_objects": slide.get("preserved_objects", []),
        })
    return summary
