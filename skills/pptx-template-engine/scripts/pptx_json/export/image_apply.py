"""Apply image replacement patches."""

from __future__ import annotations

import shutil
from pathlib import Path
from xml.etree import ElementTree as ET

from pptx_json.errors import BINDING_STALE, EngineError
from pptx_json.package.content_types import content_type_for_path, ensure_default
from pptx_json.package.paths import rels_path_for_part, workspace_resource
from pptx_json.package.rels import target_from_part, update_relationship_target
from pptx_json.package.opc import write_xml
from pptx_json.xmlns import NS


def _unique_media_path(package_dir: Path, source: Path) -> str:
    media_dir = package_dir / "ppt" / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    name = source.name
    target = media_dir / name
    stem = source.stem
    suffix = source.suffix
    i = 2
    while target.exists():
        target = media_dir / f"{stem}_{i}{suffix}"
        i += 1
    return target.relative_to(package_dir).as_posix()


def apply_image_patch(package_dir: Path, workspace: Path, operation: dict) -> None:
    target_slide = operation["target_slide"]
    rel_id = operation.get("binding", {}).get("rel_id")
    if operation.get("src"):
        source = workspace_resource(workspace, operation["src"])
        media_part = _unique_media_path(package_dir, source)
        shutil.copy2(source, package_dir / media_part)
        content_type = content_type_for_path(media_part)
        if content_type:
            ensure_default(package_dir / "[Content_Types].xml", Path(media_part).suffix, content_type)
        rels_file = package_dir / rels_path_for_part(target_slide)
        rel_target = target_from_part(target_slide, media_part)
        if not update_relationship_target(rels_file, rel_id, rel_target):
            raise EngineError(
                BINDING_STALE,
                "Image relationship binding no longer exists.",
                target_slide=target_slide,
                rel_id=rel_id,
            )
    if operation.get("alt") is not None:
        _apply_alt_text(package_dir / target_slide, operation)


def _apply_alt_text(slide_path: Path, operation: dict) -> None:
    shape_id = str(operation.get("binding", {}).get("shape_id") or "")
    tree = ET.parse(slide_path)
    target = None
    for pic in tree.findall(".//p:pic", NS):
        c_nv_pr = pic.find("p:nvPicPr/p:cNvPr", NS)
        if c_nv_pr is not None and c_nv_pr.attrib.get("id") == shape_id:
            target = c_nv_pr
            break
    if target is None:
        raise EngineError(BINDING_STALE, "Image alt binding no longer exists.", shape_id=shape_id)
    target.attrib["descr"] = str(operation.get("alt") or "")
    write_xml(slide_path, tree)
