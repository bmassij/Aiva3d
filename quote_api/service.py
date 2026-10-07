"""Orchestrate print_core + pricing."""

from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException

from print_core import inspect_3mf
from print_core.errors import Empty3MFError, EmptyFileError, Invalid3MFError, PrintCoreError

from quote_api.config import CURRENCY
from quote_api.engine.pricing import build_quote_analysis
from quote_api.schemas import QuoteAnalysis


def analyze_file(
    path: Path,
    filename: str,
    *,
    mode: str,
    quantity: int,
    material_profile: str | None,
    machine_profile: str | None,
    pricing_profile: str | None,
) -> QuoteAnalysis:
    try:
        core = inspect_3mf(path, filename=filename)
    except EmptyFileError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (Invalid3MFError, Empty3MFError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PrintCoreError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        return build_quote_analysis(
            core=core,
            mode=mode,
            quantity=max(quantity, 1),
            material_profile_id=material_profile,
            machine_profile_id=machine_profile,
            pricing_profile_id=pricing_profile,
            currency=CURRENCY,
        )
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
