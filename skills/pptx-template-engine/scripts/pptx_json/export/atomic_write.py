"""Atomic output helpers."""

from __future__ import annotations

import os
from pathlib import Path


def atomic_replace(tmp_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    os.replace(tmp_path, output_path)
