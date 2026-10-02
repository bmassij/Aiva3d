"""Reference image storage for reverse-engineering workflows."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

import config

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff"}


def global_reference_dir() -> Path:
    path = config.ROOT / "reference" / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def project_reference_dir(project_id: str) -> Path:
    path = config.PROJECTS_WORK_DIR / project_id / "reference"
    path.mkdir(parents=True, exist_ok=True)
    return path


def reference_dirs(project_id: str) -> Tuple[Path, Path]:
    return global_reference_dir(), project_reference_dir(project_id)


def _is_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_SUFFIXES


def list_reference_images(project_id: str) -> List[Path]:
    seen: set[str] = set()
    out: List[Path] = []
    for directory in reference_dirs(project_id):
        if not directory.is_dir():
            continue
        for path in sorted(directory.iterdir()):
            if path.is_file() and _is_image(path):
                key = str(path.resolve())
                if key not in seen:
                    seen.add(key)
                    out.append(path)
    return out


def save_uploaded_bytes(project_id: str, filename: str, data: bytes) -> Tuple[Path, Path]:
    """Write the same file to global uploads and project reference folders."""
    safe_name = Path(filename).name
    if not safe_name or safe_name.startswith("."):
        raise ValueError("Invalid upload filename")
    global_dir, project_dir = reference_dirs(project_id)
    global_path = global_dir / safe_name
    project_path = project_dir / safe_name
    for target in (global_path, project_path):
        target.write_bytes(data)
    return global_path, project_path


def save_uploads_from_streamlit(project_id: str, uploads: Sequence) -> List[Path]:
    """Persist Streamlit UploadedFile objects; returns project-side paths."""
    saved: List[Path] = []
    for upload in uploads:
        if upload is None:
            continue
        _, project_path = save_uploaded_bytes(project_id, upload.name, upload.getvalue())
        saved.append(project_path)
    return saved


def copy_paths_into_project(project_id: str, paths: Iterable[Path]) -> List[Path]:
    project_dir = project_reference_dir(project_id)
    copied: List[Path] = []
    for src in paths:
        if not src.is_file() or not _is_image(src):
            continue
        dest = project_dir / src.name
        if src.resolve() != dest.resolve():
            shutil.copy2(src, dest)
        copied.append(dest)
    return copied
