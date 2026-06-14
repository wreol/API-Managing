"""Abstract base provider and data structures."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date


@dataclass
class UsageRecord:
    """Standardized usage data returned by any provider."""

    provider: str
    key_id: str = ""
    period_start: date | None = None
    period_end: date | None = None
    calls: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    cost_estimate: float | None = None
    raw_response: dict | None = None


class BaseProvider(ABC):
    """Abstract base for all provider implementations."""

    provider_name: str = ""
    base_url: str = ""
    usage_endpoint: str = ""

    @abstractmethod
    def auth_headers(self, api_key: str) -> dict[str, str]:
        """Return the HTTP headers needed to authenticate with the provider API."""
        ...

    @abstractmethod
    async def fetch_usage(self, api_key: str, target_date: date | None = None) -> UsageRecord:
        """Fetch usage data from the provider for the given date."""
        ...

    def normalize_response(self, raw: dict) -> UsageRecord:
        """Convert a raw provider response into a standardized UsageRecord."""
        raise NotImplementedError
