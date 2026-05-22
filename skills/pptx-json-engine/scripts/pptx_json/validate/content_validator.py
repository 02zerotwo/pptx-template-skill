"""deck_content.json validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pptx_json.errors import (
    FIELD_NOT_EDITABLE,
    INVALID_CONTENT,
    REQUIRED_SLOT_MISSING,
    UNKNOWN_SLOT,
    UNKNOWN_TEMPLATE_SLIDE,
)
from pptx_json.models.content import load_content
from pptx_json.models.manifest import load_manifest
from pptx_json.models.reports import Report, write_report
from pptx_json.validate.capacity import validate_capacity
from pptx_json.validate.resources import validate_resource


def _slide_index(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {slide["slide_id"]: slide for slide in manifest.get("slides", [])}


def _slot_index(slide: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {slot["slot_id"]: slot for slot in slide.get("slots", [])}


def validate_content(workspace: Path, content_path: Path, *, write: bool = True) -> Report:
    manifest = load_manifest(workspace)
    content = load_content(content_path)
    report = Report()

    slides_content = content.get("slides")
    if not isinstance(slides_content, list) or not slides_content:
        report.add_error(INVALID_CONTENT, "deck_content.json must contain a non-empty slides array.")
        if write:
            write_report(workspace / "reports" / "validation-report.json", report)
        return report

    slides_by_id = _slide_index(manifest)
    for idx, slide_content in enumerate(slides_content, start=1):
        template_slide = slide_content.get("template_slide")
        if template_slide not in slides_by_id:
            report.add_error(
                UNKNOWN_TEMPLATE_SLIDE,
                "deck_content.json references an unknown template slide.",
                slide_index=idx,
                template_slide=template_slide,
            )
            continue
        slide_manifest = slides_by_id[template_slide]
        slots_by_id = _slot_index(slide_manifest)
        values = slide_content.get("content", {})
        if not isinstance(values, dict):
            report.add_error(INVALID_CONTENT, "slide.content must be an object.", slide=template_slide)
            continue
        for slot in slide_manifest.get("slots", []):
            if slot.get("required") and slot["slot_id"] not in values:
                report.add_error(
                    REQUIRED_SLOT_MISSING,
                    "Required slot is missing from deck_content.json.",
                    slide=template_slide,
                    slot_id=slot["slot_id"],
                )
        for slot_id, raw_value in values.items():
            slot = slots_by_id.get(slot_id)
            if slot is None:
                report.add_error(
                    UNKNOWN_SLOT,
                    "deck_content.json references an unknown slot.",
                    slide=template_slide,
                    slot_id=slot_id,
                )
                continue
            value = raw_value if isinstance(raw_value, dict) else {"content": raw_value}
            editable = set(slot.get("editable_fields", []))
            for field in value:
                if field not in editable:
                    report.add_error(
                        FIELD_NOT_EDITABLE,
                        "deck_content.json tries to edit a field not allowed by the slot.",
                        slide=template_slide,
                        slot_id=slot_id,
                        field=field,
                    )
            validate_capacity(report, template_slide, slot, value)
            validate_resource(report, workspace, template_slide, slot, value)

    report.data["slides"] = len(slides_content)
    if write:
        write_report(workspace / "reports" / "validation-report.json", report)
    return report
