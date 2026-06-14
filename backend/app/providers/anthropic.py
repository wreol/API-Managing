"""Anthropic provider — placeholder (usage must be entered manually)."""

from __future__ import annotations

from datetime import date

from app.providers.base import BaseProvider, UsageRecord


class AnthropicProvider(BaseProvider):
    provider_name = "anthropic"
    base_url = "https://api.anthropic.com"
    usage_endpoint = ""

    def auth_headers(self, api_key: str) -> dict[str, str]:
        return {"x-api-key": api_key}

    async def fetch_usage(
        self, api_key: str, target_date: date | None = None
    ) -> UsageRecord:
        # Anthropic does not expose a public usage API key-based endpoint.
        # Usage data must be entered manually via the Console.
        return UsageRecord(
            provider=self.provider_name,
            raw_response={
                "note": "Anthropic usage must be manually entered — no programmatic usage API available",
                "source": "console.anthropic.com",
            },
        )
