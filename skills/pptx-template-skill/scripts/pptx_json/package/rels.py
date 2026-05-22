"""Relationship file helpers."""

from __future__ import annotations

import posixpath
from pathlib import PurePosixPath
from typing import Any
from xml.etree import ElementTree as ET

from pptx_json.package.paths import package_path, part_for_rels, rels_path_for_part
from pptx_json.xmlns import NS


def _rel_tag() -> str:
    return f"{{{NS['rel']}}}Relationship"


def load_relationships(rels_file) -> list[dict[str, Any]]:
    if not rels_file.exists():
        return []
    root = ET.parse(rels_file).getroot()
    rels: list[dict[str, Any]] = []
    for rel in root.findall(_rel_tag()):
        rels.append({
            "Id": rel.attrib.get("Id", ""),
            "Type": rel.attrib.get("Type", ""),
            "Target": rel.attrib.get("Target", ""),
            "TargetMode": rel.attrib.get("TargetMode"),
        })
    return rels


def save_relationships(rels_file, rels: list[dict[str, Any]]) -> None:
    ET.register_namespace("", NS["rel"])
    root = ET.Element(f"{{{NS['rel']}}}Relationships")
    for item in rels:
        attrib = {
            "Id": item["Id"],
            "Type": item["Type"],
            "Target": item["Target"],
        }
        if item.get("TargetMode"):
            attrib["TargetMode"] = item["TargetMode"]
        ET.SubElement(root, f"{{{NS['rel']}}}Relationship", attrib)
    rels_file.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(rels_file, encoding="utf-8", xml_declaration=True)


def resolve_target(source_part: str | None, target: str) -> str:
    """Resolve a relationship Target to a package path."""
    if target.startswith("/"):
        return package_path(target[1:])
    base = PurePosixPath(source_part).parent if source_part else PurePosixPath("")
    normalized = posixpath.normpath(str(base / target))
    return package_path(normalized)


def target_from_part(source_part: str, target_part: str) -> str:
    """Return a relative Target from source_part to target_part."""
    source_dir = PurePosixPath(source_part).parent
    target = PurePosixPath(package_path(target_part))
    try:
        # Most slide relationships point to ../media/foo.png; this simple form is
        # enough for first-phase slide/media targets.
        if source_dir == PurePosixPath("ppt/slides") and target.parts[:2] == ("ppt", "media"):
            return str(PurePosixPath("..") / "media" / target.name)
        if source_dir == PurePosixPath("ppt") and target.parts[:2] == ("ppt", "slides"):
            return str(PurePosixPath("slides") / target.name)
    except IndexError:
        pass
    return str(target)


def next_rid(rels: list[dict[str, Any]]) -> str:
    used: set[int] = set()
    for rel in rels:
        rid = rel.get("Id", "")
        if rid.startswith("rId") and rid[3:].isdigit():
            used.add(int(rid[3:]))
    i = 1
    while i in used:
        i += 1
    return f"rId{i}"


def update_relationship_target(rels_file, rel_id: str, target: str) -> bool:
    rels = load_relationships(rels_file)
    changed = False
    for rel in rels:
        if rel["Id"] == rel_id:
            rel["Target"] = target
            changed = True
            break
    if changed:
        save_relationships(rels_file, rels)
    return changed


def rels_path_for_package_part(package_dir, part: str):
    return package_dir / rels_path_for_part(part)


def source_part_for_rels_path(rels_path: str) -> str | None:
    return part_for_rels(rels_path)
