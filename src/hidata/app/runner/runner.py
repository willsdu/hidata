import logging
import os
from typing import Any

from agentscope_runtime.engine.runner import Runner
from agentscope.memory import MemoryBase
from openai import OpenAI

logger = logging.getLogger(__name__)


class AgentRunner(Runner):
    def __init__(self) -> None:
        super().__init__()
        # Use the runtime's "text" adapter so our query_handler can simply
        # return text (or stream text deltas) without depending on AgentScope Msg.
        self.framework_type = "text"
        self._chat_manager = None  # Store chat_manager reference
        self._mcp_manager = None  # MCP client manager for hot-reload
        self.memory_manager: MemoryBase | None = None

    def _make_openai_client(self) -> tuple[OpenAI, str]:
        api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")

        base_url = (os.getenv("OPENAI_BASE_URL") or "").strip() or None
        model = (os.getenv("OPENAI_MODEL") or "").strip() or "gpt-4o-mini"

        if base_url:
            return OpenAI(api_key=api_key, base_url=base_url), model
        return OpenAI(api_key=api_key), model

    @staticmethod
    def _agent_input_to_openai_messages(agent_input: list[Any]) -> list[dict[str, str]]:
        """Convert AgentRequest.input (runtime protocol) to OpenAI messages."""
        messages: list[dict[str, str]] = []
        for item in agent_input or []:
            if not isinstance(item, dict):
                continue
            if item.get("type") != "message":
                continue
            role = (item.get("role") or "").strip() or "user"
            blocks = item.get("content") or []
            parts: list[str] = []
            if isinstance(blocks, list):
                for b in blocks:
                    if isinstance(b, dict) and b.get("type") == "text":
                        t = (b.get("text") or "").strip()
                        if t:
                            parts.append(t)
            content = "\n".join(parts).strip()
            if not content:
                continue
            if role not in ("system", "user", "assistant"):
                role = "user"
            messages.append({"role": role, "content": content})
        return messages

    async def query_handler(self, request, response, **kwargs):  # pylint: disable=unused-argument
        """Runtime query handler for `/api/agent/process`.

        We return plain text; AgentScope Runtime will adapt it into SSE events.
        """
        client, default_model = self._make_openai_client()
        model = getattr(request, "model", None) or default_model

        # request.input is a list of Message objects; model_dump() yields dicts.
        agent_input = []
        try:
            agent_input = [m.model_dump() for m in (request.input or [])]
        except Exception:
            # Fallback: try raw attribute
            agent_input = getattr(request, "input", []) or []

        messages = self._agent_input_to_openai_messages(agent_input)
        if not messages:
            return "（空输入）"

        # If caller didn't provide system message, add a default one.
        if messages[0].get("role") != "system":
            messages.insert(
                0,
                {
                    "role": "system",
                    "content": "你是一个有帮助、简洁、可靠的中文助手。如果信息不足，请先提出澄清问题。",
                },
            )

        resp = client.chat.completions.create(model=model, messages=messages)
        return ((resp.choices[0].message.content or "").strip()) or "（模型未返回内容）"