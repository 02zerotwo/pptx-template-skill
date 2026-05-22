#!/usr/bin/env python3
"""Analyze a PPTX template into a pptx-translate-skill workspace."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from pptx_json.analyze.analyzer import analyze_template  # noqa: E402
from pptx_json.errors import EngineError  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze a PPTX template.")
    parser.add_argument("pptx_file", help="Path to .pptx template")
    parser.add_argument("-o", "--output", required=True, help="Workspace output directory")
    parser.add_argument("--allow-pptm", action="store_true", help="Allow macro-enabled .pptm input")
    parser.add_argument("--template-id", help="Optional template id")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manifest = analyze_template(
            Path(args.pptx_file).expanduser().resolve(),
            Path(args.output).expanduser().resolve(),
            allow_pptm=args.allow_pptm,
            template_id=args.template_id,
        )
    except EngineError as exc:
        print(f"{exc.code}: {exc.message}", file=sys.stderr)
        return 1
    print(f"Analyzed {len(manifest.get('slides', []))} slides")
    print(Path(args.output).expanduser().resolve() / "template_manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
