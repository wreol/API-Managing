"""DeepSeek provider — OpenAI-compatible usage endpoint."""

from __future__ import annotations

from datetime import date

import httpx

from app.providers.base import BaseProvider, UsageRecord


class DeepSeekProvider(BaseProvider):
    """DeepSeek offers an OpenAI-compatible API.

    Attempts to use OpenAI-compatible /v1/usage endpoint.
    Falls back to placeholder if the endpoint is not available.
    """

    provider_name = "deepseek"
    base_url = "https://api.deepseek.com"
    usage_endpoint = "/v1/usage"

    def auth_headers(self, api_key: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {api_key}"}

    async def fetch_usage(
        self, api_key: str, target_date: date | None = None
    ) -> UsageRecord:
        url = f"{self.base_url}{self.usage_endpoint}"

        if target_date is None:
            target_date = date.today()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self.auth_headers(api_key),
                params={"date": target_date.isoformat()},
            )

        if response.status_code != 200:
            # Fallback: DeepSeek may not have a public usage endpoint;
            # return placeholder similar to Anthropic.
            return UsageRecord(
                provider=self.provider_name,
                raw_response={
                    "note": "DeepSeek usage endpoint not available — usage must be manually entered",
                },
            )

        return self.normalize_response(response.json())

    def normalize_response(self, raw: dict) -> UsageRecord:
        # OpenAI-compatible: current_usage_usd in cents
        cost_cents = raw.get("current_usage_usd", 0)
        return UsageRecord(
            provider=self.provider_name,
            cost_estimate=cost_cents / 100.0 if isinstance(cost_cents, (int, float)) and cost_cents > 0 else 0.0,
            raw_response=raw,
        )
