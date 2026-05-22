"""Content type helpers."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any
from xml.etree import ElementTree as ET

from pptx_json.xmlns import NS


CONTENT_TYPES = {
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".emf": "image/x-emf",
    ".wmf": "image/x-wmf",
    ".xml": "application/xml",
}

SLIDE_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.presentationml.slide+xml"


def _override_tag() -> str:
    return f"{{{NS['ct']}}}Override"


def _default_tag() -> str:
    return f"{{{NS['ct']}}}Default"


def load_content_types(path) -> tuple[ET.ElementTree, ET.Element]:
    tree = ET.parse(path)
    return tree, tree.getroot()


def has_override(root: ET.Element, part_name: str) -> bool:
    wanted = "/" + str(PurePosixPath(part_name))
    for override in root.findall(_override_tag()):
        if override.attrib.get("PartName") == wanted:
            return True
    return False


def add_override(path, part_name: str, content_type: str) -> None:
    ET.register_namespace("", NS["ct"])
    tree, root = load_content_types(path)
    if not has_override(root, part_name):
        ET.SubElement(
            root,
            _override_tag(),
            {"PartName": "/" + str(PurePosixPath(part_name)), "ContentType": content_type},
        )
        tree.write(path, encoding="utf-8", xml_declaration=True)


def defaults(root: ET.Element) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in root.findall(_default_tag()):
        ext = item.attrib.get("Extension")
        content_type = item.attrib.get("ContentType")
        if ext and content_type:
            result[ext.lower()] = content_type
    return result


def ensure_default(path, extension: str, content_type: str) -> None:
    ET.register_namespace("", NS["ct"])
    tree, root = load_content_types(path)
    existing = defaults(root)
    ext = extension.lstrip(".").lower()
    if ext not in existing:
        ET.SubElement(root, _default_tag(), {"Extension": ext, "ContentType": content_type})
        tree.write(path, encoding="utf-8", xml_declaration=True)


def content_type_for_path(package_path: str) -> str | None:
    suffix = PurePosixPath(package_path).suffix.lower()
    if package_path.startswith("ppt/slides/") and suffix == ".xml":
        return SLIDE_CONTENT_TYPE
    return CONTENT_TYPES.get(suffix)
