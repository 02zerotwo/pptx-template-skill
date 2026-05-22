#!/usr/bin/env python3
"""Aggregate CLI for pptx-json-engine skill scripts."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
_SKILL_ROOT = _SCRIPTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from pptx_json.analyze.analyzer import analyze_template  # noqa: E402
from pptx_json.compile.compiler import compile_patch  # noqa: E402
from pptx_json.draft.content_skeleton import draft_content_skeleton  # noqa: E402
from pptx_json.export.exporter import export_pptx  # noqa: E402
from pptx_json.inspect.manifest_summary import summarize_for_ai  # noqa: E402
from pptx_json.models.manifest import load_manifest  # noqa: E402
from pptx_json.verify.pptx_export import verify_pptx_text  # noqa: E402
from pptx_json.validate.content_validator import validate_content  # noqa: E402


def _resolve(p: str) -> Path:
    return Path(p).expanduser().resolve()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="pptx-json-engine CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Quick start (AI workflow):
  1. uv run python scripts/pptx_json_cli.py setup
  2. uv run python scripts/pptx_json_cli.py init <template.pptx> -w <workspace>
  3. # Write deck_content.json
  4. uv run python scripts/pptx_json_cli.py build <workspace>
""",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ── One-shot commands ────────────────────────────────────────────
    sub.add_parser("setup", help="Check environment and show project info")

    init_cmd = sub.add_parser("init", help="Create workspace + analyze template in one step")
    init_cmd.add_argument("pptx_file", help="Path to .pptx template file")
    init_cmd.add_argument("-w", "--workspace", required=True, help="Workspace directory to create")
    init_cmd.add_argument("--allow-pptm", action="store_true", help="Allow macro-enabled .pptm input")
    init_cmd.add_argument("--template-id", help="Optional template id")

    build_cmd = sub.add_parser("build", help="Validate + compile + export PPTX in one step")
    build_cmd.add_argument("workspace", help="Workspace directory")
    build_cmd.add_argument("-c", "--content", help="Path to deck_content.json (default: <workspace>/deck_content.json)")
    build_cmd.add_argument("-o", "--output", help="Output .pptx path (default: <workspace>/exports/output.pptx)")

    # ── Granular commands (still available) ──────────────────────────
    analyze = sub.add_parser("analyze-template", help="Analyze PPTX template")
    analyze.add_argument("pptx_file")
    analyze.add_argument("-o", "--output", required=True)

    inspect_cmd = sub.add_parser("inspect-manifest", help="Show template slots")
    inspect_cmd.add_argument("workspace")
    inspect_cmd.add_argument("--for-ai", action="store_true")

    draft = sub.add_parser("draft-content", help="Generate content skeleton")
    draft.add_argument("workspace")
    draft.add_argument("-o", "--output", required=True)
    draft.add_argument("--title", default="")
    draft.add_argument("--mode", choices=["blank", "current"], default="blank")
    draft.add_argument("--slides", nargs="*")
    draft.add_argument("--include-optional-images", action="store_true")

    validate_cmd = sub.add_parser("validate-content", help="Validate deck_content.json")
    validate_cmd.add_argument("workspace")
    validate_cmd.add_argument("content_json")

    compile_cmd = sub.add_parser("compile-patch", help="Compile patch plan")
    compile_cmd.add_argument("workspace")
    compile_cmd.add_argument("content_json")

    export_cmd = sub.add_parser("export-pptx", help="Export PPTX from patch plan")
    export_cmd.add_argument("workspace")
    export_cmd.add_argument("-o", "--output", required=True)

    verify = sub.add_parser("verify-pptx", help="Verify exported PPTX text")
    verify.add_argument("pptx_file")
    verify.add_argument("--old-terms", nargs="*", default=[])
    verify.add_argument("--new-terms", nargs="*", default=[])

    return parser


# ── setup ────────────────────────────────────────────────────────────

def cmd_setup(_args: argparse.Namespace) -> int:
    print("=== pptx-json-engine environment check ===")
    print(f"Python:     {sys.version.split()[0]}")
    print(f"Skill root: {_SKILL_ROOT}")
    print(f"Scripts:    {_SCRIPTS_DIR}")

    # Check Python version
    if sys.version_info < (3, 10):
        print("\n✗ Python >= 3.10 required")
        return 1
    print("✓ Python >= 3.10")

    # Check stdlib modules
    try:
        import xml.etree.ElementTree, zipfile, json, shutil, copy, re, dataclasses  # noqa: F401, E401
        print("✓ Standard library modules available")
    except ImportError as e:
        print(f"✗ Missing stdlib module: {e}")
        return 1

    # Check uv
    uv_path = shutil.which("uv")
    if uv_path:
        print(f"✓ uv found: {uv_path}")
    else:
        print("⚠ uv not found (install: curl -LsSf https://astral.sh/uv/install.sh | sh)")

    # Check .venv
    venv_dir = _SKILL_ROOT / ".venv"
    if venv_dir.is_dir():
        print(f"✓ Virtual environment: {venv_dir}")
    else:
        print("⚠ No .venv found — run 'uv sync' in skill root to create")

    print("\n=== Ready ===")
    return 0


# ── init ─────────────────────────────────────────────────────────────

def cmd_init(args: argparse.Namespace) -> int:
    pptx_path = _resolve(args.pptx_file)
    workspace = _resolve(args.workspace)

    if not pptx_path.is_file():
        print(f"✗ Template not found: {pptx_path}", file=sys.stderr)
        return 1

    # Step 1: Create workspace dirs
    print(f"=== Initializing workspace: {workspace} ===")
    source_dir = workspace / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    (workspace / "assets" / "media").mkdir(parents=True, exist_ok=True)
    (workspace / "assets" / "generated").mkdir(parents=True, exist_ok=True)
    (workspace / "exports").mkdir(parents=True, exist_ok=True)

    # Step 2: Copy template to source/
    dest_pptx = source_dir / pptx_path.name
    if not dest_pptx.exists():
        shutil.copy2(pptx_path, dest_pptx)
        print(f"✓ Template copied to {dest_pptx}")
    else:
        print(f"✓ Template already at {dest_pptx}")

    # Step 3: Analyze template
    print("─── Analyzing template ───")
    from pptx_json.errors import EngineError
    try:
        manifest = analyze_template(
            pptx_path,
            workspace,
            allow_pptm=args.allow_pptm,
            template_id=args.template_id,
        )
    except EngineError as exc:
        print(f"✗ {exc.code}: {exc.message}", file=sys.stderr)
        return 1

    slide_count = len(manifest.get("slides", []))
    slot_count = sum(len(s.get("slots", [])) for s in manifest.get("slides", []))
    print(f"✓ Analyzed: {slide_count} slides, {slot_count} slots")

    # Step 4: Show AI-friendly slot summary
    print("─── Slot summary ───")
    summary = summarize_for_ai(manifest)
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    # Step 5: Generate content skeleton
    skeleton_path = workspace / "deck_content.skeleton.json"
    skeleton = draft_content_skeleton(workspace)
    skeleton_path.write_text(
        json.dumps(skeleton, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"✓ Skeleton written to {skeleton_path}")

    print(f"\n=== Workspace ready: {workspace} ===")
    print("Next: write deck_content.json, then run 'build' command")
    return 0


# ── build ────────────────────────────────────────────────────────────

def cmd_build(args: argparse.Namespace) -> int:
    workspace = _resolve(args.workspace)
    content_path = _resolve(args.content) if args.content else workspace / "deck_content.json"
    output_path = _resolve(args.output) if args.output else workspace / "exports" / "output.pptx"

    if not workspace.is_dir():
        print(f"✗ Workspace not found: {workspace}", file=sys.stderr)
        return 1
    if not content_path.is_file():
        print(f"✗ Content file not found: {content_path}", file=sys.stderr)
        return 1

    print(f"=== Building PPTX from {workspace.name} ===")
    print(f"Content:   {content_path}")
    print(f"Output:    {output_path}")

    # Step 1: Validate
    print("─── Validating content ───")
    report = validate_content(workspace, content_path)
    print(f"  ok={report.ok} errors={len(report.errors)} warnings={len(report.warnings)}")
    if not report.ok:
        for err in report.errors:
            print(f"  ✗ {err}", file=sys.stderr)
        print("✗ Validation failed — fix errors and retry", file=sys.stderr)
        return 1
    print("✓ Validation passed")

    # Step 2: Compile patch plan
    print("─── Compiling patch plan ───")
    patch = compile_patch(workspace, content_path)
    op_count = len(patch.get("operations", []))
    print(f"✓ Compiled: {op_count} operations")

    # Step 3: Export PPTX
    print("─── Exporting PPTX ───")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    export_report = export_pptx(workspace, workspace / "patch_plan.json", output_path)
    if not export_report.ok:
        for err in export_report.errors:
            print(f"  ✗ {err}", file=sys.stderr)
        print("✗ Export failed", file=sys.stderr)
        return 1

    print(f"✓ PPTX exported: {output_path}")
    print(f"\n=== Build complete ===")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    # ── One-shot commands ────────────────────────────────────────
    if args.command == "setup":
        return cmd_setup(args)
    if args.command == "init":
        return cmd_init(args)
    if args.command == "build":
        return cmd_build(args)

    # ── Granular commands ────────────────────────────────────────
    if args.command == "analyze-template":
        manifest = analyze_template(_resolve(args.pptx_file), _resolve(args.output))
        print(f"slides={len(manifest.get('slides', []))}")
        return 0
    if args.command == "inspect-manifest":
        manifest = load_manifest(_resolve(args.workspace))
        if args.for_ai:
            print(json.dumps(summarize_for_ai(manifest), ensure_ascii=False, indent=2))
            return 0
        summary = [
            {
                "slide_id": slide["slide_id"],
                "role": slide.get("role"),
                "slots": [
                    {"slot_id": slot["slot_id"], "type": slot["type"]}
                    for slot in slide.get("slots", [])
                ],
            }
            for slide in manifest.get("slides", [])
        ]
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    if args.command == "draft-content":
        skeleton = draft_content_skeleton(
            _resolve(args.workspace),
            title=args.title,
            slide_ids=args.slides,
            mode=args.mode,
            include_optional_images=args.include_optional_images,
        )
        output = _resolve(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(skeleton, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(output)
        return 0
    if args.command == "validate-content":
        report = validate_content(_resolve(args.workspace), _resolve(args.content_json))
        print(f"ok={report.ok}")
        return 0 if report.ok else 1
    if args.command == "compile-patch":
        patch = compile_patch(_resolve(args.workspace), _resolve(args.content_json))
        print(f"operations={len(patch.get('operations', []))}")
        return 0
    if args.command == "export-pptx":
        workspace = _resolve(args.workspace)
        report = export_pptx(workspace, workspace / "patch_plan.json", _resolve(args.output))
        print(f"ok={report.ok}")
        return 0 if report.ok else 1
    if args.command == "verify-pptx":
        report = verify_pptx_text(
            _resolve(args.pptx_file),
            old_terms=args.old_terms,
            new_terms=args.new_terms,
        )
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return 0 if report.ok else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
