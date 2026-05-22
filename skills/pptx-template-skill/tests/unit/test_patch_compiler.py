from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from helpers import SCRIPTS_DIR, write_minimal_pptx, write_png  # noqa: F401
from pptx_json.analyze.analyzer import analyze_template
from pptx_json.compile.compiler import compile_patch


class PatchCompilerTests(unittest.TestCase):
    def test_compiles_stable_patch_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "template.pptx"
            workspace = root / "workspace"
            write_minimal_pptx(pptx)
            analyze_template(pptx, workspace)
            write_png(workspace / "assets" / "generated" / "hero.png")
            content_path = workspace / "deck_content.json"
            content_path.write_text(json.dumps({
                "title": "Deck",
                "slides": [{
                    "template_slide": "template-slide-001",
                    "content": {
                        "cover_title": {"content": "Hello"},
                        "cover_subtitle": {"content": "World"},
                        "hero_image": {"src": "assets/generated/hero.png"}
                    }
                }]
            }), encoding="utf-8")
            patch = compile_patch(workspace, content_path)
            self.assertEqual(patch["schema_version"], "1.0")
            self.assertEqual(patch["operations"][0]["type"], "copy_slide")
            self.assertIn("replace_text", {op["type"] for op in patch["operations"]})
            self.assertIn("replace_image", {op["type"] for op in patch["operations"]})


if __name__ == "__main__":
    unittest.main()
