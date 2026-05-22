from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from helpers import SCRIPTS_DIR, write_minimal_pptx  # noqa: F401
from pptx_json.analyze.analyzer import analyze_template
from pptx_json.draft.content_skeleton import draft_content_skeleton
from pptx_json.inspect.manifest_summary import summarize_for_ai
from pptx_json.verify.pptx_export import verify_pptx_text


class CliHelperTests(unittest.TestCase):
    def test_summarizes_manifest_for_ai_with_capacity_and_text_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "template.pptx"
            workspace = root / "workspace"
            write_minimal_pptx(pptx)
            manifest = analyze_template(pptx, workspace)

            summary = summarize_for_ai(manifest)

            first = summary[0]
            self.assertEqual(first["slide_id"], "template-slide-001")
            text_slot = first["text_slots"][0]
            self.assertEqual(text_slot["slot_id"], "cover_title")
            self.assertIn("current_text", text_slot)
            self.assertIn("max_chars", text_slot)
            self.assertIn("suggested_use", text_slot)

    def test_drafts_content_skeleton_with_text_slots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "template.pptx"
            workspace = root / "workspace"
            write_minimal_pptx(pptx)
            analyze_template(pptx, workspace)

            skeleton = draft_content_skeleton(workspace, title="Draft")

            self.assertEqual(skeleton["title"], "Draft")
            slide = skeleton["slides"][0]
            self.assertEqual(slide["template_slide"], "template-slide-001")
            self.assertEqual(slide["content"]["cover_title"]["content"], "")
            self.assertNotIn("hero_image", slide["content"])

    def test_verifies_pptx_visible_text_terms(self):
        with tempfile.TemporaryDirectory() as tmp:
            pptx = Path(tmp) / "template.pptx"
            write_minimal_pptx(pptx)

            result = verify_pptx_text(pptx, old_terms=["Missing old"], new_terms=["cover_title"])

            self.assertTrue(result.ok, result.errors)
            self.assertEqual(result.data["visible_slides"], 1)
            self.assertEqual(result.data["old_terms_found"], [])
            self.assertEqual(result.data["new_terms_found"], ["cover_title"])


if __name__ == "__main__":
    unittest.main()
