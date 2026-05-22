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


class ChartSlotTests(unittest.TestCase):
    def test_detects_and_replaces_chart_cache_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "template.pptx"
            workspace = root / "workspace"
            output = workspace / "exports" / "out.pptx"
            write_feature_pptx(pptx)
            manifest = analyze_template(pptx, workspace)
            chart_slot = next(slot for slot in manifest["slides"][0]["slots"] if slot["slot_id"] == "growth_chart")
            self.assertEqual(chart_slot["type"], "chart")
            self.assertEqual(chart_slot["source"]["categories"], ["Q1", "Q2"])

            content_path = workspace / "deck_content.json"
            content_path.write_text(json.dumps({
                "title": "Chart",
                "slides": [{
                    "template_slide": "template-slide-001",
                    "content": {
                        "body": {"content": "Body"},
                        "growth_chart": {
                            "categories": ["2026", "2027"],
                            "series": [{"name": "Adoption", "values": [30, 70]}],
                        },
                    },
                }],
            }), encoding="utf-8")
            compile_patch(workspace, content_path)
            report = export_pptx(workspace, workspace / "patch_plan.json", output)
            self.assertTrue(report.ok, report.errors)
            with zipfile.ZipFile(output) as zf:
                chart_xml = zf.read("ppt/charts/chart1.xml").decode("utf-8")
            self.assertIn("Adoption", chart_xml)
            self.assertIn("2027", chart_xml)
            self.assertIn("70", chart_xml)

    def test_repeated_chart_template_slides_get_independent_chart_parts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "template.pptx"
            workspace = root / "workspace"
            output = workspace / "exports" / "out.pptx"
            write_feature_pptx(pptx)
            analyze_template(pptx, workspace)

            content_path = workspace / "deck_content.json"
            content_path.write_text(json.dumps({
                "title": "Two Charts",
                "slides": [
                    {
                        "template_slide": "template-slide-001",
                        "content": {
                            "body": {"content": "First slide"},
                            "growth_chart": {
                                "categories": ["North"],
                                "series": [{"name": "First", "values": [10]}],
                            },
                        },
                    },
                    {
                        "template_slide": "template-slide-001",
                        "content": {
                            "body": {"content": "Second slide"},
                            "growth_chart": {
                                "categories": ["South"],
                                "series": [{"name": "Second", "values": [20]}],
                            },
                        },
                    },
                ],
            }), encoding="utf-8")
            compile_patch(workspace, content_path)
            report = export_pptx(workspace, workspace / "patch_plan.json", output)
            self.assertTrue(report.ok, report.errors)

            with zipfile.ZipFile(output) as zf:
                names = set(zf.namelist())
                self.assertIn("ppt/charts/chart1.xml", names)
                self.assertIn("ppt/charts/chart2.xml", names)
                slide1_rels = zf.read("ppt/slides/_rels/slide1.xml.rels").decode("utf-8")
                slide2_rels = zf.read("ppt/slides/_rels/slide2.xml.rels").decode("utf-8")
                chart1_xml = zf.read("ppt/charts/chart1.xml").decode("utf-8")
                chart2_xml = zf.read("ppt/charts/chart2.xml").decode("utf-8")
            self.assertIn("../charts/chart1.xml", slide1_rels)
            self.assertIn("../charts/chart2.xml", slide2_rels)
            self.assertIn("First", chart1_xml)
            self.assertNotIn("Second", chart1_xml)
            self.assertIn("Second", chart2_xml)

    def test_rejects_chart_data_beyond_template_capacity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "template.pptx"
            workspace = root / "workspace"
            write_feature_pptx(pptx)
            analyze_template(pptx, workspace)

            content_path = workspace / "deck_content.json"
            content_path.write_text(json.dumps({
                "slides": [{
                    "template_slide": "template-slide-001",
                    "content": {
                        "body": {"content": "Body"},
                        "growth_chart": {
                            "categories": ["Q1", "Q2", "Q3"],
                            "series": [
                                {"name": "One", "values": [1, 2, 3]},
                                {"name": "Two", "values": [4, 5, 6]},
                            ],
                        },
                    },
                }],
            }), encoding="utf-8")
            from pptx_json.validate.content_validator import validate_content
            report = validate_content(workspace, content_path, write=False)
            self.assertFalse(report.ok)
            self.assertEqual(report.errors[-1]["code"], "CAPACITY_EXCEEDED")


if __name__ == "__main__":
    unittest.main()
