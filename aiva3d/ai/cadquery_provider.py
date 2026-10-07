"""Qwen2.5-Coder-7B-CadQuery provider (LM Studio, text-only)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Protocol, Sequence

from aiva3d.ai.lmstudio_client import ChatMessage, LMStudioError, chat_completions
from aiva3d.ai.settings import AISettings, CADQUERY_SYSTEM_PROMPT, load_settings
from aiva3d.ai.types import CadSpecification


class ChatFn(Protocol):
    def __call__(
        self,
        *,
        base_url: str,
        model: str,
        messages: Sequence[ChatMessage],
        temperature: float,
        max_tokens: int,
        stop: Optional[Sequence[str]],
    ) -> str: ...


@dataclass
class CadQueryProvider:
    """Generate CadQuery Python from a structured CAD specification."""

    settings: AISettings
    chat_fn: ChatFn = chat_completions

    @classmethod
    def from_env(cls, chat_fn: ChatFn = chat_completions) -> "CadQueryProvider":
        return cls(settings=load_settings(), chat_fn=chat_fn)

    @property
    def model_id(self) -> str:
        return self.settings.cadquery_model

    @property
    def system_prompt(self) -> str:
        return CADQUERY_SYSTEM_PROMPT

    @property
    def stop_token(self) -> str:
        return self.settings.cadquery_stop_token

    def build_user_message(self, spec: CadSpecification) -> str:
        return spec.to_prompt_text()

    def generate_code(
        self,
        spec: CadSpecification,
        *,
        extra_user_hint: str = "",
    ) -> str:
        user = self.build_user_message(spec)
        if extra_user_hint.strip():
            user = f"{user}\n\nAdditional notes:\n{extra_user_hint.strip()}"
        messages = [
            ChatMessage(role="system", content=self.system_prompt),
            ChatMessage(role="user", content=user),
        ]
        stop = [self.stop_token] if self.stop_token else None
        try:
            return self.chat_fn(
                base_url=self.settings.lmstudio_base_url,
                model=self.model_id,
                messages=messages,
                temperature=self.settings.cadquery_temperature,
                max_tokens=self.settings.cadquery_max_tokens,
                stop=stop,
            )
        except LMStudioError:
            raise

    def generate_code_or_raise(self, spec: CadSpecification) -> str:
        return self.generate_code(spec)


def mock_chat_response(text: str) -> ChatFn:
    """Test helper: return fixed model output without LM Studio."""

    def _chat(**kwargs) -> str:  # type: ignore[no-untyped-def]
        return text

    return _chat
