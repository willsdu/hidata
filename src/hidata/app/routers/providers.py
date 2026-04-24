from hidata.providers.provider_manager import ProviderManager
from fastapi import APIRouter, Depends, Request, Body, HTTPException
from typing import List
from hidata.providers.provider import ModelInfo, ProviderInfo
from typing import Optional, Literal
from pydantic import BaseModel, Field


ChatModelName = Literal["OpenAIChatModel", "AnthropicChatModel"]

router = APIRouter(prefix="/providers", tags=["models"])

def get_provider_manager(request: Request) -> ProviderManager:
    """Get the provider manager from app state.

    Args:
        request: FastAPI request object
    """
    provider_manager = getattr(request.app.state, "provider_manager", None)
    if provider_manager is None:
        provider_manager = ProviderManager.get_instance()
    return provider_manager

class ProviderConfigRequest(BaseModel):
    name: Optional[str] = Field(
        default=None,
        description="Display name of the provider",
    )
    api_key: Optional[str] = Field(default=None)
    base_url: Optional[str] = Field(default=None)
    chat_model: Optional[ChatModelName] = Field(
        default=None,
        description="Chat model class name for protocol selection",
    )
    generate_kwargs: Optional[dict] = Field(
        default=None,
        description=(
            "Configuration in json format, will be expanded "
            "and passed to generation calls "
            "(e.g., openai.chat.completions, anthropic.messages)."
        ),
    )


class ProviderCreateRequest(BaseModel):
    """Create a custom provider (OpenAI-compatible or local placeholder)."""

    id: str = Field(
        ...,
        min_length=1,
        description="Desired provider id; may be auto-suffixed on conflict.",
    )
    name: str = Field(..., min_length=1)
    base_url: str = Field(default="")
    api_key: str = Field(default="")
    chat_model: ChatModelName = Field(default="OpenAIChatModel")
    models: List[ModelInfo] = Field(
        default_factory=list,
        description="Pre-defined model list (optional)",
    )
    extra_models: List[ModelInfo] = Field(default_factory=list)
    is_local: bool = Field(
        default=False,
        description="If true, create a DefaultProvider (local) entry.",
    )
    require_api_key: bool = Field(default=True)
    freeze_url: bool = Field(default=False)
    support_model_discovery: bool = Field(default=False)
    generate_kwargs: dict = Field(default_factory=dict)


@router.get(
    "/",
    response_model=List[ProviderInfo],
    summary="List all providers",
)
async def list_all_providers(
    manager: ProviderManager = Depends(get_provider_manager),
) -> List[ProviderInfo]:
    return await manager.list_provider_info()


@router.get(
    "/{provider_id}",
    response_model=ProviderInfo,
    summary="Get a single provider by id",
)
async def get_provider(
    provider_id: str,
    manager: ProviderManager = Depends(get_provider_manager),
) -> ProviderInfo:
    info = await manager.get_provider_info(provider_id)
    if info is None:
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{provider_id}' not found",
        )
    return info


@router.post(
    "/",
    response_model=ProviderInfo,
    summary="Create a custom provider",
)
async def create_custom_provider(
    body: ProviderCreateRequest,
    manager: ProviderManager = Depends(get_provider_manager),
) -> ProviderInfo:
    try:
        info = ProviderInfo(
            id=body.id.strip(),
            name=body.name.strip(),
            base_url=body.base_url,
            api_key=body.api_key,
            chat_model=body.chat_model,
            models=body.models,
            extra_models=body.extra_models,
            is_local=body.is_local,
            is_custom=True,
            require_api_key=body.require_api_key,
            freeze_url=body.freeze_url,
            support_model_discovery=body.support_model_discovery,
            generate_kwargs=body.generate_kwargs,
        )
        return await manager.add_custom_provider(info)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail=str(e),
        ) from e


@router.delete(
    "/{provider_id}",
    status_code=204,
    summary="Delete a custom provider (built-in cannot be removed)",
)
async def delete_custom_provider(
    provider_id: str,
    manager: ProviderManager = Depends(get_provider_manager),
) -> None:
    info = await manager.get_provider_info(provider_id)
    if info is None:
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{provider_id}' not found",
        )
    if not info.is_custom:
        raise HTTPException(
            status_code=400,
            detail="Only custom providers can be deleted",
        )
    if not manager.remove_custom_provider(provider_id):
        raise HTTPException(
            status_code=500,
            detail="Failed to remove provider",
        )


@router.put(
    "/{provider_id}/config",
    response_model=ProviderInfo,
    summary="Configure a provider",
)
async def configure_provider(
    manager: ProviderManager = Depends(get_provider_manager),
    provider_id: str = "",
    body: ProviderConfigRequest = Body(...),
) -> ProviderInfo:
    config = {}
    if body.name is not None:
        config["name"] = body.name
    if body.api_key is not None:
        config["api_key"] = body.api_key
    if body.base_url is not None:
        config["base_url"] = body.base_url
    if body.chat_model is not None:
        config["chat_model"] = body.chat_model
    if body.generate_kwargs is not None:
        config["generate_kwargs"] = body.generate_kwargs

    ok = manager.update_provider(provider_id, config)
    if not ok:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{provider_id}' not found after update",
        )
    provider_info = await manager.get_provider_info(provider_id)
    if provider_info is None:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{provider_id}' not found after update",
        )
    return provider_info
