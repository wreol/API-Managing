"""Provider API routes — list, register custom, delete custom."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.models.user import User
from app.providers.base import BaseProvider
from app.providers.registry import ProviderRegistry
from app.providers.openai import OpenAIProvider
from app.providers.anthropic import AnthropicProvider
from app.providers.deepseek import DeepSeekProvider
from app.providers.generic import GenericProvider
from app.schemas.provider import ProviderInfoResponse, CustomProviderRequest

router = APIRouter(prefix="/api/v1/providers", tags=["providers"])

# ---------------------------------------------------------------------------
# Built-in provider set
# ---------------------------------------------------------------------------

_BUILTIN_NAMES = {"openai", "anthropic", "deepseek"}

# ---------------------------------------------------------------------------
# Global provider registry (module-level, lives for app lifetime)
# ---------------------------------------------------------------------------

_provider_registry: ProviderRegistry = ProviderRegistry()


def _init_builtin_providers():
    """Register built-in providers into the registry if not already present."""
    if _provider_registry.get("openai") is None:
        _provider_registry.register(OpenAIProvider())
    if _provider_registry.get("anthropic") is None:
        _provider_registry.register(AnthropicProvider())
    if _provider_registry.get("deepseek") is None:
        _provider_registry.register(DeepSeekProvider())


_init_builtin_providers()

# Label mapping for known providers
_PROVIDER_LABELS = {
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "deepseek": "DeepSeek",
}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("", response_model=list[ProviderInfoResponse])
async def list_providers(
    current_user: User = Depends(get_current_user),
):
    """List all registered providers (built-in + custom)."""
    providers: list[ProviderInfoResponse] = []

    for p in _provider_registry.list():
        is_custom = p.provider_name not in _BUILTIN_NAMES
        label = _PROVIDER_LABELS.get(p.provider_name, p.provider_name.title())
        providers.append(
            ProviderInfoResponse(
                name=p.provider_name,
                label=label,
                is_custom=is_custom,
            )
        )

    return providers


@router.post("/custom", response_model=ProviderInfoResponse, status_code=status.HTTP_201_CREATED)
async def register_custom_provider(
    body: CustomProviderRequest,
    current_user: User = Depends(get_current_user),
):
    """Register a new custom provider."""
    # Prevent overwriting a built-in
    if body.name in _BUILTIN_NAMES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot register custom provider with built-in name: {body.name}",
        )

    # Check for duplicate custom provider
    existing = _provider_registry.get(body.name)
    if existing is not None and body.name not in _BUILTIN_NAMES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Custom provider '{body.name}' already exists. Delete it first or use a different name.",
        )

    config = {
        "provider_name": body.name,
        "base_url": body.base_url,
        "usage_endpoint": body.usage_endpoint,
        "auth_type": body.auth_type,
        "auth_header_name": body.auth_header_name,
        "field_mapping": body.field_mapping,
    }
    provider = GenericProvider(config)
    _provider_registry.register(provider)

    return ProviderInfoResponse(
        name=body.name,
        label=body.label,
        is_custom=True,
    )


@router.delete("/custom/{provider_name}")
async def delete_custom_provider(
    provider_name: str,
    current_user: User = Depends(get_current_user),
):
    """Remove a custom provider from the registry."""
    # Cannot delete built-in providers
    if provider_name in _BUILTIN_NAMES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot remove built-in provider: {provider_name}",
        )

    existing = _provider_registry.get(provider_name)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Custom provider '{provider_name}' not found",
        )

    _provider_registry.remove(provider_name)
    return {"message": f"Custom provider '{provider_name}' removed"}
