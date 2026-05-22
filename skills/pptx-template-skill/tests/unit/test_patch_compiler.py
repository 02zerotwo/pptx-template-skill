from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

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

    def test_slide_relationship_ids_do_not_collide_with_existing_non_slide_rels(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "template.pptx"
            workspace = root / "workspace"
            write_minimal_pptx(pptx)
            analyze_template(pptx, workspace)

            rels_path = workspace / "package" / "ppt" / "_rels" / "presentation.xml.rels"
            tree = ET.parse(rels_path)
            root_el = tree.getroot()
            rel_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
            ET.SubElement(root_el, f"{{{rel_ns}}}Relationship", {
                "Id": "rId17",
                "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesMaster",
                "Target": "notesMasters/notesMaster1.xml",
            })
            tree.write(rels_path, encoding="utf-8", xml_declaration=True)

            content_path = workspace / "deck_content.json"
            content_path.write_text(json.dumps({
                "title": "Deck",
                "slides": [{
                    "template_slide": "template-slide-001",
                    "content": {
                        "cover_title": {"content": "Hello"},
                        "cover_subtitle": {"content": "World"},
                    }
                }]
            }), encoding="utf-8")

            patch = compile_patch(workspace, content_path)
            copy_op = next(op for op in patch["operations"] if op["type"] == "copy_slide")
            self.assertEqual(copy_op["presentation_rel_id"], "rId18")


if __name__ == "__main__":
    unittest.main()
