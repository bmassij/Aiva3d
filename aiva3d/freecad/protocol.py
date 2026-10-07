"""JSON command protocol for Aiva3D ↔ FreeCAD bridge."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

DEFAULT_PORT = 8765
DEFAULT_HOST = "127.0.0.1"


@dataclass
class BridgeResponse:
    success: bool
    command: str
    message: str
    error: Optional[str] = None
    objects: List[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "command": self.command,
            "message": self.message,
            "error": self.error,
            "objects": list(self.objects),
            **self.extra,
        }


COMMANDS = frozenset(
    {
        "PING",
        "CREATE_DOCUMENT",
        "CREATE_HANDLE",
        "UPDATE_HANDLE",
        "RECOMPUTE",
        "SAVE_DOCUMENT",
        "GET_STATUS",
        "CLOSE_DOCUMENT",
    }
)
