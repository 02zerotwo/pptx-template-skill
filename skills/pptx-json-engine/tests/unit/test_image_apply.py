from __future__ import annotations

import tempfile
import unittest
from xml.etree import ElementTree as ET
from pathlib import Path

from helpers import SCRIPTS_DIR, write_minimal_pptx, write_png  # noqa: F401
from pptx_json.export.image_apply import apply_image_patch
from pptx_json.package.opc import extract_package
from pptx_json.package.rels import load_relationships


class ImageApplyTests(unittest.TestCase):
    def test_replaces_image_relationship_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "template.pptx"
            workspace = root / "workspace"
            write_minimal_pptx(pptx)
            extract_package(pptx, workspace)
            write_png(workspace / "assets" / "generated" / "hero.png")
            apply_image_patch(workspace / "package", workspace, {
                "target_slide": "ppt/slides/slide1.xml",
                "binding": {"rel_id": "rId2"},
                "src": "assets/generated/hero.png",
            })
            rels = load_relationships(workspace / "package" / "ppt" / "slides" / "_rels" / "slide1.xml.rels")
            self.assertTrue(any(rel["Target"].endswith("hero.png") for rel in rels))

    def test_writes_image_alt_text_to_picture_description(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "template.pptx"
            workspace = root / "workspace"
            write_minimal_pptx(pptx)
            extract_package(pptx, workspace)
            apply_image_patch(workspace / "package", workspace, {
                "target_slide": "ppt/slides/slide1.xml",
                "binding": {"shape_id": "3", "rel_id": "rId2"},
                "alt": "AIGC hero image",
            })
            tree = ET.parse(workspace / "package" / "ppt" / "slides" / "slide1.xml")
            descriptions = [
                node.attrib.get("descr")
                for node in tree.findall(".//{http://schemas.openxmlformats.org/presentationml/2006/main}pic/{http://schemas.openxmlformats.org/presentationml/2006/main}nvPicPr/{http://schemas.openxmlformats.org/presentationml/2006/main}cNvPr")
            ]
            self.assertIn("AIGC hero image", descriptions)


if __name__ == "__main__":
    unittest.main()
