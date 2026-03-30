from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


DEFAULT_SYSTEM_PROMPT = (
    "你是一个有帮助、简洁、可靠的中文助手。"
    "如果用户的问题信息不足，请先提出澄清问题。"
)


@dataclass
class ChatSession:
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    messages: list[dict[str, Any]] = field(default_factory=list)

    def reset(self) -> None:
        self.messages = [{"role": "system", "content": self.system_prompt}]

    def ensure_started(self) -> None:
        if not self.messages:
            self.reset()

    def add_user(self, text: str) -> None:
        self.ensure_started()
        self.messages.append({"role": "user", "content": text})

    def add_assistant(self, text: str) -> None:
        self.ensure_started()
        self.messages.append({"role": "assistant", "content": text})
