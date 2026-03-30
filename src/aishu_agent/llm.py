from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

from openai import OpenAI


@dataclass(frozen=True)
class LLMConfig:
    api_key: str
    base_url: Optional[str]
    model: str


def load_llm_config() -> Optional[LLMConfig]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    base_url = os.getenv("OPENAI_BASE_URL", "").strip() or None
    model = os.getenv("OPENAI_MODEL", "").strip() or "gpt-4o-mini"
    return LLMConfig(api_key=api_key, base_url=base_url, model=model)


def make_client(cfg: LLMConfig) -> OpenAI:
    if cfg.base_url:
        return OpenAI(api_key=cfg.api_key, base_url=cfg.base_url)
    return OpenAI(api_key=cfg.api_key)


def chat_once(
    *,
    client: OpenAI,
    model: str,
    messages: list[dict[str, Any]],
) -> str:
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    choice = resp.choices[0]
    content = (choice.message.content or "").strip()
    return content
