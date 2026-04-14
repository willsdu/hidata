from agentscope.model import OpenAIChatModel


class OpenAIChatModelCompat(OpenAIChatModel):
    """OpenAIChatModel with robust parsing for malformed tool-call chunks
       and transparent ``extra_content`` (Gemini thought_signature) relay."""