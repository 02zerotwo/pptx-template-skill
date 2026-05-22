"""Template analyzer entry point."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pptx_json.analyze.chart_slots import detect_chart_slots
from pptx_json.analyze.image_slots import detect_image_slots
from pptx_json.analyze.preserved import summarize_preserved_objects
from pptx_json.analyze.shape_slots import detect_shape_slots
from pptx_json.analyze.slides import iter_slides
from pptx_json.analyze.table_slots import detect_table_slots
from pptx_json.analyze.text_slots import detect_text_slots
from pptx_json.models.manifest import SCHEMA_VERSION, write_manifest
from pptx_json.models.reports import Report, write_report
from pptx_json.package.opc import extract_package, parse_xml, write_json
from pptx_json.xmlns import NS


def _presentation_size(package_dir: Path) -> dict[str, int]:
    path = package_dir / "ppt" / "presentation.xml"
    root = parse_xml(path).getroot()
    sld_sz = root.find("p:sldSz", NS)
    if sld_sz is None:
        return {"slide_width_emu": 12192000, "slide_height_emu": 6858000}
    return {
        "slide_width_emu": int(sld_sz.attrib.get("cx", "12192000")),
        "slide_height_emu": int(sld_sz.attrib.get("cy", "6858000")),
    }


def analyze_template(
    pptx_path: Path,
    workspace: Path,
    *,
    allow_pptm: bool = False,
    template_id: str | None = None,
) -> dict[str, Any]:
    """Analyze a template PPTX into a workspace manifest."""
    report = extract_package(pptx_path, workspace, allow_pptm=allow_pptm)
    package_dir = workspace / "package"
    slides = []
    for slide_ref in iter_slides(package_dir):
        text_slots = detect_text_slots(package_dir, slide_ref)
        image_slots = detect_image_slots(package_dir, slide_ref)
        table_slots = detect_table_slots(package_dir, slide_ref)
        chart_slots = detect_chart_slots(package_dir, slide_ref)
        shape_slots = detect_shape_slots(package_dir, slide_ref)
        preserved = summarize_preserved_objects(package_dir, slide_ref)
        slides.append({
            "slide_id": slide_ref["slide_id"],
            "source_part": slide_ref["source_part"],
            "role": slide_ref["role"],
            "index": slide_ref["index"],
            "slots": text_slots + image_slots + table_slots + chart_slots + shape_slots,
            "preserved_objects": preserved,
        })
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "template_id": template_id or pptx_path.stem,
        "source": {"filename": pptx_path.name, "format": pptx_path.suffix.lower().lstrip(".")},
        "presentation": _presentation_size(package_dir),
        "slides": slides,
        "assets": {
            "media": sorted(
                p.relative_to(workspace).as_posix()
                for p in (workspace / "assets" / "media").glob("*")
                if p.is_file()
            )
        },
        "warnings": report.warnings,
    }
    write_manifest(workspace, manifest)
    report.data["slides"] = len(slides)
    report.data["slots"] = sum(len(s.get("slots", [])) for s in slides)
    write_report(workspace / "reports" / "analyze-report.json", report)
    write_json(workspace / "reports" / "slot-summary.json", {
        "slides": [
            {
                "slide_id": slide["slide_id"],
                "role": slide["role"],
                "slots": [
                    {"slot_id": slot["slot_id"], "type": slot["type"]}
                    for slot in slide["slots"]
                ],
            }
            for slide in slides
        ]
    })
    return manifest
