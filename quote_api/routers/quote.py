from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import Response

from quote_api.pdf.customer import render_customer_pdf
from quote_api.security import read_upload_to_tempfile, validate_upload
from quote_api.service import analyze_file

router = APIRouter(tags=["quote"])


async def _process_upload(
    file: UploadFile,
    mode: str,
    quantity: int,
    material_profile: str | None,
    machine_profile: str | None,
    pricing_profile: str | None,
):
    safe = validate_upload(file)
    path, _size = await read_upload_to_tempfile(file, safe)
    try:
        return analyze_file(
            path,
            safe,
            mode=mode,
            quantity=quantity,
            material_profile=material_profile,
            machine_profile=machine_profile,
            pricing_profile=pricing_profile,
        )
    finally:
        Path(path).unlink(missing_ok=True)


@router.post("/estimate")
async def estimate(
    file: UploadFile = File(...),
    quantity: int = Form(1),
    material_profile: str | None = Form(None),
    machine_profile: str | None = Form(None),
    pricing_profile: str | None = Form(None),
):
    return await _process_upload(
        file,
        "estimate",
        quantity,
        material_profile,
        machine_profile,
        pricing_profile,
    )


@router.post("/quote")
async def quote(
    file: UploadFile = File(...),
    quantity: int = Form(1),
    material_profile: str | None = Form(None),
    machine_profile: str | None = Form(None),
    pricing_profile: str | None = Form(None),
):
    return await _process_upload(
        file,
        "quote",
        quantity,
        material_profile,
        machine_profile,
        pricing_profile,
    )


@router.post("/quote/pdf")
async def quote_pdf(
    file: UploadFile = File(...),
    quantity: int = Form(1),
    material_profile: str | None = Form(None),
    machine_profile: str | None = Form(None),
    pricing_profile: str | None = Form(None),
    notes: str = Form(""),
):
    safe = validate_upload(file)
    path, _size = await read_upload_to_tempfile(file, safe)
    try:
        analysis = analyze_file(
            path,
            safe,
            mode="quote",
            quantity=quantity,
            material_profile=material_profile,
            machine_profile=machine_profile,
            pricing_profile=pricing_profile,
        )
    finally:
        Path(path).unlink(missing_ok=True)
    quote_number = f"Q-{uuid.uuid4().hex[:8].upper()}"
    pdf_bytes = render_customer_pdf(analysis, quote_number=quote_number, notes=notes)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{quote_number}.pdf"'},
    )
