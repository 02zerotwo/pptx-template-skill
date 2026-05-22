"""OPC package extraction, XML IO, and PPTX packing."""

from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from pptx_json.errors import EngineError, INVALID_PACKAGE, MACRO_DISABLED
from pptx_json.models.reports import Report
from pptx_json.package.paths import validate_zip_member
from pptx_json.xmlns import register_namespaces


def parse_xml(path: Path) -> ET.ElementTree:
    return ET.parse(path)


def write_xml(path: Path, tree: ET.ElementTree) -> None:
    register_namespaces()
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def validate_powerpoint_package(pptx_path: Path, allow_pptm: bool = False) -> None:
    if pptx_path.suffix.lower() == ".pptm" and not allow_pptm:
        raise EngineError(
            MACRO_DISABLED,
            "Macro-enabled PPTM input is disabled by default.",
            file=str(pptx_path),
        )
    if pptx_path.suffix.lower() not in {".pptx", ".pptm"}:
        raise EngineError(INVALID_PACKAGE, "Expected a .pptx or .pptm file.", file=str(pptx_path))
    try:
        with zipfile.ZipFile(pptx_path, "r") as zf:
            names = set(zf.namelist())
            if "ppt/presentation.xml" not in names or "[Content_Types].xml" not in names:
                raise EngineError(
                    INVALID_PACKAGE,
                    "Package is missing required PowerPoint parts.",
                    file=str(pptx_path),
                )
    except zipfile.BadZipFile as exc:
        raise EngineError(INVALID_PACKAGE, "Input is not a valid zip package.", file=str(pptx_path)) from exc


def extract_package(pptx_path: Path, workspace: Path, allow_pptm: bool = False) -> Report:
    """Create a workspace with source, package, assets, reports, and exports."""
    validate_powerpoint_package(pptx_path, allow_pptm=allow_pptm)
    workspace.mkdir(parents=True, exist_ok=True)
    for child in ("package", "assets", "reports", "exports"):
        path = workspace / child
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)
    source_dir = workspace / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(pptx_path, source_dir / pptx_path.name)

    package_dir = workspace / "package"
    with zipfile.ZipFile(pptx_path, "r") as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            member = validate_zip_member(info.filename)
            target = package_dir / Path(*member.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info, "r") as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)

    media_dir = package_dir / "ppt" / "media"
    asset_media = workspace / "assets" / "media"
    asset_media.mkdir(parents=True, exist_ok=True)
    if media_dir.exists():
        for media in media_dir.iterdir():
            if media.is_file():
                shutil.copy2(media, asset_media / media.name)

    report = Report()
    report.data["workspace"] = str(workspace)
    report.data["source"] = str(source_dir / pptx_path.name)
    return report


def pack_pptx(package_dir: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(package_dir.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(package_dir).as_posix())


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
