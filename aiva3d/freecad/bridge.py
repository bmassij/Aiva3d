"""High-level FreeCAD connection: live HTTP bridge or FreeCADCmd fallback."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from aiva3d.freecad.client import FreeCADBridgeClient
from aiva3d.freecad.cmd_runner import detect_freecad_cmd, sync_document_cmd, verify_fcstd_objects
from aiva3d.freecad.document_builder import build_sync_payload
from aiva3d.freecad.protocol import BridgeResponse, DEFAULT_PORT
from projects.work.handle_test.parameters import HandleParameters


@dataclass
class FreeCADConnection:
    mode: str = "disconnected"  # disconnected | http | cmd
    host: str = "127.0.0.1"
    port: int = DEFAULT_PORT
    last_fcstd: Optional[Path] = None
    last_message: str = ""
    client: Optional[FreeCADBridgeClient] = field(default=None, repr=False)

    def connect(self, prefer_cmd: bool = False) -> BridgeResponse:
        if prefer_cmd and detect_freecad_cmd() is not None:
            self.mode = "cmd"
            self.last_message = "FreeCADCmd (batch mode)"
            return BridgeResponse(
                success=True,
                command="CONNECT",
                message=self.last_message,
                extra={"freecad_cmd": True, "http_bridge": False},
            )
        self.client = FreeCADBridgeClient(self.host, self.port)
        ping = self.client.ping()
        if ping.success:
            self.mode = "http"
            ver = ping.extra.get("bridge_version", "?")
            if ver != "2026-03-03-v3":
                self.last_message = (
                    f"{ping.message} (old bridge {ver} — run scripts/restart_freecad_bridge.ps1)"
                )
            else:
                self.last_message = f"{ping.message} (bridge {ver})"
            return ping
        if detect_freecad_cmd() is not None:
            self.mode = "cmd"
            self.last_message = "FreeCADCmd available (batch sync; start GUI bridge for live viewport)"
            return BridgeResponse(
                success=True,
                command="CONNECT",
                message=self.last_message,
                extra={"freecad_cmd": True, "http_bridge": False},
            )
        self.mode = "disconnected"
        return BridgeResponse(
            success=False,
            command="CONNECT",
            message="FreeCAD not available",
            error=ping.error,
        )

    def disconnect(self) -> None:
        self.mode = "disconnected"
        self.client = None
        self.last_message = "Disconnected"

    @property
    def is_connected(self) -> bool:
        return self.mode in ("http", "cmd")

    def sync_model(
        self,
        params: HandleParameters,
        fcstd_path: Path,
        work_dir: Path | None = None,
        update: bool = True,
    ) -> BridgeResponse:
        payload = build_sync_payload(params, work_dir)
        self.last_fcstd = fcstd_path

        if self.mode == "http" and self.client:
            resp = self.client.sync_handle(
                {
                    "steps": payload["steps"],
                    "metadata_path": payload["metadata_path"],
                    "fcstd_path": str(fcstd_path),
                    "document_name": "Aiva3D_Handle",
                },
                update=update,
            )
            if not resp.success:
                if detect_freecad_cmd():
                    resp = sync_document_cmd(payload, fcstd_path)
                    self.mode = "cmd"
                else:
                    return resp
            elif not resp.extra.get("fcstd_saved"):
                doc_name = str(resp.extra.get("document") or "Aiva3D_Handle")
                save = self.client.save_document(str(fcstd_path), document_name=doc_name)
                if not save.success:
                    return save
            self.last_message = resp.message
            return resp

        if self.mode == "cmd" or detect_freecad_cmd():
            resp = sync_document_cmd(payload, fcstd_path)
            self.mode = "cmd"
            self.last_message = resp.message
            return resp

        return BridgeResponse(success=False, command="SYNC_MODEL", message="Not connected", error="connect first")

    def verify_saved(self) -> BridgeResponse:
        if self.last_fcstd is None:
            return BridgeResponse(success=False, command="GET_STATUS", message="No FCStd path", error="no file")
        return verify_fcstd_objects(self.last_fcstd)
