"""模型与消息格式化器工厂。

根据当前激活的 LLM 提供商构造 ``ChatModel`` 与 ``Formatter``，并对格式化器做
工具结果中的文件块、思考块、``extra_content``（如 Gemini thought_signature）等
兼容处理。
"""

import logging
from typing import Sequence, Tuple, Type, Any
from functools import wraps

from agentscope.formatter import FormatterBase, OpenAIChatFormatter
from agentscope.model import ChatModelBase, OpenAIChatModel
from agentscope.message import Msg
import agentscope

try:
    from agentscope.formatter import AnthropicChatFormatter
    from agentscope.model import AnthropicChatModel
except ImportError:  # pragma: no cover — 未安装 Anthropic 依赖时的兼容占位
    AnthropicChatFormatter = None
    AnthropicChatModel = None

from hidata.agent.utils.tool_message_utils import _sanitize_tool_messages
from hidata.providers import ProviderManager
from hidata.providers.retry_chat_model import RetryChatModel
from hidata.token_usage import TokenRecordingModelWrapper

logger = logging.getLogger(__name__)

# 对话模型类 → 对应格式化器类（无映射时回退到 OpenAI 格式化器）
_CHAT_MODEL_FORMATTER_MAP: dict[Type[ChatModelBase], Type[FormatterBase]] = {
    OpenAIChatModel: OpenAIChatFormatter,
}

if AnthropicChatModel is not None and AnthropicChatFormatter is not None:
    _CHAT_MODEL_FORMATTER_MAP[AnthropicChatModel] = AnthropicChatFormatter



def _get_formatter_for_chat_model(
    chat_model_class: Type[ChatModelBase],
) -> Type[FormatterBase]:
    """根据对话模型类返回应使用的格式化器类。

    Args:
        chat_model_class: 对话模型类

    Returns:
        对应的格式化器类；无映射时默认为 ``OpenAIChatFormatter``。
    """
    return _CHAT_MODEL_FORMATTER_MAP.get(
        chat_model_class,
        OpenAIChatFormatter,
    )


def create_model_and_formatter() -> Tuple[ChatModelBase, FormatterBase]:
    """创建模型与格式化器实例（工厂入口）。

    通过 ``ProviderManager`` 取得当前激活的对话模型，再为其构造带文件块增强的
    格式化器；模型外层依次包装：Token 用量记录、瞬时 API 错误的重试。

    Returns:
        ``(wrapped_model, formatter)``：已包装的模型实例与格式化器实例。

    Example:
        >>> model, formatter = create_model_and_formatter()
    """
    model = ProviderManager.get_active_chat_model()

    formatter = _create_formatter_instance(model.__class__)

    # 对瞬时性 LLM API 错误做重试；内层先记录各 provider 的 token 用量
    provider_id = ProviderManager.get_instance().get_active_model().provider_id
    wrapped_model = TokenRecordingModelWrapper(provider_id, model)
    wrapped_model = RetryChatModel(wrapped_model)

    return wrapped_model, formatter

def _create_file_block_support_formatter(
    base_formatter_class: Type[FormatterBase],
) -> Type[FormatterBase]:
    """基于给定格式化器类，派生出「支持工具结果中的 file 块」的子类。

    AgentScope 原生不在工具输出里支持 ``file`` 类型块；此处通过子类在
    ``convert_tool_result_to_string`` 中解析文件路径/URL，并拼成可读文本与多模态数据。

    Args:
        base_formatter_class: 要扩展的基类格式化器

    Returns:
        增强后的格式化器类（非实例）。
    """

    class FileBlockSupportFormatter(base_formatter_class):
        """在工具结果中支持 file 块，并修正与 OpenAI 兼容 API 相关的消息形态。"""

        # pylint: disable=too-many-branches
        async def _format(self, msgs):
            """重写：清洗 tool 消息、保留 thinking 与 ``extra_content``（如 Gemini）。

            - 先规范化工具消息配对，避免 OpenAI 兼容后端因 tool 消息不成对而 400/500。
            - 从 ``thinking`` 块提取 ``reasoning_content``（基类可能丢弃）。
            - 将 ``tool_use`` 上的 ``extra_content``（如 ``thought_signature``）
              透传到发往 API 的请求体。
            """
            msgs = _sanitize_tool_messages(msgs)

            # 从 assistant 消息中收集 thinking 文本与 tool_use 的 extra_content
            reasoning_contents = {}
            extra_contents: dict[str, Any] = {}
            for msg in msgs:
                if msg.role != "assistant":
                    continue
                for block in msg.get_content_blocks():
                    if block.get("type") == "thinking":
                        thinking = block.get("thinking", "")
                        if thinking:
                            reasoning_contents[id(msg)] = thinking
                        break
                for block in msg.get_content_blocks():
                    if (
                        block.get("type") == "tool_use"
                        and "extra_content" in block
                    ):
                        extra_contents[block["id"]] = block["extra_content"]

            messages = await super()._format(msgs)

            # 将 tool_call id → extra_content 写回格式化后的 tool_calls
            if extra_contents:
                for message in messages:
                    for tc in message.get("tool_calls", []):
                        ec = extra_contents.get(tc.get("id"))
                        if ec:
                            tc["extra_content"] = ec

            # 按序把 thinking 注入为 reasoning_content（仅当格式化前后 assistant 条数一致）
            if reasoning_contents:
                in_assistant = [m for m in msgs if m.role == "assistant"]
                out_assistant = [
                    m for m in messages if m.get("role") == "assistant"
                ]
                if len(in_assistant) != len(out_assistant):
                    logger.warning(
                        "格式化前后 assistant 消息条数不一致（前 %d 后 %d），"
                        "跳过 reasoning_content 注入。",
                        len(in_assistant),
                        len(out_assistant),
                    )
                else:
                    for in_msg, out_msg in zip(
                        in_assistant,
                        out_assistant,
                    ):
                        reasoning = reasoning_contents.get(id(in_msg))
                        if reasoning:
                            out_msg["reasoning_content"] = reasoning

            return _strip_top_level_message_name(messages)

        @staticmethod
        def convert_tool_result_to_string(
            output: str | list[dict],
        ) -> tuple[str, Sequence[Tuple[str, dict]]]:
            """在父类基础上增加对 ``file`` 类型块的处理。

            策略：优先走父类；若因 ``Unsupported block type: file`` 失败，再逐块解析。

            Args:
                output: 工具返回，字符串或块列表

            Returns:
                ``(文本表示, 多模态数据列表)``，与父类约定一致。
            """
            if isinstance(output, str):
                return output, []

            # 先尝试父类（覆盖常见块类型）
            try:
                return base_formatter_class.convert_tool_result_to_string(
                    output,
                )
            except ValueError as e:
                if "Unsupported block type: file" not in str(e):
                    raise

                # 含 file 块：拆成可读说明 + (path/url, block) 供多模态上传
                textual_output = []
                multimodal_data = []

                for block in output:
                    if not isinstance(block, dict) or "type" not in block:
                        raise ValueError(
                            f"Invalid block: {block}, "
                            "expected a dict with 'type' key",
                        ) from e

                    if block["type"] == "file":
                        file_path = block.get("path", "") or block.get(
                            "url",
                            "",
                        )
                        file_name = block.get("name", file_path)

                        textual_output.append(
                            f"The returned file '{file_name}' "
                            f"can be found at: {file_path}",
                        )
                        multimodal_data.append((file_path, block))
                    else:
                        # 其它块类型仍委托父类单块转换
                        (
                            text,
                            data,
                        ) = base_formatter_class.convert_tool_result_to_string(
                            [block],
                        )
                        textual_output.append(text)
                        multimodal_data.extend(data)

                if len(textual_output) == 0:
                    return "", multimodal_data
                elif len(textual_output) == 1:
                    return textual_output[0], multimodal_data
                else:
                    return (
                        "\n".join("- " + _ for _ in textual_output),
                        multimodal_data,
                    )

    # 动态类名便于日志与调试区分
    FileBlockSupportFormatter.__name__ = (
        f"FileBlockSupport{base_formatter_class.__name__}"
    )
    return FileBlockSupportFormatter


def _strip_top_level_message_name(
    messages: list[dict],
) -> list[dict]:
    """去掉 OpenAI 风格消息顶层的 ``name`` 字段。

    部分严格的 OpenAI 兼容网关会拒绝 ``messages[*].name``（尤其 assistant/tool 轮次），
    导致后续请求 400/500。此处仅移除顶层 ``name``，不改变 function/tool 名称字段。
    """
    for message in messages:
        message.pop("name", None)
    return messages


def _create_formatter_instance(chat_model_class: Type[ChatModelBase]) -> FormatterBase:
    """为指定对话模型类创建格式化器实例。

    在映射到的基类格式化器上套用 ``_create_file_block_support_formatter``，
    使工具结果中的 ``file`` 块能被正确转成文本并附带多模态元数据。
    """
    base_formatter_class = _get_formatter_for_chat_model(chat_model_class)
    formatter_class = _create_file_block_support_formatter(
        base_formatter_class,
    )
    return formatter_class()


__all__ = [
    "create_model_and_formatter",
]
