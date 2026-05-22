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
from pptx_json.validate.content_validator import validate_content


class TableSlotTests(unittest.TestCase):
    def test_detects_and_replaces_table_cells(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "template.pptx"
            workspace = root / "workspace"
            output = workspace / "exports" / "out.pptx"
            write_feature_pptx(pptx)
            manifest = analyze_template(pptx, workspace)
            slots = manifest["slides"][0]["slots"]
            table_slot = next(slot for slot in slots if slot["slot_id"] == "sales_table")
            self.assertEqual(table_slot["type"], "table")
            self.assertEqual(table_slot["capacity"]["rows"], 2)
            self.assertEqual(table_slot["capacity"]["cols"], 2)

            content_path = workspace / "deck_content.json"
            content_path.write_text(json.dumps({
                "title": "Table",
                "slides": [{
                    "template_slide": "template-slide-001",
                    "content": {
                        "body": {"content": "Body"},
                        "sales_table": {"cells": [["Market", "Share"], ["AIGC", "42"]]},
                    },
                }],
            }), encoding="utf-8")
            compile_patch(workspace, content_path)
            report = export_pptx(workspace, workspace / "patch_plan.json", output)
            self.assertTrue(report.ok, report.errors)
            with zipfile.ZipFile(output) as zf:
                slide_xml = zf.read("ppt/slides/slide1.xml").decode("utf-8")
            self.assertIn("AIGC", slide_xml)
            self.assertIn("Share", slide_xml)

    def test_rejects_table_cells_beyond_template_capacity(self):
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
                        "sales_table": {
                            "cells": [
                                ["Region", "Value", "Extra"],
                                ["North", "10", "Ignored"],
                                ["South", "20", "Ignored"],
                            ],
                        },
                    },
                }],
            }), encoding="utf-8")
            report = validate_content(workspace, content_path, write=False)
            self.assertFalse(report.ok)
            self.assertEqual(report.errors[-1]["code"], "CAPACITY_EXCEEDED")


if __name__ == "__main__":
    unittest.main()
