from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from helpers import SCRIPTS_DIR, write_feature_pptx  # noqa: F401
from pptx_json.analyze.analyzer import analyze_template
from pptx_json.compile.compiler import compile_patch
from pptx_json.export.exporter import export_pptx


class ShapeSlotTests(unittest.TestCase):
    def test_detects_and_replaces_shape_style_and_geometry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "template.pptx"
            workspace = root / "workspace"
            output = workspace / "exports" / "out.pptx"
            write_feature_pptx(pptx)
            manifest = analyze_template(pptx, workspace)
            shape_slot = next(slot for slot in manifest["slides"][0]["slots"] if slot["slot_id"] == "brand_shape")
            self.assertEqual(shape_slot["type"], "shape")
            self.assertIn("fill", shape_slot["editable_fields"])
            self.assertEqual(shape_slot["source"]["fill"], "FF0000")

            content_path = workspace / "deck_content.json"
            content_path.write_text(json.dumps({
                "title": "Shape",
                "slides": [{
                    "template_slide": "template-slide-001",
                    "content": {
                        "body": {"content": "Body"},
                        "brand_shape": {"fill": "#00AAFF", "line": "#111111", "geometry": "roundRect"},
                    },
                }],
            }), encoding="utf-8")
            compile_patch(workspace, content_path)
            report = export_pptx(workspace, workspace / "patch_plan.json", output)
            self.assertTrue(report.ok, report.errors)
            with zipfile.ZipFile(output) as zf:
                slide_xml = zf.read("ppt/slides/slide1.xml").decode("utf-8")
            self.assertIn('val="00AAFF"', slide_xml)
            self.assertIn('val="111111"', slide_xml)
            self.assertIn('prst="roundRect"', slide_xml)


if __name__ == "__main__":
    unittest.main()
