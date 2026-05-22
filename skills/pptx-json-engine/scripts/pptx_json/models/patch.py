"""Patch plan JSON helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"


def load_patch_plan(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_patch_plan(workspace: Path, patch_plan: dict[str, Any]) -> Path:
    path = workspace / "patch_plan.json"
    path.write_text(
        json.dumps(patch_plan, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path
