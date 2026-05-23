from __future__ import annotations

import tempfile
import unittest
import json
import zipfile
from pathlib import Path

from helpers import SCRIPTS_DIR, write_feature_pptx, write_minimal_pptx  # noqa: F401
from pptx_json.analyze.analyzer import analyze_template
from pptx_json.compile.compiler import compile_patch
from pptx_json.export.exporter import export_pptx


class TextSlotTests(unittest.TestCase):
    def test_detects_explicit_text_slots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "template.pptx"
            workspace = root / "workspace"
            write_minimal_pptx(pptx)
            manifest = analyze_template(pptx, workspace)
            slots = manifest["slides"][0]["slots"]
            slot_ids = {slot["slot_id"] for slot in slots}
            self.assertIn("cover_title", slot_ids)
            self.assertIn("cover_subtitle", slot_ids)
            title = next(slot for slot in slots if slot["slot_id"] == "cover_title")
            self.assertIn("box", title["capacity"])
            self.assertIn("font_size", title["source"])

    def test_extracts_paragraphs_and_replaces_structured_paragraphs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "template.pptx"
            workspace = root / "workspace"
            output = workspace / "exports" / "out.pptx"
            write_feature_pptx(pptx)
            manifest = analyze_template(pptx, workspace)
            body = next(slot for slot in manifest["slides"][0]["slots"] if slot["slot_id"] == "body")
            self.assertEqual(body["source"]["paragraphs"][0]["text"], "Old bullet")
            self.assertTrue(body["source"]["paragraphs"][0]["bullet"])
            self.assertIn("paragraphs", body["editable_fields"])

            content_path = workspace / "deck_content.json"
            content_path.write_text(json.dumps({
                "title": "Text",
                "slides": [{
                    "template_slide": "template-slide-001",
                    "content": {
                        "body": {
                            "paragraphs": [
                                {"text": "First AIGC bullet", "bullet": True},
                                {"runs": [{"text": "Second paragraph", "bold": True}]},
                            ]
                        },
                    },
                }],
            }), encoding="utf-8")
            compile_patch(workspace, content_path)
            report = export_pptx(workspace, workspace / "patch_plan.json", output)
            self.assertTrue(report.ok, report.errors)
            with zipfile.ZipFile(output) as zf:
                slide_xml = zf.read("ppt/slides/slide1.xml").decode("utf-8")
            self.assertIn("First AIGC bullet", slide_xml)
            self.assertIn("Second paragraph", slide_xml)


if __name__ == "__main__":
    unittest.main()
