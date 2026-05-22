#!/usr/bin/env python3
"""Export a PPTX from a workspace and patch_plan.json."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from pptx_json.export.exporter import export_pptx  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export PPTX from patch plan.")
    parser.add_argument("workspace", help="Workspace directory")
    parser.add_argument("-p", "--patch", help="Patch plan path (default: workspace/patch_plan.json)")
    parser.add_argument("-o", "--output", required=True, help="Output .pptx path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    workspace = Path(args.workspace).expanduser().resolve()
    patch_path = Path(args.patch).expanduser().resolve() if args.patch else workspace / "patch_plan.json"
    report = export_pptx(workspace, patch_path, Path(args.output).expanduser().resolve())
    print(f"ok={report.ok} errors={len(report.errors)} warnings={len(report.warnings)}")
    if report.ok:
        print(report.data.get("output", args.output))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
