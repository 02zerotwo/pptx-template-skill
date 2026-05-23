from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from helpers import SCRIPTS_DIR, write_minimal_pptx  # noqa: F401
from pptx_json.analyze.analyzer import analyze_template
from pptx_json.validate.content_validator import validate_content


class ContentValidatorTests(unittest.TestCase):
    def test_rejects_unknown_slot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "template.pptx"
            workspace = root / "workspace"
            write_minimal_pptx(pptx)
            analyze_template(pptx, workspace)
            content_path = workspace / "deck_content.json"
            content_path.write_text(json.dumps({
                "slides": [{
                    "template_slide": "template-slide-001",
                    "content": {
                        "cover_title": {"content": "Hello"},
                        "cover_subtitle": {"content": "World"},
                        "unknown": {"content": "Bad"}
                    }
                }]
            }), encoding="utf-8")
            report = validate_content(workspace, content_path, write=False)
            self.assertFalse(report.ok)
            self.assertEqual(report.errors[-1]["code"], "UNKNOWN_SLOT")

    def test_warns_for_text_over_capacity_because_autofit_will_shrink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "template.pptx"
            workspace = root / "workspace"
            write_minimal_pptx(pptx)
            analyze_template(pptx, workspace)
            content_path = workspace / "deck_content.json"
            content_path.write_text(json.dumps({
                "slides": [{
                    "template_slide": "template-slide-001",
                    "content": {
                        "cover_title": {"content": "x" * 500},
                        "cover_subtitle": {"content": "Subtitle"}
                    }
                }]
            }), encoding="utf-8")
            report = validate_content(workspace, content_path, write=False)
            self.assertTrue(report.ok)
            self.assertEqual(report.warnings[-1]["code"], "CAPACITY_EXCEEDED")


if __name__ == "__main__":
    unittest.main()
