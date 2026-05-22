"""Patch plan executor and PPTX exporter."""

from __future__ import annotations

import shutil
from pathlib import Path

from pptx_json.export.chart_apply import apply_chart_patch
from pptx_json.export.atomic_write import atomic_replace
from pptx_json.export.image_apply import apply_image_patch
from pptx_json.export.shape_apply import apply_shape_patch
from pptx_json.export.slide_copy import apply_slide_copies
from pptx_json.export.table_apply import apply_table_patch
from pptx_json.export.text_apply import apply_text_patch
from pptx_json.models.patch import load_patch_plan
from pptx_json.models.reports import Report, write_report
from pptx_json.package.opc import pack_pptx
from pptx_json.package.validate import validate_package


def export_pptx(workspace: Path, patch_path: Path, output_path: Path) -> Report:
    patch_plan = load_patch_plan(patch_path)
    source_package = workspace / "package"
    export_package = workspace / ".export_tmp_package"
    if export_package.exists():
        shutil.rmtree(export_package)
    shutil.copytree(source_package, export_package)

    report = Report()
    try:
        operations = patch_plan.get("operations", [])
        apply_slide_copies(export_package, operations)
        for operation in operations:
            op_type = operation.get("type")
            if op_type == "replace_text":
                apply_text_patch(export_package, operation)
            elif op_type == "replace_image":
                apply_image_patch(export_package, workspace, operation)
            elif op_type == "replace_table_cells":
                apply_table_patch(export_package, operation)
            elif op_type == "replace_chart_data":
                apply_chart_patch(export_package, operation)
            elif op_type == "replace_shape_style":
                apply_shape_patch(export_package, operation)
        validation = validate_package(export_package)
        report.merge(validation)
        if not report.ok:
            write_report(workspace / "reports" / "export-report.json", report)
            return report
        tmp_pptx = output_path.with_suffix(output_path.suffix + ".tmp")
        if tmp_pptx.exists():
            tmp_pptx.unlink()
        pack_pptx(export_package, tmp_pptx)
        atomic_replace(tmp_pptx, output_path)
        report.data["output"] = str(output_path)
        write_report(workspace / "reports" / "export-report.json", report)
        return report
    finally:
        if export_package.exists():
            shutil.rmtree(export_package)
