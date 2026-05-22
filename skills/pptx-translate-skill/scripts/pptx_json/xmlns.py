"""Shared OOXML namespace helpers."""

from __future__ import annotations

from xml.etree import ElementTree as ET


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "ct": "http://schemas.openxmlformats.org/package/2006/content-types",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}

REL_TYPES = {
    "slide": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide",
    "image": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image",
    "chart": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart",
}


def register_namespaces() -> None:
    """Register common OOXML namespaces for stable XML serialization."""
    for prefix, uri in NS.items():
        if prefix in {"rel", "ct"}:
            continue
        ET.register_namespace(prefix, uri)
    ET.register_namespace("", NS["rel"])


def qn(prefix: str, tag: str) -> str:
    """Return a qualified XML name."""
    return f"{{{NS[prefix]}}}{tag}"
