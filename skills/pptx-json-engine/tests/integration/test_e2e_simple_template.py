from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from helpers import SCRIPTS_DIR, write_minimal_pptx, write_png  # noqa: F401
from pptx_json.analyze.analyzer import analyze_template
from pptx_json.compile.compiler import compile_patch
from pptx_json.export.exporter import export_pptx
from pptx_json.validate.content_validator import validate_content


class E2ETests(unittest.TestCase):
    def test_analyze_validate_compile_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "template.pptx"
            workspace = root / "workspace"
            output = workspace / "exports" / "output.pptx"
            write_minimal_pptx(pptx)
            analyze_template(pptx, workspace)
            write_png(workspace / "assets" / "generated" / "hero.png")
            content_path = workspace / "deck_content.json"
            content_path.write_text(json.dumps({
                "title": "Generated",
                "slides": [{
                    "template_slide": "template-slide-001",
                    "content": {
                        "cover_title": {"content": "Generated title"},
                        "cover_subtitle": {"content": "Generated subtitle"},
                        "hero_image": {"src": "assets/generated/hero.png"}
                    }
                }]
            }), encoding="utf-8")
            self.assertTrue(validate_content(workspace, content_path).ok)
            compile_patch(workspace, content_path)
            report = export_pptx(workspace, workspace / "patch_plan.json", output)
            self.assertTrue(report.ok, report.errors)
            self.assertTrue(output.exists())
            with zipfile.ZipFile(output) as zf:
                slide_xml = zf.read("ppt/slides/slide1.xml").decode("utf-8")
                self.assertIn("Generated title", slide_xml)
                self.assertIn("Generated subtitle", slide_xml)


if __name__ == "__main__":
    unittest.main()
