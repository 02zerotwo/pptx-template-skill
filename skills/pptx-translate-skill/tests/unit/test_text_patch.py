from __future__ import annotations

import unittest

from pptx_json.compile.text_patch import compile_text_patch


class TextPatchTests(unittest.TestCase):
    def test_marks_longer_translated_text_for_autofit(self):
        operation = compile_text_patch(
            "ppt/slides/slide1.xml",
            {
                "slot_id": "title",
                "binding": {"shape_id": "2", "xpath": ".//p:sp[1]"},
                "capacity": {
                    "max_chars": 12,
                    "box": {"x": 100, "y": 100, "cx": 2000000, "cy": 400000},
                },
                "source": {"current_text": "Short title", "font_size": 2000},
            },
            {"content": "A much longer translated title"},
        )
        self.assertEqual(operation["autofit"]["enabled"], True)
        self.assertLess(operation["autofit"]["font_scale"], 100000)
        self.assertIn("layout", operation)
        self.assertLess(operation["layout"]["font_scale"], 100000)

    def test_enables_autofit_for_short_translated_text_too(self):
        operation = compile_text_patch(
            "ppt/slides/slide1.xml",
            {
                "slot_id": "title",
                "binding": {"shape_id": "2", "xpath": ".//p:sp[1]"},
                "capacity": {"max_chars": 80},
            },
            {"content": "Short title"},
        )
        self.assertEqual(operation["autofit"]["enabled"], True)
        self.assertEqual(operation["autofit"]["font_scale"], 100000)


if __name__ == "__main__":
    unittest.main()
