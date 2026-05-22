#!/usr/bin/env python3
"""Compile deck_content.json into public patch_plan.json."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from pptx_json.compile.compiler import compile_patch  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compile a PPTX patch plan.")
    parser.add_argument("workspace", help="Workspace directory")
    parser.add_argument("content_json", help="Path to deck_content.json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    patch_plan = compile_patch(
        Path(args.workspace).expanduser().resolve(),
        Path(args.content_json).expanduser().resolve(),
    )
    print(f"operations={len(patch_plan.get('operations', []))}")
    print(Path(args.workspace).expanduser().resolve() / "patch_plan.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
