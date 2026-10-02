"""
Future AI layer hook: map natural-language intent to structured parameters.

Not an LLM implementation — only typed interfaces for a later orchestrator.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

import cadquery as cq

from cad.utilities.parameters import ParametricModelMeta


@dataclass
class CADBuildRequest:
    """Structured request produced by a future NL → parameter translator."""

    template_id: str
    parameters: Dict[str, float]
    metadata: Optional[ParametricModelMeta] = None
    notes: str = ""


@dataclass
class CADBuildResult:
    workpiece: cq.Workplane
    metadata: ParametricModelMeta
    validation_passed: bool = False


# Registry: template_id -> callable(**kwargs) -> Workplane
TemplateRegistry = Dict[str, Callable[..., cq.Workplane]]


def register_template(registry: TemplateRegistry, template_id: str, builder: Callable[..., cq.Workplane]) -> None:
    registry[template_id] = builder


def build_from_request(request: CADBuildRequest, registry: TemplateRegistry) -> CADBuildResult:
    if request.template_id not in registry:
        raise KeyError(f"Unknown template_id: {request.template_id}")
    builder = registry[request.template_id]
    workpiece = builder(**request.parameters)
    meta = request.metadata or ParametricModelMeta(name=request.template_id)
    return CADBuildResult(workpiece=workpiece, metadata=meta, validation_passed=True)
