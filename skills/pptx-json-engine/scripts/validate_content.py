#!/usr/bin/env python3
"""Validate deck_content.json against template_manifest.json."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from pptx_json.validate.content_validator import validate_content  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate deck content JSON.")
    parser.add_argument("workspace", help="Workspace directory")
    parser.add_argument("content_json", help="Path to deck_content.json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = validate_content(
        Path(args.workspace).expanduser().resolve(),
        Path(args.content_json).expanduser().resolve(),
    )
    print(f"ok={report.ok} errors={len(report.errors)} warnings={len(report.warnings)}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
