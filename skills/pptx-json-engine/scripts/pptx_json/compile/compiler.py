"""Compile deck_content.json into public patch_plan.json."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pptx_json.compile.chart_patch import compile_chart_patch
from pptx_json.compile.image_patch import compile_image_patch
from pptx_json.compile.shape_patch import compile_shape_patch
from pptx_json.compile.table_patch import compile_table_patch
from pptx_json.compile.text_patch import compile_text_patch
from pptx_json.models.content import load_content
from pptx_json.models.manifest import load_manifest
from pptx_json.models.patch import SCHEMA_VERSION, write_patch_plan
from pptx_json.models.reports import write_report
from pptx_json.package.rels import load_relationships
from pptx_json.validate.content_validator import validate_content
from pptx_json.xmlns import REL_TYPES


def _slide_index(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {slide["slide_id"]: slide for slide in manifest.get("slides", [])}


def _slot_index(slide: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {slot["slot_id"]: slot for slot in slide.get("slots", [])}


def compile_patch(workspace: Path, content_path: Path) -> dict[str, Any]:
    validation = validate_content(workspace, content_path, write=True)
    if not validation.ok:
        write_report(workspace / "reports" / "compile-report.json", validation)
        raise SystemExit(1)

    manifest = load_manifest(workspace)
    content = load_content(content_path)
    slides_by_id = _slide_index(manifest)

    # Read existing presentation rels to find the max rId in use by non-slide
    # relationships (slideMaster, theme, presProps, etc.). New slide rIds must
    # start *after* these to avoid overwriting them.
    pres_rels_path = workspace / "package" / "ppt" / "_rels" / "presentation.xml.rels"
    max_existing_rid = 0
    if pres_rels_path.exists():
        for rel in load_relationships(pres_rels_path):
            rel_id = rel.get("Id", "")
            if rel_id.startswith("rId"):
                try:
                    max_existing_rid = max(max_existing_rid, int(rel_id[3:]))
                except ValueError:
                    pass
    # Subtract existing slide count so we only reserve non-slide rIds
    existing_slide_count = len([
        rel for rel in load_relationships(pres_rels_path)
        if rel.get("Type") == REL_TYPES["slide"]
    ]) if pres_rels_path.exists() else 0
    rid_start = max_existing_rid - existing_slide_count

    operations: list[dict[str, Any]] = []
    for index, slide_content in enumerate(content.get("slides", []), start=1):
        template_slide_id = slide_content["template_slide"]
        slide_manifest = slides_by_id[template_slide_id]
        target_slide = f"ppt/slides/slide{index}.xml"
        operations.append({
            "type": "copy_slide",
            "source_slide": slide_manifest["source_part"],
            "target_slide": target_slide,
            "new_slide_id": 255 + index,
            "presentation_rel_id": f"rId{rid_start + index}",
            "template_slide": template_slide_id,
        })
        slots_by_id = _slot_index(slide_manifest)
        for slot_id, raw_value in slide_content.get("content", {}).items():
            slot = slots_by_id.get(slot_id)
            if slot is None:
                continue
            value = raw_value if isinstance(raw_value, dict) else {"content": raw_value}
            if slot.get("type") == "text":
                operations.append(compile_text_patch(target_slide, slot, value))
            elif slot.get("type") == "image":
                image_op = compile_image_patch(target_slide, slot, value)
                if image_op:
                    operations.append(image_op)
            elif slot.get("type") == "table":
                table_op = compile_table_patch(target_slide, slot, value)
                if table_op:
                    operations.append(table_op)
            elif slot.get("type") == "chart":
                chart_op = compile_chart_patch(target_slide, slot, value)
                if chart_op:
                    operations.append(chart_op)
            elif slot.get("type") == "shape":
                shape_op = compile_shape_patch(target_slide, slot, value)
                if shape_op:
                    operations.append(shape_op)

    patch_plan = {
        "schema_version": SCHEMA_VERSION,
        "title": content.get("title", manifest.get("template_id")),
        "operations": operations,
    }
    write_patch_plan(workspace, patch_plan)
    return patch_plan
