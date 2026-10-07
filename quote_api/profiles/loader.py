"""Load DEVELOPMENT DEFAULT profile JSON."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from quote_api.schemas import MachineProfile, MaterialProfile, PricingProfile

_PROFILES_DIR = Path(__file__).resolve().parent


@lru_cache(maxsize=1)
def load_materials() -> list[MaterialProfile]:
    data = json.loads((_PROFILES_DIR / "materials.json").read_text(encoding="utf-8"))
    return [MaterialProfile.model_validate(p) for p in data["profiles"]]


@lru_cache(maxsize=1)
def load_machines() -> list[MachineProfile]:
    data = json.loads((_PROFILES_DIR / "machines.json").read_text(encoding="utf-8"))
    return [MachineProfile.model_validate(p) for p in data["profiles"]]


@lru_cache(maxsize=1)
def load_pricing_profiles() -> list[PricingProfile]:
    data = json.loads((_PROFILES_DIR / "pricing.json").read_text(encoding="utf-8"))
    return [PricingProfile.model_validate(p) for p in data["profiles"]]


def get_material(profile_id: str | None) -> MaterialProfile:
    profiles = load_materials()
    if profile_id:
        for p in profiles:
            if p.id == profile_id:
                return p
        raise KeyError(f"unknown material profile: {profile_id}")
    return profiles[0]


def get_machine(profile_id: str | None) -> MachineProfile:
    profiles = load_machines()
    if profile_id:
        for p in profiles:
            if p.id == profile_id:
                return p
        raise KeyError(f"unknown machine profile: {profile_id}")
    return profiles[0]


def get_pricing(profile_id: str | None) -> PricingProfile:
    profiles = load_pricing_profiles()
    if profile_id:
        for p in profiles:
            if p.id == profile_id:
                return p
        raise KeyError(f"unknown pricing profile: {profile_id}")
    return profiles[0]
