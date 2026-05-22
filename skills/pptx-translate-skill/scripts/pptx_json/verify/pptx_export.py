"""Verify exported PPTX visible text."""

from __future__ import annotations

import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from pptx_json.models.reports import Report
from pptx_json.xmlns import NS

REL_NS = {"rel": "http://schemas.openxmlformats.org/package/2006/relationships"}


def _visible_slide_parts(zf: zipfile.ZipFile) -> list[str]:
    presentation = ET.fromstring(zf.read("ppt/presentation.xml"))
    rels = ET.fromstring(zf.read("ppt/_rels/presentation.xml.rels"))
    rel_by_id = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rels.findall("rel:Relationship", REL_NS)
    }
    parts = []
    for slide_id in presentation.findall(".//p:sldIdLst/p:sldId", NS):
        rel_id = slide_id.attrib.get(f"{{{NS['r']}}}id")
        target = rel_by_id.get(str(rel_id), "")
        if target:
            parts.append("ppt/" + target.lstrip("/"))
    return parts


def _visible_text(zf: zipfile.ZipFile, parts: list[str]) -> list[str]:
    slides = []
    for part in parts:
        root = ET.fromstring(zf.read(part))
        slides.append("".join(node.text or "" for node in root.findall(".//a:t", NS)))
    return slides


def verify_pptx_text(
    pptx_path: Path,
    *,
    old_terms: list[str] | None = None,
    new_terms: list[str] | None = None,
) -> Report:
    """Check visible slide text for old-term residue and new-term presence."""
    report = Report()
    old_terms = old_terms or []
    new_terms = new_terms or []
    with zipfile.ZipFile(pptx_path) as zf:
        bad_member = zf.testzip()
        if bad_member:
            report.add_error("ZIP_CORRUPT", "PPTX zip member failed CRC check.", member=bad_member)
            return report
        parts = _visible_slide_parts(zf)
        slides = _visible_text(zf, parts)
    joined = "\n".join(slides)
    old_found = [term for term in old_terms if term and term in joined]
    new_found = [term for term in new_terms if term and term in joined]
    missing_new = [term for term in new_terms if term and term not in joined]
    if old_found:
        report.add_error("OLD_TEXT_REMAINS", "Old template text remains in visible slides.", terms=old_found)
    if missing_new:
        report.add_warning("NEW_TEXT_MISSING", "Expected new terms were not found.", terms=missing_new)
    report.data.update({
        "visible_slides": len(slides),
        "old_terms_found": old_found,
        "new_terms_found": new_found,
        "new_terms_missing": missing_new,
    })
    return report
