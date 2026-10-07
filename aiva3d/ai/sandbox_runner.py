"""Execute validated CadQuery in an isolated subprocess (not in the host app)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any, Dict, Optional

from aiva3d.ai.types import GeometryValidationResult


def _worker_script() -> str:
    return textwrap.dedent(
        """
        import json
        import sys
        import cadquery as cq
        import math

        def run(code: str):
            ns = {"cq": cq, "cadquery": cq, "math": math}
            exec(compile(code, "<cadquery_generated>", "exec"), ns, ns)
            if "result" not in ns:
                raise ValueError("Variable `result` was not defined after execution.")
            return ns["result"]

        def as_shape(obj):
            if isinstance(obj, cq.Workplane):
                v = obj.val()
                if v is None:
                    raise ValueError("result Workplane has no value.")
                return v
            if isinstance(obj, cq.Shape):
                return obj
            raise TypeError(f"result must be cq.Workplane or cq.Shape, got {type(obj)!r}")

        def main():
            payload = json.loads(sys.stdin.read())
            code = payload["code"]
            obj = run(code)
            shape = as_shape(obj)
            if not shape.isValid():
                raise ValueError("result solid failed OpenCascade isValid().")
            wp = obj if isinstance(obj, cq.Workplane) else cq.Workplane().add(shape)
            step_path = payload.get("step_path")
            stl_path = payload.get("stl_path")
            if step_path:
                cq.exporters.export(wp, step_path)
            if stl_path:
                cq.exporters.export(wp, stl_path, tolerance=0.1, angularTolerance=0.1)
            solids = shape.Solids()
            solid_count = len(solids)
            bb = shape.BoundingBox()
            bbox = {
                "xmin": float(bb.xmin),
                "xmax": float(bb.xmax),
                "ymin": float(bb.ymin),
                "ymax": float(bb.ymax),
                "zmin": float(bb.zmin),
                "zmax": float(bb.zmax),
                "x": float(bb.xmax - bb.xmin),
                "y": float(bb.ymax - bb.ymin),
                "z": float(bb.zmax - bb.zmin),
            }
            com = shape.Center()
            out = {
                "valid": solid_count >= 1 and shape.isValid(),
                "solid_count": solid_count,
                "bbox": bbox,
                "volume": float(shape.Volume()) if solid_count else 0.0,
                "center_of_mass": {"x": float(com.x), "y": float(com.y), "z": float(com.z)},
                "step_path": step_path,
                "stl_path": stl_path,
                "errors": [],
            }
            print(json.dumps(out))

        if __name__ == "__main__":
            try:
                main()
            except Exception as exc:
                print(json.dumps({"valid": False, "errors": [str(exc)]}))
                sys.exit(1)
        """
    )


def execute_cadquery_in_subprocess(
    code: str,
    *,
    timeout_s: float = 60.0,
    cwd: Optional[Path] = None,
    step_path: Optional[Path] = None,
    stl_path: Optional[Path] = None,
) -> GeometryValidationResult:
    """Run CadQuery code in a child Python process; never exec in the caller."""
    worker = _worker_script()
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    payload: Dict[str, Any] = {"code": code}
    if step_path is not None:
        step_path.parent.mkdir(parents=True, exist_ok=True)
        payload["step_path"] = str(step_path.resolve())
    if stl_path is not None:
        stl_path.parent.mkdir(parents=True, exist_ok=True)
        payload["stl_path"] = str(stl_path.resolve())
    proc = subprocess.run(
        [sys.executable, "-c", worker],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=timeout_s,
        cwd=str(cwd or Path.cwd()),
        env=env,
    )
    if proc.returncode != 0 and not proc.stdout.strip():
        err = proc.stderr.strip() or "Subprocess failed without output"
        return GeometryValidationResult(valid=False, errors=[err])

    try:
        data: Dict[str, Any] = json.loads(proc.stdout.strip() or "{}")
    except json.JSONDecodeError:
        return GeometryValidationResult(
            valid=False,
            errors=[f"Invalid worker JSON: {proc.stdout!r} stderr={proc.stderr!r}"],
        )

    if not data.get("valid"):
        return GeometryValidationResult(
            valid=False,
            errors=list(data.get("errors") or ["Unknown execution failure"]),
        )

    return GeometryValidationResult(
        valid=True,
        solid_count=int(data.get("solid_count", 0)),
        bbox=dict(data.get("bbox") or {}),
        volume=float(data["volume"]) if data.get("volume") is not None else None,
        center_of_mass=dict(data.get("center_of_mass") or {}),
        errors=[],
    )


def export_validated_cadquery(
    code: str,
    *,
    step_path: Path,
    stl_path: Optional[Path] = None,
    timeout_s: float = 120.0,
) -> GeometryValidationResult:
    """Validate by execution in subprocess and write STEP (for FreeCAD import)."""
    return execute_cadquery_in_subprocess(
        code,
        timeout_s=timeout_s,
        step_path=step_path,
        stl_path=stl_path,
    )
