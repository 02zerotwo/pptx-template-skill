"""Validation and execution report helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pptx_json.errors import EngineIssue


@dataclass
class Report:
    """Machine-readable report with errors and warnings."""

    ok: bool = True
    errors: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)

    def add_error(self, code: str, message: str, **details: Any) -> None:
        self.ok = False
        self.errors.append(
            EngineIssue(code, message, "error", details).to_dict()
        )

    def add_warning(self, code: str, message: str, **details: Any) -> None:
        self.warnings.append(
            EngineIssue(code, message, "warning", details).to_dict()
        )

    def merge(self, other: "Report") -> None:
        if not other.ok:
            self.ok = False
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.data.update(other.data)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": self.errors,
            "warnings": self.warnings,
            "data": self.data,
        }


def write_report(path: Path, report: Report) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
