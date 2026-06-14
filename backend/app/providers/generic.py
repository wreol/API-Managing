"""Generic provider — user-configured via dict/config."""

from __future__ import annotations

from datetime import date

import httpx

from app.providers.base import BaseProvider, UsageRecord


class GenericProvider(BaseProvider):
    """A fully user-configured provider.

    Config keys:
        provider_name (str): Unique name for this provider.
        base_url (str): Base URL for the provider API.
        usage_endpoint (str): Path for the usage endpoint.
        auth_type (str): "bearer" or "custom_header".
        auth_header_name (str): Header name for custom_header auth (default: X-API-Key).
        field_mapping (dict): Mapping of UsageRecord fields → JSON keys in raw response.
            Keys: calls, tokens_in, tokens_out, cost_estimate.
    """

    def __init__(self, config: dict) -> None:
        self.provider_name = config["provider_name"]
        self.base_url = config["base_url"]
        self.usage_endpoint = config.get("usage_endpoint", "/v1/usage")
        self._auth_type = config.get("auth_type", "bearer")
        self._auth_header_name = config.get("auth_header_name", "X-API-Key")
        self._field_mapping = config.get("field_mapping", {})

    def auth_headers(self, api_key: str) -> dict[str, str]:
        if self._auth_type == "custom_header":
            return {self._auth_header_name: api_key}
        # Default: bearer
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
            return UsageRecord(
                provider=self.provider_name,
                raw_response={"error": f"HTTP {response.status_code}", "body": response.text},
            )

        return self.normalize_response(response.json())

    async def test_connection(self, api_key: str) -> dict:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    self.base_url,
                    headers=self.auth_headers(api_key),
                    timeout=10.0,
                )
            if resp.status_code < 500:
                return {"status": "ok", "message": f"Connected ({resp.status_code})"}
            return {"status": "error", "message": f"Server error: {resp.status_code}"}
        except httpx.TimeoutException:
            return {"status": "error", "message": "Connection timed out"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def normalize_response(self, raw: dict) -> UsageRecord:
        def _get(field: str, default=0):
            key = self._field_mapping.get(field)
            if key is None:
                return default
            return raw.get(key, default)

        return UsageRecord(
            provider=self.provider_name,
            calls=_get("calls", 0),
            tokens_in=_get("tokens_in", 0),
            tokens_out=_get("tokens_out", 0),
            cost_estimate=_get("cost_estimate", None),
            raw_response=raw,
        )
