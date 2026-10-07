"""Session state for live CAD iteration with last-valid-model preservation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import cadquery as cq


@dataclass
class BuiltModel:
    hard_core: cq.Workplane
    soft_outer: cq.Workplane
    reference_metal: Optional[cq.Workplane] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelSession:
    last_valid: Optional[BuiltModel] = None
    comparison: Optional[BuiltModel] = None
    last_error: Optional[str] = None
    build_count: int = 0
    history: List[str] = field(default_factory=list)

    def apply_build(self, result: BuiltModel, note: str = "") -> None:
        self.last_valid = result
        self.last_error = None
        self.build_count += 1
        if note:
            self.history.append(note)

    def apply_failure(self, error: str) -> None:
        self.last_error = error
        self.history.append(f"FAILED: {error}")

    def save_comparison_snapshot(self) -> None:
        if self.last_valid is not None:
            self.comparison = BuiltModel(
                hard_core=self.last_valid.hard_core,
                soft_outer=self.last_valid.soft_outer,
                reference_metal=self.last_valid.reference_metal,
                metadata=dict(self.last_valid.metadata),
            )

    def display_parts(
        self,
        model: Optional[BuiltModel] = None,
        *,
        show_reference_metal: bool = True,
    ) -> List[Tuple]:
        from projects.work.handle_test.materials import HARD_PRINT, METAL_EXISTING, SOFT_PRINT

        target = model if model is not None else self.last_valid
        if target is None:
            return []
        parts: List[Tuple] = []
        if show_reference_metal and target.reference_metal is not None:
            parts.append(
                (
                    target.reference_metal,
                    METAL_EXISTING["color"],
                    METAL_EXISTING["label"],
                    1.0,
                )
            )
            parts.append(
                (
                    target.soft_outer,
                    SOFT_PRINT["color"],
                    SOFT_PRINT["label"],
                    0.42,
                )
            )
            parts.append(
                (
                    target.hard_core,
                    HARD_PRINT["color"],
                    HARD_PRINT["label"],
                    0.98,
                )
            )
        else:
            parts.extend(
                [
                    (
                        target.hard_core,
                        HARD_PRINT["color"],
                        HARD_PRINT["label"],
                        0.98,
                    ),
                    (
                        target.soft_outer,
                        SOFT_PRINT["color"],
                        SOFT_PRINT["label"],
                        0.42,
                    ),
                ]
            )
        return parts
