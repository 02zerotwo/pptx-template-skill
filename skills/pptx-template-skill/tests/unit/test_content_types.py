from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from helpers import SCRIPTS_DIR, write_minimal_pptx  # noqa: F401
from pptx_json.package.content_types import SLIDE_CONTENT_TYPE, add_override, has_override, load_content_types
from pptx_json.package.opc import extract_package


class ContentTypesTests(unittest.TestCase):
    def test_adds_slide_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "template.pptx"
            workspace = root / "workspace"
            write_minimal_pptx(pptx)
            extract_package(pptx, workspace)
            path = workspace / "package" / "[Content_Types].xml"
            add_override(path, "ppt/slides/slide2.xml", SLIDE_CONTENT_TYPE)
            _, root_xml = load_content_types(path)
            self.assertTrue(has_override(root_xml, "ppt/slides/slide2.xml"))


if __name__ == "__main__":
    unittest.main()
