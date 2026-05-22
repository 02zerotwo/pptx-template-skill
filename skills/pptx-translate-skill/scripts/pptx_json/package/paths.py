"""Safe path helpers for PPTX package workspaces."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from pptx_json.errors import EngineError, RESOURCE_OUTSIDE_WORKSPACE, UNSAFE_ZIP_PATH


def validate_zip_member(name: str) -> PurePosixPath:
    """Validate a zip member path and return it as a posix path."""
    posix = PurePosixPath(name)
    if name.startswith("/") or posix.is_absolute():
        raise EngineError(UNSAFE_ZIP_PATH, "Zip entry uses an absolute path.", path=name)
    if any(part in {"", ".", ".."} for part in posix.parts):
        raise EngineError(UNSAFE_ZIP_PATH, "Zip entry escapes the package root.", path=name)
    return posix


def ensure_within(root: Path, candidate: Path) -> Path:
    """Resolve a path and ensure it stays within root."""
    root_resolved = root.resolve()
    candidate_resolved = candidate.resolve()
    try:
        candidate_resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise EngineError(
            RESOURCE_OUTSIDE_WORKSPACE,
            "Path resolves outside the workspace.",
            path=str(candidate),
        ) from exc
    return candidate_resolved


def workspace_resource(workspace: Path, rel_path: str) -> Path:
    """Resolve a JSON resource path under a workspace."""
    if rel_path.startswith("/") or PurePosixPath(rel_path).is_absolute():
        raise EngineError(
            RESOURCE_OUTSIDE_WORKSPACE,
            "Resource path must be relative to the workspace.",
            path=rel_path,
        )
    if any(part in {"", ".", ".."} for part in PurePosixPath(rel_path).parts):
        raise EngineError(
            RESOURCE_OUTSIDE_WORKSPACE,
            "Resource path must not contain traversal segments.",
            path=rel_path,
        )
    return ensure_within(workspace, workspace / rel_path)


def package_path(path: str) -> str:
    """Normalize a package path to a slash-separated relative path."""
    normalized = PurePosixPath(path)
    if normalized.is_absolute() or any(part in {"", ".", ".."} for part in normalized.parts):
        raise EngineError(UNSAFE_ZIP_PATH, "Invalid package path.", path=path)
    return str(normalized)


def rels_path_for_part(part: str) -> str:
    """Return the package path for a part's relationship file."""
    part_path = PurePosixPath(package_path(part))
    return str(part_path.parent / "_rels" / f"{part_path.name}.rels")


def part_for_rels(rels_path: str) -> str | None:
    """Return the owning part path for a .rels path, or None for package rels."""
    posix = PurePosixPath(package_path(rels_path))
    if posix.parent == PurePosixPath("_rels"):
        return None
    parent = posix.parent
    if parent.name != "_rels":
        return None
    if not posix.name.endswith(".rels"):
        return None
    return str(parent.parent / posix.name[:-5])
