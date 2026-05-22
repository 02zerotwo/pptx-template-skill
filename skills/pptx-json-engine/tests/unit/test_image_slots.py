from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from helpers import SCRIPTS_DIR, write_minimal_pptx  # noqa: F401
from pptx_json.analyze.analyzer import analyze_template


class ImageSlotTests(unittest.TestCase):
    def test_detects_explicit_image_slot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "template.pptx"
            workspace = root / "workspace"
            write_minimal_pptx(pptx)
            manifest = analyze_template(pptx, workspace)
            image_slots = [slot for slot in manifest["slides"][0]["slots"] if slot["type"] == "image"]
            self.assertEqual(image_slots[0]["slot_id"], "hero_image")
            self.assertEqual(image_slots[0]["binding"]["rel_id"], "rId2")


if __name__ == "__main__":
    unittest.main()
