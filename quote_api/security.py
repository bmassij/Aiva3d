"""Upload validation and safe temp file handling."""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

from fastapi import HTTPException, UploadFile

from quote_api import config as quote_config

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(name: str) -> str:
    base = Path(name).name
    if not base or base in (".", ".."):
        return "upload.3mf"
    cleaned = _SAFE_NAME.sub("_", base).strip("._")
    return cleaned or "upload.3mf"


def validate_upload(file: UploadFile) -> str:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    safe = sanitize_filename(file.filename)
    if not safe.lower().endswith(".3mf"):
        raise HTTPException(status_code=400, detail="Only .3mf files are accepted")
    return safe


async def read_upload_to_tempfile(file: UploadFile, safe_name: str) -> tuple[Path, int]:
    """Stream upload to a temp file; enforce size limit."""
    suffix = ".3mf" if not safe_name.lower().endswith(".3mf") else ""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix="quote_")
    path = Path(tmp.name)
    total = 0
    try:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            max_bytes = quote_config.QUOTE_MAX_UPLOAD_BYTES
            if total > max_bytes:
                raise HTTPException(
                    status_code=413,
                    detail=f"File exceeds maximum size ({max_bytes} bytes)",
                )
            tmp.write(chunk)
        tmp.close()
        if total == 0:
            path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail="Empty file")
        return path, total
    except HTTPException:
        tmp.close()
        path.unlink(missing_ok=True)
        raise
    except Exception:
        tmp.close()
        path.unlink(missing_ok=True)
        raise
