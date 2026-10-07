"""Make headless .FCStd files open in the FreeCAD GUI with visible solids."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

CAMERA_XML = (
    '<Camera settings="OrthographicCamera {&#10;'
    "  viewportMapping ADJUST_CAMERA&#10;"
    "  position -50 80 500&#10;"
    "  orientation 0 0 1  0&#10;"
    "  nearDistance 1&#10;"
    "  farDistance 10000&#10;"
    "  aspectRatio 1&#10;"
    "  focalDistance 500&#10;"
    "  height 360&#10;"
    "&#10;}&#10;\"/>"
)


def _object_names(document_xml: str) -> list[str]:
    names = re.findall(r'<Object name="([^"]+)"', document_xml)
    seen: set[str] = set()
    ordered: list[str] = []
    for name in names:
        if name not in seen:
            seen.add(name)
            ordered.append(name)
    return ordered


def _view_provider(name: str) -> str:
    return (
        f'        <ViewProvider name="{name}" expanded="1">\n'
        "            <Properties Count=\"2\">\n"
        '                <Property name="Visibility" type="App::PropertyBool" status="1">\n'
        '                    <Bool value="true"/>\n'
        "                </Property>\n"
        '                <Property name="DisplayMode" type="App::PropertyEnumeration" status="1">\n'
        "                    <Integer value=\"0\"/>\n"
        "                </Property>\n"
        "            </Properties>\n"
        "        </ViewProvider>\n"
    )


def build_gui_document_xml(document_xml: str) -> str:
    names = _object_names(document_xml)
    body = "".join(_view_provider(n) for n in names)
    return (
        "<?xml version='1.0' encoding='utf-8'?>\n"
        '<Document SchemaVersion="1">\n'
        f'    <ViewProviderData Count="{len(names)}">\n'
        f"{body}"
        "    </ViewProviderData>\n"
        f"    {CAMERA_XML}\n"
        "</Document>\n"
    )


def ensure_visible_camera(fcstd_path: Path) -> bool:
    path = Path(fcstd_path)
    if not path.exists():
        return False
    with zipfile.ZipFile(path, "r") as zin:
        names = zin.namelist()
        if "Document.xml" not in names:
            return False
        infos = {info.filename: info for info in zin.infolist()}
        blobs = {name: zin.read(name) for name in names}

    doc_xml = blobs["Document.xml"].decode("utf-8", errors="replace")
    if "GuiDocument.xml" not in names:
        blobs["GuiDocument.xml"] = build_gui_document_xml(doc_xml).encode("utf-8")
        names.append("GuiDocument.xml")
    else:
        gui = blobs["GuiDocument.xml"].decode("utf-8", errors="replace")
        patched, n = re.subn(r'<Camera settings="[^"]*"/>', CAMERA_XML, gui, count=1)
        if n == 0:
            patched = gui.replace("</Document>", f"    {CAMERA_XML}\n</Document>", 1)
        blobs["GuiDocument.xml"] = patched.encode("utf-8")

    tmp = path.with_suffix(".FCStd.tmp")
    with zipfile.ZipFile(tmp, "w") as zout:
        for name in names:
            info = infos.get(name)
            data = blobs[name]
            if info is not None:
                zout.writestr(info, data)
            else:
                zout.writestr(name, data)
    tmp.replace(path)
    return True
