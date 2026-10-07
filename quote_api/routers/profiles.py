from fastapi import APIRouter

from quote_api.profiles.loader import load_machines, load_materials, load_pricing_profiles

router = APIRouter(tags=["profiles"])


@router.get("/materials")
def list_materials() -> dict:
    return {
        "ok": True,
        "note": "DEVELOPMENT DEFAULT — replace before Crooijmans production.",
        "profiles": [p.model_dump() for p in load_materials()],
    }


@router.get("/machines")
def list_machines() -> dict:
    return {
        "ok": True,
        "note": "DEVELOPMENT DEFAULT — replace before Crooijmans production.",
        "profiles": [p.model_dump() for p in load_machines()],
    }


@router.get("/pricing/profiles")
def list_pricing() -> dict:
    return {
        "ok": True,
        "note": "DEVELOPMENT DEFAULT — replace before Crooijmans production.",
        "profiles": [p.model_dump() for p in load_pricing_profiles()],
    }
