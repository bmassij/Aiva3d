"""Minimal OpenAI-compatible client for LM Studio."""

from __future__ import annotations

import base64
import json
import mimetypes
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union


class LMStudioError(RuntimeError):
    """LM Studio request failed."""


@dataclass
class ChatMessage:
    role: str
    content: str


def chat_completions(
    *,
    base_url: str,
    model: str,
    messages: Sequence[ChatMessage],
    temperature: float = 0.2,
    max_tokens: int = 1024,
    stop: Optional[Sequence[str]] = None,
    timeout_s: float = 120.0,
) -> str:
    url = f"{base_url.rstrip('/')}/v1/chat/completions"
    payload: Dict[str, Any] = {
        "model": model,
        "messages": [{"role": m.role, "content": m.content} for m in messages],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    if stop:
        payload["stop"] = list(stop)

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise LMStudioError(
            f"Cannot reach LM Studio at {base_url}: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise LMStudioError("LM Studio returned non-JSON response") from exc

    try:
        return str(body["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as exc:
        raise LMStudioError(f"Unexpected LM Studio response shape: {body!r}") from exc


def image_file_to_data_url(path: Path) -> str:
    """Encode a local image for OpenAI-style vision chat payloads."""
    path = path.resolve()
    if not path.is_file():
        raise LMStudioError(f"Image not found: {path}")
    mime, _ = mimetypes.guess_type(str(path))
    if not mime or not mime.startswith("image/"):
        mime = "image/jpeg"
    raw = path.read_bytes()
    b64 = base64.standard_b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{b64}"


def vision_chat_completions(
    *,
    base_url: str,
    model: str,
    text: str,
    image_paths: Sequence[Union[str, Path]],
    system: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 4096,
    timeout_s: float = 300.0,
) -> str:
    """
    Multimodal chat (Qwen3-VL via LM Studio).

    ``image_paths`` are sent in order; label them in ``text`` (image 1, image 2, …).
    """
    content: List[Dict[str, Any]] = [{"type": "text", "text": text}]
    for p in image_paths:
        url = image_file_to_data_url(Path(p))
        content.append({"type": "image_url", "image_url": {"url": url}})

    messages: List[Dict[str, Any]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": content})

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    url = f"{base_url.rstrip('/')}/v1/chat/completions"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise LMStudioError(
            f"Cannot reach LM Studio at {base_url}: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise LMStudioError("LM Studio returned non-JSON response") from exc

    try:
        return str(body["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as exc:
        raise LMStudioError(f"Unexpected LM Studio response shape: {body!r}") from exc
