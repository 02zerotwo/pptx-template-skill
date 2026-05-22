"""PPTX package structural validation."""

from __future__ import annotations

from pathlib import Path

from pptx_json.errors import BROKEN_RELATIONSHIP, CONTENT_TYPE_MISSING
from pptx_json.models.reports import Report
from pptx_json.package.content_types import has_override, load_content_types
from pptx_json.package.paths import part_for_rels
from pptx_json.package.rels import load_relationships, resolve_target


def _is_optional_notes_master_relationship(rels_package_path: str, rel: dict[str, str | None], resolved: str) -> bool:
    return (
        rels_package_path.startswith("ppt/notesSlides/_rels/")
        and rel.get("Type") == "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesMaster"
        and resolved.startswith("ppt/notesMasters/")
    )


def validate_package(package_dir: Path) -> Report:
    report = Report()
    content_types_path = package_dir / "[Content_Types].xml"
    if not content_types_path.exists():
        report.add_error(CONTENT_TYPE_MISSING, "Package is missing [Content_Types].xml.")
        return report
    _, content_root = load_content_types(content_types_path)

    for rels_path in package_dir.rglob("*.rels"):
        rels_package_path = rels_path.relative_to(package_dir).as_posix()
        owner = part_for_rels(rels_package_path)
        for rel in load_relationships(rels_path):
            if rel.get("TargetMode") == "External":
                continue
            target = rel.get("Target", "")
            if not target:
                continue
            resolved = resolve_target(owner, target)
            if not (package_dir / resolved).exists():
                if _is_optional_notes_master_relationship(rels_package_path, rel, resolved):
                    continue
                report.add_error(
                    BROKEN_RELATIONSHIP,
                    "Relationship target does not exist.",
                    rels=rels_package_path,
                    rel_id=rel.get("Id"),
                    target=target,
                    resolved=resolved,
                )

    slides_dir = package_dir / "ppt" / "slides"
    if slides_dir.exists():
        for slide in slides_dir.glob("slide*.xml"):
            part = slide.relative_to(package_dir).as_posix()
            if not has_override(content_root, part):
                report.add_error(
                    CONTENT_TYPE_MISSING,
                    "Slide part is missing a content type override.",
                    part=part,
                )
    return report
