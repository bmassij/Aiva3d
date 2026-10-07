"""Thin wrapper around bridge sync for UI and scripts."""

from __future__ import annotations

from pathlib import Path

from aiva3d.freecad.bridge import FreeCADConnection
from aiva3d.freecad.protocol import BridgeResponse
from projects.work.handle_test.parameters import HandleParameters

DEFAULT_FCSTD = Path("projects/work/handle_test/exports/handle_assembly.FCStd")


def default_fcstd_path(root: Path) -> Path:
    return root / DEFAULT_FCSTD


def sync_handle_to_freecad(
    connection: FreeCADConnection,
    params: HandleParameters,
    root: Path,
    fcstd: Path | None = None,
) -> BridgeResponse:
    path = fcstd or default_fcstd_path(root)
    return connection.sync_model(params, path)
