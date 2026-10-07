"""
Run inside a live FreeCAD GUI session (Python console or macro).

  import runpy
  runpy.run_path(r"D:\\AI\\3d\\scripts\\freecad\\aiva3d_bridge_server.py")

This starts the server automatically (look for "Aiva3D bridge listening …").
runpy does not put ``start_server`` in the console globals — do not call
``start_server()`` unless you first bind it, e.g.::

  _aiva3d = runpy.run_path(r"...")
  start_server = _aiva3d["start_server"]

Starts a local HTTP JSON server on 127.0.0.1:8765 (Aiva3D client posts commands here).
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Optional

PORT = 8765
BRIDGE_VERSION = "2026-03-03-v3"
_server: Optional[HTTPServer] = None
_doc_name = "Aiva3D_Handle"


def _get_document(name: str):
    """Return open document by name, or None (avoid getDocument raising on FC 1.x)."""
    import FreeCAD as App

    return App.listDocuments().get(name)


def _gui_event_loop_available() -> bool:
    try:
        import FreeCADGui  # noqa: F401
    except ImportError:
        return False
    try:
        from PySide2 import QtCore
    except ImportError:
        try:
            from PySide6 import QtCore
        except ImportError:
            try:
                from PySide import QtCore
            except ImportError:
                return False
    return QtCore.QCoreApplication.instance() is not None


def _run_on_gui_thread(fn):
    """Run document mutations on the Qt GUI thread when a FreeCAD GUI session is active."""
    import threading

    if not _gui_event_loop_available():
        return fn()

    try:
        from PySide2 import QtCore
    except ImportError:
        try:
            from PySide6 import QtCore
        except ImportError:
            from PySide import QtCore

    done = threading.Event()
    holder: dict = {}

    def _runner() -> None:
        try:
            holder["value"] = fn()
        except Exception as exc:  # noqa: BLE001
            holder["error"] = exc
        finally:
            done.set()

    QtCore.QTimer.singleShot(0, _runner)
    if not done.wait(timeout=120.0):
        raise TimeoutError("FreeCAD GUI thread did not run the bridge command in time")
    if "error" in holder:
        raise holder["error"]
    return holder["value"]


def _response(
    success: bool,
    command: str,
    message: str,
    error: Optional[str] = None,
    objects: Optional[list[str]] = None,
    **extra: Any,
) -> dict:
    out = {
        "success": success,
        "command": command,
        "message": message,
        "error": error,
        "objects": objects or [],
    }
    out.update(extra)
    return out


def _ensure_groups(doc):
    import FreeCAD as App

    def _get_or_create(name, label):
        obj = doc.getObject(name)
        if obj is None:
            obj = doc.addObject("App::DocumentObjectGroup", name)
            obj.Label = label
        return obj

    ref = _get_or_create("Reference", "Reference")
    prod = _get_or_create("Production", "Production")
    meta = _get_or_create("Metadata", "Metadata")
    return ref, prod, meta


def _set_design_props(obj, props: Dict[str, Any]) -> None:
    import FreeCAD as App

    for key, val in props.items():
        if hasattr(obj, key):
            setattr(obj, key, val)
            continue
        if isinstance(val, (int, float)):
            obj.addProperty("App::PropertyLength", key, "Design", "")
            setattr(obj, key, float(val))
        else:
            obj.addProperty("App::PropertyString", key, "Design", "")
            setattr(obj, key, str(val))


def _load_or_update_step(doc, group, label: str, path: str, production: bool) -> Any:
    import Part

    obj = doc.getObject(label)
    shape = Part.read(path)
    if obj is None:
        obj = doc.addObject("Part::Feature", label)
        group.addObject(obj)
    obj.Shape = shape
    if not hasattr(obj, "ProductionPart"):
        obj.addProperty("App::PropertyBool", "ProductionPart", "Aiva3D", "")
    obj.ProductionPart = production
    return obj


def _handle_create_or_update(payload: Dict[str, Any], update: bool) -> dict:
    import FreeCAD as App
    import json as _json
    from pathlib import Path

    global _doc_name
    name = payload.get("document_name") or _doc_name
    doc = _get_document(name)
    if doc is None:
        doc = App.newDocument(name)
    _doc_name = doc.Name
    ref_g, prod_g, meta_g = _ensure_groups(doc)

    steps = payload.get("steps") or {}
    ref = _load_or_update_step(doc, ref_g, "OriginalMetalHandle", steps["reference_step"], False)
    hard = _load_or_update_step(doc, prod_g, "HardCore", steps["hard_step"], True)
    soft = _load_or_update_step(doc, prod_g, "SoftGrip", steps["soft_step"], True)

    _set_design_props(
        hard,
        {"GripLength": 110.0, "HardCoreDiameter": 11.1, "Material": "hard_print"},
    )
    _set_design_props(
        soft,
        {
            "GripLength": 110.0,
            "GripOuterDiameter": 30.0,
            "SoftWallNominal": 9.45,
            "Material": "variShore",
        },
    )

    meta_path = payload.get("metadata_path")
    if meta_path and Path(meta_path).exists():
        data = _json.loads(Path(meta_path).read_text(encoding="utf-8"))
        meas = doc.getObject("Measurements")
        if meas is None:
            meas = doc.addObject("App::FeaturePython", "Measurements")
            meta_g.addObject(meas)
        if not hasattr(meas, "Source"):
            meas.addProperty("App::PropertyString", "Source", "Aiva3D", "")
        meas.Source = str(data.get("source", ""))
        if not hasattr(meas, "Grid"):
            meas.addProperty("App::PropertyString", "Grid", "Aiva3D", "")
        meas.Grid = str(data.get("grid", ""))

    doc.recompute()
    fcstd = payload.get("fcstd_path")
    if fcstd:
        dest = Path(str(fcstd))
        dest.parent.mkdir(parents=True, exist_ok=True)
        doc.saveAs(str(dest))

    try:
        import FreeCADGui

        FreeCADGui.updateGui()
    except Exception:  # noqa: BLE001
        pass

    cmd = "UPDATE_HANDLE" if update else "CREATE_HANDLE"
    return _response(
        True,
        cmd,
        "Aiva3D handle synchronized",
        objects=["OriginalMetalHandle", "HardCore", "SoftGrip"],
        document=doc.Name,
        fcstd_saved=bool(fcstd),
    )


class _Aiva3DHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def do_GET(self) -> None:
        """Browsers open :8765 with GET — show a short hint (API uses POST JSON only)."""
        body = (
            "<!DOCTYPE html><html><head><meta charset='utf-8'>"
            "<title>Aiva3D FreeCAD bridge</title></head><body>"
            f"<h1>Aiva3D bridge ({BRIDGE_VERSION})</h1>"
            "<p>Running on <code>127.0.0.1:8765</code>. "
            "Use the <strong>Streamlit</strong> app: Connect → Create in FreeCAD.</p>"
            "</body></html>"
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            self._send(_response(False, "UNKNOWN", "Invalid JSON", error="json"))
            return
        command = str(body.get("command", "")).upper()
        payload = body.get("payload") or {}
        try:
            if command == "PING":
                result = self._dispatch(command, payload)
            else:
                result = _run_on_gui_thread(lambda: self._dispatch(command, payload))
        except Exception as exc:  # noqa: BLE001
            import traceback

            result = _response(
                False,
                command,
                "Command failed",
                error=str(exc),
                traceback=traceback.format_exc(),
            )
        self._send(result)

    def _dispatch(self, command: str, payload: Dict[str, Any]) -> dict:
        import FreeCAD as App

        if command == "PING":
            return _response(
                True,
                "PING",
                "Aiva3D FreeCAD bridge alive",
                bridge_version=BRIDGE_VERSION,
            )
        if command == "SHUTDOWN":
            global _server
            srv = _server
            if srv is not None:
                srv.shutdown()
                _server = None
            return _response(True, "SHUTDOWN", "bridge stopped")
        if command == "GET_STATUS":
            doc = _get_document(_doc_name)
            names = [o.Name for o in doc.Objects] if doc else []
            return _response(True, "GET_STATUS", "ok", objects=names, document=_doc_name)
        if command == "CREATE_DOCUMENT":
            name = payload.get("name") or _doc_name
            doc = _get_document(name)
            if doc is None:
                doc = App.newDocument(name)
            return _response(True, "CREATE_DOCUMENT", f"Document {doc.Name}", document=doc.Name)
        if command == "CREATE_HANDLE":
            return _handle_create_or_update(payload, update=False)
        if command == "UPDATE_HANDLE":
            return _handle_create_or_update(payload, update=True)
        if command == "RECOMPUTE":
            doc = _get_document(_doc_name)
            if doc:
                doc.recompute()
            return _response(True, "RECOMPUTE", "recomputed")
        if command == "SAVE_DOCUMENT":
            from pathlib import Path

            path = payload.get("path")
            doc_name = payload.get("document") or _doc_name
            doc = _get_document(doc_name)
            if not doc or not path:
                return _response(False, "SAVE_DOCUMENT", "missing doc or path", error="path")
            dest = Path(str(path))
            dest.parent.mkdir(parents=True, exist_ok=True)
            doc.saveAs(str(dest))
            return _response(True, "SAVE_DOCUMENT", f"saved {path}")
        if command == "CLOSE_DOCUMENT":
            doc = _get_document(_doc_name)
            if doc:
                App.closeDocument(doc.Name)
            return _response(True, "CLOSE_DOCUMENT", "closed")
        return _response(False, command, "Unknown command", error="unknown")

    def _send(self, data: dict) -> None:
        encoded = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def _shutdown_previous_bridge(port: int = PORT) -> None:
    """Stop a bridge HTTP server left from an earlier runpy in this FreeCAD session."""
    import time

    try:
        import FreeCAD as App
    except ImportError:
        App = None  # type: ignore[assignment]

    if App is not None:
        prev = getattr(App, "_aiva3d_bridge_server", None)
        if prev is not None:
            try:
                prev.shutdown()
            except Exception:  # noqa: BLE001
                pass
            setattr(App, "_aiva3d_bridge_server", None)
            time.sleep(0.25)

    try:
        import urllib.request

        body = json.dumps({"command": "SHUTDOWN", "payload": {}}).encode("utf-8")
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=2.0)
        time.sleep(0.25)
    except Exception:  # noqa: BLE001
        pass


def _bridge_self_test(port: int = PORT) -> None:
    import time
    import urllib.request

    time.sleep(0.15)
    body = json.dumps({"command": "PING", "payload": {}}).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"Aiva3D bridge self-test failed: {exc}")
        return
    if data.get("bridge_version") != BRIDGE_VERSION:
        print(
            "WARNING: Another (older) listener may still be on port "
            f"{port}. Fully quit FreeCAD and start the bridge once."
        )
    else:
        print(f"Aiva3D bridge self-test OK ({BRIDGE_VERSION})")


def start_server(port: int = PORT) -> HTTPServer:
    global _server
    _shutdown_previous_bridge(port)

    try:
        import FreeCAD as App
    except ImportError:
        App = None  # type: ignore[assignment]

    if _server is not None:
        try:
            _server.shutdown()
        except Exception:  # noqa: BLE001
            pass
        _server = None

    try:
        _server = HTTPServer(("127.0.0.1", port), _Aiva3DHandler)
    except OSError as exc:
        print(
            f"Could not bind port {port} ({exc}). "
            "Close FreeCAD completely and run this script again."
        )
        raise
    thread = threading.Thread(target=_server.serve_forever, daemon=True)
    thread.start()
    if App is not None:
        setattr(App, "_aiva3d_bridge_server", _server)
    print(f"Aiva3D bridge v{BRIDGE_VERSION} listening on http://127.0.0.1:{port}")
    _bridge_self_test(port)
    return _server


# runpy.run_path sets __name__ to "<run_path>" (see module docstring).
if __name__ in ("__main__", "<run_path>"):
    start_server()
