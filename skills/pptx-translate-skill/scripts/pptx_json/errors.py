"""Error types and stable error codes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


INVALID_PACKAGE = "INVALID_PACKAGE"
UNSAFE_ZIP_PATH = "UNSAFE_ZIP_PATH"
MACRO_DISABLED = "MACRO_DISABLED"
UNKNOWN_TEMPLATE_SLIDE = "UNKNOWN_TEMPLATE_SLIDE"
UNKNOWN_SLOT = "UNKNOWN_SLOT"
FIELD_NOT_EDITABLE = "FIELD_NOT_EDITABLE"
REQUIRED_SLOT_MISSING = "REQUIRED_SLOT_MISSING"
RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
RESOURCE_OUTSIDE_WORKSPACE = "RESOURCE_OUTSIDE_WORKSPACE"
RESOURCE_INVALID_TYPE = "RESOURCE_INVALID_TYPE"
CAPACITY_EXCEEDED = "CAPACITY_EXCEEDED"
BINDING_STALE = "BINDING_STALE"
BROKEN_RELATIONSHIP = "BROKEN_RELATIONSHIP"
CONTENT_TYPE_MISSING = "CONTENT_TYPE_MISSING"
INVALID_CONTENT = "INVALID_CONTENT"


@dataclass
class EngineIssue:
    """A structured warning or error."""

    code: str
    message: str
    severity: str = "error"
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
        }
        data.update(self.details)
        return data


class EngineError(Exception):
    """Exception carrying a stable engine error code."""

    def __init__(self, code: str, message: str, **details: Any) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details

    def to_issue(self) -> EngineIssue:
        return EngineIssue(self.code, self.message, "error", self.details)
