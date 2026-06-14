"""OpenAI provider — usage via /v1/usage endpoint."""

from __future__ import annotations

from datetime import date

import httpx

from app.providers.base import BaseProvider, UsageRecord


class OpenAIProvider(BaseProvider):
    provider_name = "openai"
    base_url = "https://api.openai.com"
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
            raise Exception(
                f"OpenAI usage fetch failed: {response.status_code} {response.text}"
            )

        return self.normalize_response(response.json())

    async def test_connection(self, api_key: str) -> dict:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/v1/models",
                    headers=self.auth_headers(api_key),
                    timeout=10.0,
                )
            if resp.status_code == 200:
                return {"status": "ok", "message": "OpenAI API key is valid"}
            if resp.status_code == 401:
                return {"status": "error", "message": "Invalid API key"}
            return {"status": "error", "message": f"Unexpected response: {resp.status_code}"}
        except httpx.TimeoutException:
            return {"status": "error", "message": "Connection timed out"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def normalize_response(self, raw: dict) -> UsageRecord:
        cost_cents = raw.get("current_usage_usd", 0)
        return UsageRecord(
            provider=self.provider_name,
            cost_estimate=cost_cents / 100.0 if isinstance(cost_cents, (int, float)) and cost_cents > 0 else 0.0,
            raw_response=raw,
        )
