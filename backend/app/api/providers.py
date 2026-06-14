"""Provider API routes — list, register custom, delete custom."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.models.user import User
from app.providers.generic import GenericProvider
from app.providers.registry import ProviderRegistry
from app.schemas.provider import ProviderInfoResponse, CustomProviderRequest

router = APIRouter(prefix="/api/v1/providers", tags=["providers"])

_BUILTIN_NAMES = {"openai", "anthropic", "deepseek"}
_PROVIDER_LABELS = {
    "openai": "OpenAI", "anthropic": "Anthropic", "deepseek": "DeepSeek",
}


@router.get("", response_model=list[ProviderInfoResponse])
async def list_providers(current_user: User = Depends(get_current_user)):
    providers = []
    for name in ProviderRegistry.list_providers():
        is_custom = name not in _BUILTIN_NAMES
        label = _PROVIDER_LABELS.get(name, name.title())
        providers.append(ProviderInfoResponse(name=name, label=label, is_custom=is_custom))
    return providers


@router.post("/custom", response_model=ProviderInfoResponse, status_code=status.HTTP_201_CREATED)
async def register_custom_provider(body: CustomProviderRequest, current_user: User = Depends(get_current_user)):
    if body.name in _BUILTIN_NAMES:
        raise HTTPException(status_code=409, detail=f"Cannot overwrite built-in provider: {body.name}")
    if ProviderRegistry.get(body.name):
        raise HTTPException(status_code=409, detail=f"Custom provider '{body.name}' already exists")

    config = {
        "provider_name": body.name, "base_url": body.base_url,
        "usage_endpoint": body.usage_endpoint, "auth_type": body.auth_type,
        "auth_header_name": body.auth_header_name, "field_mapping": body.field_mapping,
    }
    ProviderRegistry.register(GenericProvider(config))
    return ProviderInfoResponse(name=body.name, label=body.label, is_custom=True)


@router.delete("/custom/{provider_name}")
async def delete_custom_provider(provider_name: str, current_user: User = Depends(get_current_user)):
    if provider_name in _BUILTIN_NAMES:
        raise HTTPException(status_code=403, detail=f"Cannot remove built-in provider: {provider_name}")
    if not ProviderRegistry.get(provider_name):
        raise HTTPException(status_code=404, detail=f"Custom provider '{provider_name}' not found")
    ProviderRegistry.remove(provider_name)
    return {"message": f"Custom provider '{provider_name}' removed"}
