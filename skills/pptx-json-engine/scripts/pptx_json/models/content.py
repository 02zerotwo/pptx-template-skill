"""Content JSON helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"


def load_content(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
