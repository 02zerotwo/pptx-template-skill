from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from helpers import SCRIPTS_DIR  # noqa: F401
from pptx_json.package.validate import validate_package


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_base_package(root: Path) -> Path:
    package_dir = root / "package"
    _write(
        package_dir / "[Content_Types].xml",
        """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
</Types>
""",
    )
    _write(
        package_dir / "ppt/slides/slide1.xml",
        """<?xml version="1.0" encoding="UTF-8"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"/>
""",
    )
    _write(
        package_dir / "ppt/notesSlides/notesSlide1.xml",
        """<?xml version="1.0" encoding="UTF-8"?>
<p:notes xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"/>
""",
    )
    return package_dir


class PackageValidateTests(unittest.TestCase):
    def test_ignores_missing_notes_master_relationship_from_notes_slide(self):
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = _write_base_package(Path(tmp))
            _write(
                package_dir / "ppt/notesSlides/_rels/notesSlide1.xml.rels",
                """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesMaster" Target="../notesMasters/notesMaster1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="../slides/slide1.xml"/>
</Relationships>
""",
            )

            report = validate_package(package_dir)

            self.assertTrue(report.ok)
            self.assertEqual(report.errors, [])

    def test_still_reports_other_missing_relationship_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = _write_base_package(Path(tmp))
            _write(
                package_dir / "ppt/notesSlides/_rels/notesSlide1.xml.rels",
                """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="../slides/missing-slide.xml"/>
</Relationships>
""",
            )

            report = validate_package(package_dir)

            self.assertFalse(report.ok)
            self.assertEqual(len(report.errors), 1)
            self.assertEqual(report.errors[0]["resolved"], "ppt/slides/missing-slide.xml")


if __name__ == "__main__":
    unittest.main()
