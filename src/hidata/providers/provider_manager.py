


import logging
from dataclasses import Field
from pydantic import BaseModel, Field
from typing import Dict
from hidata.providers.provider import (
    Provider,
    ModelInfo,
    DefaultProvider,
    OpenAIProvider,
)
import os
from typing import List
from hidata.constant import SECRET_DIR

logger = logging.getLogger(__name__)


MODELSCOPE_MODELS: List[ModelInfo] = [
    ModelInfo(
        id="Qwen/Qwen3.5-122B-A10B",
        name="Qwen3.5-122B-A10B",
    ),
    ModelInfo(id="ZhipuAI/GLM-5", name="GLM-5"),
]

DASHSCOPE_MODELS: List[ModelInfo] = [
    ModelInfo(id="qwen3-max", name="Qwen3 Max"),
    ModelInfo(
        id="qwen3-235b-a22b-thinking-2507",
        name="Qwen3 235B A22B Thinking",
    ),
    ModelInfo(id="deepseek-v3.2", name="DeepSeek-V3.2"),
]

ALIYUN_CODINGPLAN_MODELS: List[ModelInfo] = [
    ModelInfo(id="qwen3.5-plus", name="Qwen3.5 Plus"),
    ModelInfo(id="glm-5", name="GLM-5"),
    ModelInfo(id="glm-4.7", name="GLM-4.7"),
    ModelInfo(id="MiniMax-M2.5", name="MiniMax M2.5"),
    ModelInfo(id="kimi-k2.5", name="Kimi K2.5"),
    ModelInfo(id="qwen3-max-2026-01-23", name="Qwen3 Max 2026-01-23"),
    ModelInfo(id="qwen3-coder-next", name="Qwen3 Coder Next"),
    ModelInfo(id="qwen3-coder-plus", name="Qwen3 Coder Plus"),
]

OPENAI_MODELS: List[ModelInfo] = [
    ModelInfo(id="gpt-5.2", name="GPT-5.2"),
    ModelInfo(id="gpt-5", name="GPT-5"),
    ModelInfo(id="gpt-5-mini", name="GPT-5 Mini"),
    ModelInfo(id="gpt-5-nano", name="GPT-5 Nano"),
    ModelInfo(id="gpt-4.1", name="GPT-4.1"),
    ModelInfo(id="gpt-4.1-mini", name="GPT-4.1 Mini"),
    ModelInfo(id="gpt-4.1-nano", name="GPT-4.1 Nano"),
    ModelInfo(id="o3", name="o3"),
    ModelInfo(id="o4-mini", name="o4-mini"),
    ModelInfo(id="gpt-4o", name="GPT-4o"),
    ModelInfo(id="gpt-4o-mini", name="GPT-4o Mini"),
]

AZURE_OPENAI_MODELS: List[ModelInfo] = [
    ModelInfo(id="gpt-5-chat", name="GPT-5 Chat"),
    ModelInfo(id="gpt-5-mini", name="GPT-5 Mini"),
    ModelInfo(id="gpt-5-nano", name="GPT-5 Nano"),
    ModelInfo(id="gpt-4.1", name="GPT-4.1"),
    ModelInfo(id="gpt-4.1-mini", name="GPT-4.1 Mini"),
    ModelInfo(id="gpt-4.1-nano", name="GPT-4.1 Nano"),
    ModelInfo(id="gpt-4o", name="GPT-4o"),
    ModelInfo(id="gpt-4o-mini", name="GPT-4o Mini"),
]

MINIMAX_MODELS: List[ModelInfo] = [
    ModelInfo(id="MiniMax-M2.5", name="MiniMax M2.5"),
    ModelInfo(id="MiniMax-M2.5-highspeed", name="MiniMax M2.5 Highspeed"),
]

DEEPSEEK_MODELS: List[ModelInfo] = [
    ModelInfo(id="deepseek-chat", name="DeepSeek Chat"),
    ModelInfo(id="deepseek-reasoner", name="DeepSeek Reasoner"),
]

ANTHROPIC_MODELS: List[ModelInfo] = []

PROVIDER_MODELSCOPE = OpenAIProvider(
    id="modelscope",
    name="ModelScope",
    base_url="https://api-inference.modelscope.cn/v1",
    api_key_prefix="ms",
    models=MODELSCOPE_MODELS,
    freeze_url=True,
)

PROVIDER_DASHSCOPE = OpenAIProvider(
    id="dashscope",
    name="DashScope",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key_prefix="sk",
    models=DASHSCOPE_MODELS,
    freeze_url=True,
)

PROVIDER_ALIYUN_CODINGPLAN = OpenAIProvider(
    id="aliyun-codingplan",
    name="Aliyun Coding Plan",
    base_url="https://coding.dashscope.aliyuncs.com/v1",
    api_key_prefix="sk-sp",
    models=ALIYUN_CODINGPLAN_MODELS,
    freeze_url=True,
)

PROVIDER_LLAMACPP = DefaultProvider(
    id="llamacpp",
    name="llama.cpp (Local)",
    is_local=True,
    require_api_key=False,
)

PROVIDER_MLX = DefaultProvider(
    id="mlx",
    name="MLX (Local, Apple Silicon)",
    is_local=True,
    require_api_key=False,
)

PROVIDER_OPENAI = OpenAIProvider(
    id="openai",
    name="OpenAI",
    base_url="https://api.openai.com/v1",
    api_key_prefix="sk-",
    models=OPENAI_MODELS,
    freeze_url=True,
)

PROVIDER_AZURE_OPENAI = OpenAIProvider(
    id="azure-openai",
    name="Azure OpenAI",
    api_key_prefix="",
    models=AZURE_OPENAI_MODELS,
)

PROVIDER_MINIMAX = OpenAIProvider(
    id="minimax",
    name="MiniMax",
    base_url="https://api.minimax.io/v1",
    api_key_prefix="eyJ",
    models=MINIMAX_MODELS,
    freeze_url=True,
    generate_kwargs={"temperature": 1.0},
)

PROVIDER_DEEPSEEK = OpenAIProvider(
    id="deepseek",
    name="DeepSeek",
    base_url="https://api.deepseek.com",
    api_key_prefix="sk-",
    models=DEEPSEEK_MODELS,
    freeze_url=True,
)


PROVIDER_LMSTUDIO = OpenAIProvider(
    id="lmstudio",
    name="LM Studio",
    base_url="http://localhost:1234/v1",
    require_api_key=False,
    api_key_prefix="",
    support_model_discovery=True,
    generate_kwargs={"max_tokens": None},
)


class ModelSlotConfig(BaseModel):
    provider_id: str = Field(
        ...,
        description="ID of the provider to use for this model slot",
    )
    model: str = Field(
        ...,
        description="ID of the model to use for this model slot",
    )

class ActiveModelsInfo(BaseModel):
    active_llm: ModelSlotConfig | None


class ProviderManager:

    _instance: 'ProviderManager' | None = None

    def __init__(self) -> None:
        self.built_in_providers : Dict[str, Provider] = {}
        self.custom_providers : Dict[str, Provider] = {}
        self.active_model: ModelSlotConfig |  None = None
        self.root_path =  SECRET_DIR / "providers"
        self.builtin_path=self.root_path / "builtin"
        self.custom_path=self.root_path / "custom"
        self._prepare_dis_storage()
        self._init_builtins()

        try:
            self._migrate_legacy_providers()
        except Exception as e:
            logger.warning(f"Failed to migrate legacy providers: {e}")
        self._init_from_storage()
        self.update_local_models()

    
    def _prepare_dis_storage(self) -> None:
        for path in [self.root_path, self.builtin_path, self.custom_path]:
            path.mkdir(parents=True, exist_ok=True)
            try:
                os.chmod(path, 0o700)
            except Exception as e:
                logger.warning(f"Failed to set permissions for {path}: {e}")
                pass
    
    def _init_builtins(self) -> None:
        self._add_builtin(PROVIDER_MODELSCOPE)
        self._add_builtin(PROVIDER_DASHSCOPE)
        self._add_builtin(PROVIDER_ALIYUN_CODINGPLAN)
        self._add_builtin(PROVIDER_OPENAI)
        self._add_builtin(PROVIDER_AZURE_OPENAI)
        self._add_builtin(PROVIDER_MINIMAX)
        self._add_builtin(PROVIDER_DEEPSEEK)
        self._add_builtin(PROVIDER_LMSTUDIO)
        self._add_builtin(PROVIDER_LLAMACPP)
        self._add_builtin(PROVIDER_MLX)
    
    def _add_builtin(self, provider: Provider) -> None:
        self.built_in_providers[provider.id] = provider

    def get_provider(self, provider_id: str) -> Provider | None:
        if provider_id in self.built_in_providers:
            return self.built_in_providers[provider_id]
        elif provider_id in self.custom_providers:
            return self.custom_providers[provider_id]
        else:
            return None

    def get_active_model(self) -> ModelSlotConfig | None:
        return self.active_model
        
    @staticmethod
    def get_instance() -> "ProviderManager":
        """Get the singleton instance of ProviderManager."""
        if ProviderManager._instance is None:
            ProviderManager._instance = ProviderManager()
        return ProviderManager._instance