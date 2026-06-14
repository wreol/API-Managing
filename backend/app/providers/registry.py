"""ProviderRegistry — tracks registered provider instances."""

from __future__ import annotations

from app.providers.base import BaseProvider


class ProviderRegistry:
    """A simple registry that holds provider instances keyed by provider_name."""

    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {}

    def register(self, provider: BaseProvider) -> None:
        """Add or replace a provider in the registry."""
        self._providers[provider.provider_name] = provider

    def get(self, name: str) -> BaseProvider | None:
        """Retrieve a provider by name, or None if not registered."""
        return self._providers.get(name)

    def list(self) -> list[BaseProvider]:
        """Return all registered providers."""
        return list(self._providers.values())

    def remove(self, name: str) -> None:
        """Remove a provider from the registry by name."""
        self._providers.pop(name, None)
