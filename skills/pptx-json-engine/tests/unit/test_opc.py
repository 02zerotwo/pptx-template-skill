from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from helpers import SCRIPTS_DIR, write_minimal_pptx  # noqa: F401
from pptx_json.package.opc import extract_package


class OpcTests(unittest.TestCase):
    def test_extracts_package_and_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "template.pptx"
            workspace = root / "workspace"
            write_minimal_pptx(pptx)
            report = extract_package(pptx, workspace)
            self.assertTrue(report.ok)
            self.assertTrue((workspace / "package" / "ppt" / "presentation.xml").exists())
            self.assertTrue((workspace / "assets" / "media" / "image1.png").exists())


if __name__ == "__main__":
    unittest.main()
