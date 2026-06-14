"""DeepSeek provider — real connection test, usage endpoint when available.

DeepSeek's API is OpenAI-compatible. This provider validates keys via
/v1/models and attempts to fetch usage via /v1/usage (may not be available).
"""

from __future__ import annotations

from datetime import date

import httpx

from app.providers.base import BaseProvider, UsageRecord


class DeepSeekProvider(BaseProvider):
    provider_name = "deepseek"
    base_url = "https://api.deepseek.com"
    usage_endpoint = "/v1/usage"

    def auth_headers(self, api_key: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {api_key}"}

    async def fetch_usage(
        self, api_key: str, target_date: date | None = None
    ) -> UsageRecord:
        """Try usage endpoint, return empty if unavailable."""
        url = f"{self.base_url}{self.usage_endpoint}"

        if target_date is None:
            target_date = date.today()

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.auth_headers(api_key),
                    params={"date": target_date.isoformat()},
                    timeout=10.0,
                )

            if response.status_code == 200:
                return self.normalize_response(response.json())

            return UsageRecord(
                provider=self.provider_name,
                raw_response={"note": "DeepSeek usage endpoint unavailable — use console"},
            )
        except httpx.TimeoutException:
            return UsageRecord(
                provider=self.provider_name,
                raw_response={"error": "Connection timed out"},
            )
        except Exception:
            return UsageRecord(
                provider=self.provider_name,
                raw_response={"note": "DeepSeek usage endpoint unavailable — use console"},
            )

    async def test_connection(self, api_key: str) -> dict:
        """Validate key via /v1/models endpoint."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/v1/models",
                    headers=self.auth_headers(api_key),
                    timeout=10.0,
                )
            if resp.status_code == 200:
                return {"status": "ok", "message": "DeepSeek API key is valid"}
            if resp.status_code in (401, 403):
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
