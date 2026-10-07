"""Quote API tests."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import trimesh
from fastapi.testclient import TestClient

from quote_api.app import app
ROOT = Path(__file__).resolve().parents[1]
HANDLE_3MF = (
    ROOT
    / "projects"
    / "work"
    / "handle_test"
    / "exports"
    / "print"
    / "handle_greep_2helften_2material.3mf"
)

client = TestClient(app)


def _make_3mf_bytes(names: list[str] | None = None) -> bytes:
    scene = trimesh.Scene()
    names = names or ["PART__FILAMENT1_hard"]
    for i, name in enumerate(names):
        box = trimesh.creation.box(extents=(10.0, 10.0, 10.0))
        t = np.eye(4)
        t[0, 3] = i * 12.0
        scene.add_geometry(box, geom_name=name, transform=t)
    return scene.export(file_type="3mf")


def test_health() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_materials_machines_pricing() -> None:
    assert client.get("/materials").status_code == 200
    assert client.get("/machines").status_code == 200
    assert client.get("/pricing/profiles").status_code == 200


def test_quote_upload() -> None:
    data = _make_3mf_bytes()
    r = client.post(
        "/quote",
        files={"file": ("test.3mf", data, "application/vnd.ms-package.3dmanufacturing-3dmodel+xml")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["weight_g"] > 0
    assert body["sale_price"] > body["cost_price"] or body["cost_price"] == 0


def test_estimate_upload() -> None:
    data = _make_3mf_bytes(["A__FILAMENT1_pla", "B__FILAMENT2_varishore"])
    r = client.post(
        "/estimate",
        files={"file": ("dual.3mf", data, "application/octet-stream")},
    )
    assert r.status_code == 200
    assert r.json()["mode"] == "estimate"
    assert r.json()["object_count"] == 2


def test_invalid_extension() -> None:
    r = client.post("/quote", files={"file": ("x.txt", b"hello", "text/plain")})
    assert r.status_code == 400


def test_empty_file() -> None:
    r = client.post(
        "/quote",
        files={"file": ("empty.3mf", b"", "application/octet-stream")},
    )
    assert r.status_code == 400


def test_invalid_3mf() -> None:
    r = client.post(
        "/quote",
        files={"file": ("bad.3mf", b"notzip", "application/octet-stream")},
    )
    assert r.status_code == 400


def test_oversized_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("quote_api.config.QUOTE_MAX_UPLOAD_BYTES", 100)
    big = b"x" * 200
    r = client.post(
        "/quote",
        files={"file": ("big.3mf", big, "application/octet-stream")},
    )
    assert r.status_code == 413


def test_pdf_no_internal_cost() -> None:
    data = _make_3mf_bytes()
    r = client.post(
        "/quote/pdf",
        files={"file": ("test.3mf", data, "application/octet-stream")},
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    text = r.content.decode("latin-1", errors="ignore")
    assert "kostprijs" not in text.lower()
    assert "marge" not in text.lower()
    assert "cost_price" not in text


def test_pricing_margin() -> None:
    data = _make_3mf_bytes()
    r = client.post("/quote", files={"file": ("t.3mf", data, "application/octet-stream")})
    body = r.json()
    expected = round(body["cost_price"] * (1 + body["margin_percent"] / 100), 2)
    assert body["sale_price"] == expected


@pytest.mark.integration
def test_handle_3mf_chain_if_present() -> None:
    if not HANDLE_3MF.is_file():
        pytest.skip(f"fixture not built: {HANDLE_3MF}")
    with HANDLE_3MF.open("rb") as f:
        r = client.post(
            "/quote",
            files={"file": (HANDLE_3MF.name, f.read(), "application/octet-stream")},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["object_count"] >= 2
    assert body["weight_g"] > 0
    assert body["sale_price"] > 0
