"""Vision model provider (Qwen3-VL via LM Studio). Images stay on this path only."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol, Sequence, Union

from aiva3d.ai.lmstudio_client import LMStudioError, vision_chat_completions
from aiva3d.ai.router import model_for_task
from aiva3d.ai.settings import AISettings, load_settings
from aiva3d.ai.types import ModelTask

VisionChatFn = Callable[..., str]


class VisionProvider(Protocol):
    def analyze_image(self, *, image_path: str, prompt: str) -> Dict[str, Any]: ...


@dataclass
class LMStudioVisionProvider:
    """Qwen3-VL-8B-Instruct (or configured VISION_MODEL) via LM Studio multimodal API."""

    settings: AISettings
    vision_fn: VisionChatFn = vision_chat_completions

    @classmethod
    def from_env(cls, vision_fn: VisionChatFn = vision_chat_completions) -> "LMStudioVisionProvider":
        return cls(settings=load_settings(), vision_fn=vision_fn)

    @property
    def model_id(self) -> str:
        return model_for_task(ModelTask.VISION, self.settings)

    def analyze_image(
        self,
        *,
        image_path: str,
        prompt: str,
        system: Optional[str] = None,
    ) -> Dict[str, Any]:
        path = Path(image_path)
        text = self.vision_fn(
            base_url=self.settings.lmstudio_base_url,
            model=self.model_id,
            text=prompt,
            image_paths=[path],
            system=system,
            temperature=self.settings.vision_temperature,
            max_tokens=self.settings.vision_max_tokens,
        )
        return {
            "model": self.model_id,
            "images": [str(path.resolve())],
            "analysis": text,
        }

    def analyze_images(
        self,
        *,
        image_paths: Sequence[Union[str, Path]],
        prompt: str,
        system: Optional[str] = None,
    ) -> Dict[str, Any]:
        paths = [Path(p) for p in image_paths]
        text = self.vision_fn(
            base_url=self.settings.lmstudio_base_url,
            model=self.model_id,
            text=prompt,
            image_paths=paths,
            system=system,
            temperature=self.settings.vision_temperature,
            max_tokens=self.settings.vision_max_tokens,
        )
        return {
            "model": self.model_id,
            "images": [str(p.resolve()) for p in paths],
            "analysis": text,
        }


def vision_unavailable_message() -> str:
    return (
        "Qwen3-VL integration is routed separately from CadQuery code generation. "
        "Do not send photos to the CadQuery model."
    )


def check_vision_available(provider: Optional[LMStudioVisionProvider] = None) -> None:
    """Ping LM Studio models list (best-effort)."""
    import urllib.error
    import urllib.request

    settings = (provider or LMStudioVisionProvider.from_env()).settings
    url = f"{settings.lmstudio_base_url.rstrip('/')}/v1/models"
    try:
        with urllib.request.urlopen(url, timeout=5.0) as resp:
            resp.read()
    except urllib.error.URLError as exc:
        raise LMStudioError(
            f"LM Studio not reachable at {settings.lmstudio_base_url}: {exc}"
        ) from exc
