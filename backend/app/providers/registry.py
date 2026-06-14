"""ProviderRegistry — singleton registry of all provider instances."""

from __future__ import annotations

from app.providers.base import BaseProvider


class ProviderRegistry:
    """Singleton registry holding provider instances keyed by provider_name."""

    _providers: dict[str, BaseProvider] = {}

    @classmethod
    def register(cls, provider: BaseProvider) -> None:
        cls._providers[provider.provider_name] = provider

    @classmethod
    def get(cls, name: str) -> BaseProvider | None:
        return cls._providers.get(name)

    @classmethod
    def list_providers(cls) -> list[str]:
        return list(cls._providers.keys())

    @classmethod
    def remove(cls, name: str) -> None:
        cls._providers.pop(name, None)
