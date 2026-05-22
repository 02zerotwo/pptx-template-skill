"""Manifest JSON helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"


def load_manifest(workspace: Path) -> dict[str, Any]:
    path = workspace / "template_manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))


def write_manifest(workspace: Path, manifest: dict[str, Any]) -> Path:
    path = workspace / "template_manifest.json"
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def slot_index(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for slide in manifest.get("slides", []):
        slide_id = slide.get("slide_id")
        for slot in slide.get("slots", []):
            index[f"{slide_id}:{slot.get('slot_id')}"] = slot
    return index
