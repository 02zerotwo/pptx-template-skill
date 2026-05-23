from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from helpers import SCRIPTS_DIR, write_minimal_pptx  # noqa: F401
from pptx_json.export.text_apply import apply_text_patch
from pptx_json.package.opc import extract_package
from pptx_json.package.opc import write_xml
from pptx_json.xmlns import NS


def _shape_by_id(tree: ET.ElementTree, shape_id: str):
    for candidate in tree.findall(".//p:sp", NS):
        c_nv_pr = candidate.find("p:nvSpPr/p:cNvPr", NS)
        if c_nv_pr is not None and c_nv_pr.attrib.get("id") == shape_id:
            return candidate
    raise AssertionError(f"shape {shape_id} not found")


class TextApplyTests(unittest.TestCase):
    def test_replaces_text_by_shape_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "template.pptx"
            workspace = root / "workspace"
            write_minimal_pptx(pptx)
            extract_package(pptx, workspace)
            apply_text_patch(workspace / "package", {
                "target_slide": "ppt/slides/slide1.xml",
                "binding": {"shape_id": "2"},
                "content": "New title",
            })
            text = "".join(
                t.text or ""
                for t in ET.parse(workspace / "package" / "ppt" / "slides" / "slide1.xml").findall(".//a:t", NS)
            )
            self.assertIn("New title", text)

    def test_enables_norm_autofit_when_text_patch_requests_autofit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "template.pptx"
            workspace = root / "workspace"
            write_minimal_pptx(pptx)
            extract_package(pptx, workspace)
            apply_text_patch(workspace / "package", {
                "target_slide": "ppt/slides/slide1.xml",
                "binding": {"shape_id": "2"},
                "content": "A translated sentence that is longer than the source.",
                "autofit": {
                    "enabled": True,
                    "font_scale": 82000,
                },
            })
            tree = ET.parse(workspace / "package" / "ppt" / "slides" / "slide1.xml")
            autofit = tree.find(".//a:bodyPr/a:normAutofit", NS)
            self.assertIsNotNone(autofit)
            self.assertNotIn("fontScale", autofit.attrib)

    def test_marks_autofit_text_dirty_without_baking_font_sizes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "template.pptx"
            workspace = root / "workspace"
            write_minimal_pptx(pptx)
            extract_package(pptx, workspace)
            slide_path = workspace / "package" / "ppt" / "slides" / "slide1.xml"
            tree = ET.parse(slide_path)
            shape = _shape_by_id(tree, "2")
            run_props = shape.find(".//a:rPr", NS)
            if run_props is None:
                run = shape.find(".//a:r", NS)
                run_props = ET.Element(f"{{{NS['a']}}}rPr")
                run.insert(0, run_props)
            run_props.attrib["sz"] = "2000"
            paragraph = shape.find(".//a:p", NS)
            end_props = ET.SubElement(paragraph, f"{{{NS['a']}}}endParaRPr", {"sz": "2000"})
            p_pr = shape.find(".//a:pPr", NS)
            if p_pr is None:
                p_pr = ET.Element(f"{{{NS['a']}}}pPr")
                paragraph.insert(0, p_pr)
            ln_spc = ET.SubElement(p_pr, f"{{{NS['a']}}}lnSpc")
            ET.SubElement(ln_spc, f"{{{NS['a']}}}spcPts", {"val": "2400"})
            write_xml(slide_path, tree)

            apply_text_patch(workspace / "package", {
                "target_slide": "ppt/slides/slide1.xml",
                "binding": {"shape_id": "2"},
                "content": "A translated sentence that should open already scaled.",
                "autofit": {
                    "enabled": True,
                    "font_scale": 60000,
                },
            })

            tree = ET.parse(slide_path)
            shape = _shape_by_id(tree, "2")
            self.assertEqual(shape.find(".//a:rPr", NS).attrib["sz"], "2000")
            self.assertEqual(shape.find(".//a:rPr", NS).attrib["dirty"], "1")
            self.assertEqual(shape.find(".//a:rPr", NS).attrib["smtClean"], "0")
            self.assertEqual(shape.find(".//a:endParaRPr", NS).attrib["sz"], "2000")
            self.assertEqual(shape.find(".//a:endParaRPr", NS).attrib["dirty"], "1")
            self.assertEqual(shape.find(".//a:lnSpc/a:spcPts", NS).attrib["val"], "2400")

    def test_applies_compiled_layout_scale_and_width(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "template.pptx"
            workspace = root / "workspace"
            write_minimal_pptx(pptx)
            extract_package(pptx, workspace)
            slide_path = workspace / "package" / "ppt" / "slides" / "slide1.xml"
            tree = ET.parse(slide_path)
            shape = _shape_by_id(tree, "2")
            sp_pr = shape.find("p:spPr", NS)
            xfrm = sp_pr.find("a:xfrm", NS)
            xfrm.find("a:off", NS).attrib.update({"x": "100", "y": "100"})
            xfrm.find("a:ext", NS).attrib.update({"cx": "1000", "cy": "500"})
            run = shape.find(".//a:r", NS)
            run_props = ET.Element(f"{{{NS['a']}}}rPr", {"sz": "2000"})
            run.insert(0, run_props)
            write_xml(slide_path, tree)

            apply_text_patch(workspace / "package", {
                "target_slide": "ppt/slides/slide1.xml",
                "binding": {"shape_id": "2"},
                "content": "A translated title",
                "autofit": {"enabled": True, "font_scale": 100000},
                "layout": {"font_scale": 70000, "expand_cx": 200},
            })

            tree = ET.parse(slide_path)
            shape = _shape_by_id(tree, "2")
            self.assertEqual(shape.find(".//a:rPr", NS).attrib["sz"], "1400")
            self.assertEqual(shape.find("p:spPr/a:xfrm/a:ext", NS).attrib["cx"], "1200")


if __name__ == "__main__":
    unittest.main()
