from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from helpers import SCRIPTS_DIR, write_minimal_pptx  # noqa: F401
from pptx_json.package.opc import extract_package
from pptx_json.package.rels import load_relationships, resolve_target


class RelationshipTests(unittest.TestCase):
    def test_loads_and_resolves_relationships(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "template.pptx"
            workspace = root / "workspace"
            write_minimal_pptx(pptx)
            extract_package(pptx, workspace)
            rels = load_relationships(workspace / "package" / "ppt" / "slides" / "_rels" / "slide1.xml.rels")
            self.assertEqual(rels[0]["Id"], "rId2")
            self.assertEqual(resolve_target("ppt/slides/slide1.xml", rels[0]["Target"]), "ppt/media/image1.png")


if __name__ == "__main__":
    unittest.main()
