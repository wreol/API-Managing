"""Anthropic provider — real connection test, usage via manual entry.

Anthropic does not expose a public usage API endpoint. Usage data must be
viewed at console.anthropic.com. This provider validates API keys via a
lightweight /v1/models request and returns empty UsageRecord for fetch.
"""

from __future__ import annotations

from datetime import date

import httpx

from app.providers.base import BaseProvider, UsageRecord


class AnthropicProvider(BaseProvider):
    provider_name = "anthropic"
    base_url = "https://api.anthropic.com"
    usage_endpoint = ""

    def auth_headers(self, api_key: str) -> dict[str, str]:
        return {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        }

    async def fetch_usage(
        self, api_key: str, target_date: date | None = None
    ) -> UsageRecord:
        """Anthropic has no programmatic usage API. Returns empty record."""
        return UsageRecord(
            provider=self.provider_name,
            raw_response={
                "note": "Anthropic usage must be manually entered — no programmatic usage API available",
                "source": "console.anthropic.com",
            },
        )

    async def test_connection(self, api_key: str) -> dict:
        """Validate key via the /v1/models endpoint."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/v1/models",
                    headers=self.auth_headers(api_key),
                    timeout=10.0,
                )
            if resp.status_code == 200:
                return {"status": "ok", "message": "Anthropic API key is valid"}
            if resp.status_code in (401, 403):
                return {"status": "error", "message": "Invalid API key"}
            return {"status": "error", "message": f"Unexpected response: {resp.status_code}"}
        except httpx.TimeoutException:
            return {"status": "error", "message": "Connection timed out"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
