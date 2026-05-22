"""Resource path validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pptx_json.errors import RESOURCE_NOT_FOUND, RESOURCE_OUTSIDE_WORKSPACE
from pptx_json.models.reports import Report
from pptx_json.package.paths import workspace_resource


def validate_resource(report: Report, workspace: Path, slide_id: str, slot: dict[str, Any], value: dict[str, Any]) -> None:
    if slot.get("type") != "image" or "src" not in value:
        return
    rel_path = str(value.get("src") or "")
    try:
        target = workspace_resource(workspace, rel_path)
    except Exception:
        report.add_error(
            RESOURCE_OUTSIDE_WORKSPACE,
            "Image resource path resolves outside the workspace.",
            slide=slide_id,
            slot_id=slot.get("slot_id"),
            path=rel_path,
        )
        return
    if not target.exists() or not target.is_file():
        report.add_error(
            RESOURCE_NOT_FOUND,
            "Image resource does not exist.",
            slide=slide_id,
            slot_id=slot.get("slot_id"),
            path=rel_path,
        )
