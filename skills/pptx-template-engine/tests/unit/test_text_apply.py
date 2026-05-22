from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from helpers import SCRIPTS_DIR, write_minimal_pptx  # noqa: F401
from pptx_json.export.text_apply import apply_text_patch
from pptx_json.package.opc import extract_package
from pptx_json.xmlns import NS


class TextApplyTests(unittest.TestCase):
    def test_replaces_text_by_shape_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "template.pptx"
            workspace = root / "workspace"
            write_minimal_pptx(pptx)
            extract_package(pptx, workspace)
            apply_text_patch(workspace / "package", {
                "target_slide": "ppt/slides/slide1.xml",
                "binding": {"shape_id": "2"},
                "content": "New title",
            })
            text = "".join(
                t.text or ""
                for t in ET.parse(workspace / "package" / "ppt" / "slides" / "slide1.xml").findall(".//a:t", NS)
            )
            self.assertIn("New title", text)


if __name__ == "__main__":
    unittest.main()
