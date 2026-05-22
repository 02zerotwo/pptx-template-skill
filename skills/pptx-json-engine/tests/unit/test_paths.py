from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from helpers import SCRIPTS_DIR  # noqa: F401
from pptx_json.errors import EngineError
from pptx_json.package.paths import validate_zip_member, workspace_resource


class PathTests(unittest.TestCase):
    def test_rejects_zip_traversal(self):
        with self.assertRaises(EngineError):
            validate_zip_member("../evil.xml")

    def test_rejects_workspace_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(EngineError):
                workspace_resource(Path(tmp), "../evil.png")


if __name__ == "__main__":
    unittest.main()
