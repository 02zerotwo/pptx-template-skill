from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from helpers import SCRIPTS_DIR, write_minimal_pptx  # noqa: F401
from pptx_json.analyze.analyzer import analyze_template
from pptx_json.validate.content_validator import validate_content


class ResourceTests(unittest.TestCase):
    def test_rejects_resource_escape(self):
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
                        "hero_image": {"src": "../outside.png"}
                    }
                }]
            }), encoding="utf-8")
            report = validate_content(workspace, content_path, write=False)
            self.assertFalse(report.ok)
            self.assertEqual(report.errors[-1]["code"], "RESOURCE_OUTSIDE_WORKSPACE")

    def test_rejects_non_image_resource_for_image_slot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "template.pptx"
            workspace = root / "workspace"
            write_minimal_pptx(pptx)
            analyze_template(pptx, workspace)
            bad_resource = workspace / "assets" / "generated" / "not-image.txt"
            bad_resource.parent.mkdir(parents=True, exist_ok=True)
            bad_resource.write_text("not an image", encoding="utf-8")
            content_path = workspace / "deck_content.json"
            content_path.write_text(json.dumps({
                "slides": [{
                    "template_slide": "template-slide-001",
                    "content": {
                        "cover_title": {"content": "Hello"},
                        "cover_subtitle": {"content": "World"},
                        "hero_image": {"src": "assets/generated/not-image.txt"}
                    }
                }]
            }), encoding="utf-8")
            report = validate_content(workspace, content_path, write=False)
            self.assertFalse(report.ok)
            self.assertEqual(report.errors[-1]["code"], "RESOURCE_INVALID_TYPE")


if __name__ == "__main__":
    unittest.main()
