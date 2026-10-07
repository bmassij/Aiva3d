"""HTTP client for the local FreeCAD Aiva3D bridge."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

from aiva3d.freecad.protocol import DEFAULT_HOST, DEFAULT_PORT, BridgeResponse


class FreeCADBridgeClient:
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, timeout: float = 30.0) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self._base = f"http://{host}:{port}"

    def _post(self, command: str, payload: Optional[Dict[str, Any]] = None) -> BridgeResponse:
        body = json.dumps({"command": command, "payload": payload or {}}).encode("utf-8")
        req = urllib.request.Request(
            self._base,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            return BridgeResponse(
                success=False,
                command=command,
                message="Bridge unreachable",
                error=str(exc),
            )
        return BridgeResponse(
            success=bool(data.get("success")),
            command=str(data.get("command", command)),
            message=str(data.get("message", "")),
            error=data.get("error"),
            objects=list(data.get("objects") or []),
            extra={k: v for k, v in data.items() if k not in ("success", "command", "message", "error", "objects")},
        )

    def ping(self) -> BridgeResponse:
        return self._post("PING")

    def create_document(self, name: str = "Aiva3D_Handle") -> BridgeResponse:
        return self._post("CREATE_DOCUMENT", {"name": name})

    def sync_handle(self, payload: Dict[str, Any], update: bool = True) -> BridgeResponse:
        cmd = "UPDATE_HANDLE" if update else "CREATE_HANDLE"
        prev = self.timeout
        self.timeout = max(prev, 120.0)
        try:
            return self._post(cmd, payload)
        finally:
            self.timeout = prev

    def recompute(self) -> BridgeResponse:
        return self._post("RECOMPUTE")

    def save_document(self, path: str, document_name: str = "Aiva3D_Handle") -> BridgeResponse:
        return self._post("SAVE_DOCUMENT", {"path": path, "document": document_name})

    def get_status(self) -> BridgeResponse:
        return self._post("GET_STATUS")

    def close_document(self) -> BridgeResponse:
        return self._post("CLOSE_DOCUMENT")
