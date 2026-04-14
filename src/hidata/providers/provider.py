from abc import ABC, abstractmethod
from typing import Dict, List, Type, Any
from pydantic import BaseModel, Field

from agentscope.model import ChatModelBase

class ModelInfo(BaseModel):
    id: str = Field(..., description="Model identifier used in API calls")
    name: str = Field(..., description="Human-readable model name")

class ProviderInfo(BaseModel):
    id: str = Field(..., description="Provider identifier used in API calls")
    name: str = Field(..., description="Human-readable provider name")
    base_url: str = Field(..., description="Base URL of the provider")
    api_key:str = Field(..., description="API key of the authentication")
    chat_model:str=Field(
        default="OpenAIChatModel",
        description="Chat model class to use for this provider",
    )
    pre_defined_models: List[ModelInfo] = Field(
        default_factory=list,
        description="List of pre-defined models",
    )
    extra_models: List[ModelInfo] = Field(
        default_factory=list,
        description="List of user-added models (not fetched from provider)",
    )
    api_key_prefix: str = Field(
        default="",
        description="Expected prefix for the API key (e.g., 'sk-')",
    )
    is_local: bool = Field(
        default=False,
        description="Whether this provider is for a local hosting platform",
    )
    freeze_url: bool = Field(
        default=False,
        description="Whether the base_url should be frozen (not editable)",
    )
    require_api_key: bool = Field(
        default=True,
        description="Whether this provider requires an API key",
    )
    is_custom: bool = Field(
        default=False,
        description=("Whether this provider is user-created (not built-in)."),
    )
    support_model_discovery: bool = Field(
        default=False,
        description=(
            "Whether this provider supports fetching available models"
            " from the provider's API"
        ),
    )
    generate_kwargs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Generation parameters for agentscope chat models.",
    )





class Provider(ProviderInfo, ABC):
    """Represents a provider instance with its configuration."""

    @abstractmethod
    async def check_connection(self, timeout: float = 5) -> tuple[bool, str]:
        """Check if the provider is reachable with the current config."""

    @abstractmethod
    async def fetch_models(self, timeout: float = 5) -> List[ModelInfo]:
        """Fetch the list of available models from the provider."""
    @abstractmethod
    async def check_model_connection(
        self,
        model_id: str,
        timeout: float = 5,  # pylint: disable=unused-argument
    ) -> tuple[bool, str]:
        """Check if a specific model is reachable/usable."""

    async def add_model(
        self, 
        model_info: ModelInfo,
        target:str="extra_models",
         timeout: float = 10,  # pylint: disable=unused-argument
     ) -> tuple[bool, str]:
        """Add a model to the provider."""
        if model_info.id in {
            model.id for model in self.models +self.extra_models
        }:
            return False, f"Model {model_info.id} already exists"
        if target == "extra_models":
            self.extra_models.append(model_info)
        elif target == "models":
            self.models.append(model_info)
        else:
            return False, f"Invalid target: {target} for adding model"
        return True, ""

class DefaultProvider(Provider):
    """Default provider implementation."""

    async def fetch_models(self, timeout: float = 5) -> List[ModelInfo]:
        return self.models

    def get_chat_model_instance(self, model_id: str) -> ChatModelBase:
        raise NotImplementedError(
            "DefaultProvider does not implement chat model",
        )