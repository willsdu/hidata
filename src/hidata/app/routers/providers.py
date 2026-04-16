from hidata.providers.provider_manager import ProviderManager
from fastapi import APIRouter, Depends,Request,Body, HTTPException
from typing import List
from hidata.providers.provider import ProviderInfo
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
    api_key: Optional[str] = Field(default=None)
    base_url: Optional[str] = Field(default=None)
    chat_model: Optional[ChatModelName] = Field(
        default=None,
        description="Chat model class name for protocol selection",
    )
    generate_kwargs: Optional[dict] = Field(
        default_factory=dict,
        description=(
            "Configuration in json format, will be expanded "
            "and passed to generation calls "
            "(e.g., openai.chat.completions, anthropic.messages)."
        ),
    )


@router.get(
    "/",
    response_model=List[ProviderInfo],
    summary="List all providers",
)
async def list_all_providers(
    manager: ProviderManager = Depends(get_provider_manager),
) -> List[ProviderInfo]:
    return await manager.list_provider_info()


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
    ok=manager.update_provider(
        provider_id, 
        {
            "api_key": body.api_key,
            "base_url": body.base_url,
            "chat_model": body.chat_model,
            "generate_kwargs": body.generate_kwargs,
        },
    )
    if not ok:
        raise HTTPException(
            status_code=400, 
            detail=f"Provider '{provider_id}' not found after update",
        )
    provider_info= await manager.get_provider_info(provider_id)
    if provider_info is None:
        raise HTTPException(
            status_code=400, 
            detail=f"Provider '{provider_id}' not found after update",
        )
    return provider_info
