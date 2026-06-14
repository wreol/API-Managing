"""Tests for Provider Engine: BaseProvider, ProviderRegistry, and all providers."""

import pytest
from datetime import date
from unittest.mock import AsyncMock, patch, MagicMock

import httpx


# ============================================================================
# T4.1: BaseProvider + ProviderRegistry tests
# ============================================================================

class TestBaseProvider:
    """Test the abstract BaseProvider interface."""

    def test_cannot_instantiate_base_provider_directly(self):
        """BaseProvider is abstract — instantiating it directly should raise TypeError."""
        from app.providers.base import BaseProvider

        with pytest.raises(TypeError):
            BaseProvider()  # type: ignore[abstract]

    def test_concrete_subclass_without_abstract_methods_fails(self):
        """A subclass that doesn't implement auth_headers or fetch_usage must be abstract too."""
        from app.providers.base import BaseProvider

        with pytest.raises(TypeError):

            class IncompleteProvider(BaseProvider):  # type: ignore[abstract]
                provider_name = "incomplete"

            IncompleteProvider()

    def test_usage_record_defaults(self):
        """UsageRecord fields have correct defaults."""
        from app.providers.base import UsageRecord

        record = UsageRecord(
            provider="openai",
            key_id="key-123",
            period_start=date(2026, 6, 1),
            period_end=date(2026, 6, 30),
        )
        assert record.calls == 0
        assert record.tokens_in == 0
        assert record.tokens_out == 0
        assert record.cost_estimate is None
        assert record.raw_response is None

    def test_usage_record_is_dataclass(self):
        """UsageRecord is a dataclass with all specified fields."""
        from app.providers.base import UsageRecord
        from dataclasses import is_dataclass, fields

        assert is_dataclass(UsageRecord)

        field_names = {f.name for f in fields(UsageRecord)}
        expected = {
            "provider",
            "key_id",
            "period_start",
            "period_end",
            "calls",
            "tokens_in",
            "tokens_out",
            "cost_estimate",
            "raw_response",
        }
        assert field_names == expected

    def test_usage_record_full_construction(self):
        """UsageRecord accepts all fields at construction."""
        from app.providers.base import UsageRecord

        raw = {"usage": "data"}
        record = UsageRecord(
            provider="anthropic",
            key_id="key-456",
            period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 31),
            calls=1500,
            tokens_in=50000,
            tokens_out=20000,
            cost_estimate=12.50,
            raw_response=raw,
        )
        assert record.calls == 1500
        assert record.tokens_in == 50000
        assert record.tokens_out == 20000
        assert record.cost_estimate == 12.50
        assert record.raw_response is raw


class TestProviderRegistry:
    """Test the ProviderRegistry pattern."""

    def test_register_and_get_provider(self):
        """Providers can be registered and retrieved by name."""
        from app.providers.base import BaseProvider, UsageRecord
        from app.providers.registry import ProviderRegistry

        registry = ProviderRegistry()

        class MockProvider(BaseProvider):
            provider_name = "mock"
            base_url = "https://mock.example.com"
            usage_endpoint = "/v1/usage"

            def auth_headers(self, api_key):
                return {"Authorization": f"Bearer {api_key}"}

            async def fetch_usage(self, api_key):
                return UsageRecord(
                    provider=self.provider_name,
                    key_id="test",
                    period_start=date.today(),
                    period_end=date.today(),
                )

        registry.register(MockProvider())
        provider = registry.get("mock")
        assert provider is not None
        assert provider.provider_name == "mock"
        assert provider.base_url == "https://mock.example.com"

    def test_get_unregistered_provider_returns_none(self):
        """Getting an unregistered provider returns None."""
        from app.providers.registry import ProviderRegistry

        registry = ProviderRegistry()
        assert registry.get("nonexistent") is None

    def test_list_all_returns_all_registered_providers(self):
        """list() returns all registered providers."""
        from app.providers.base import BaseProvider, UsageRecord
        from app.providers.registry import ProviderRegistry

        registry = ProviderRegistry()

        class ProviderA(BaseProvider):
            provider_name = "provider-a"

            def auth_headers(self, api_key):
                return {}

            async def fetch_usage(self, api_key):
                return UsageRecord(provider="a", key_id="k", period_start=date.today(), period_end=date.today())

        class ProviderB(BaseProvider):
            provider_name = "provider-b"

            def auth_headers(self, api_key):
                return {}

            async def fetch_usage(self, api_key):
                return UsageRecord(provider="b", key_id="k", period_start=date.today(), period_end=date.today())

        registry.register(ProviderA())
        registry.register(ProviderB())

        all_providers = registry.list()
        assert len(all_providers) == 2
        names = {p.provider_name for p in all_providers}
        assert names == {"provider-a", "provider-b"}

    def test_register_duplicate_overwrites(self):
        """Registering a provider with the same name overwrites the previous one."""
        from app.providers.base import BaseProvider, UsageRecord
        from app.providers.registry import ProviderRegistry

        registry = ProviderRegistry()

        class V1(BaseProvider):
            provider_name = "dup"
            base_url = "https://v1.example.com"

            def auth_headers(self, api_key):
                return {}

            async def fetch_usage(self, api_key):
                return UsageRecord(provider="dup", key_id="k", period_start=date.today(), period_end=date.today())

        class V2(BaseProvider):
            provider_name = "dup"
            base_url = "https://v2.example.com"

            def auth_headers(self, api_key):
                return {}

            async def fetch_usage(self, api_key):
                return UsageRecord(provider="dup", key_id="k", period_start=date.today(), period_end=date.today())

        registry.register(V1())
        registry.register(V2())

        provider = registry.get("dup")
        assert provider is not None
        assert provider.base_url == "https://v2.example.com"
        assert len(registry.list()) == 1

    def test_remove_provider(self):
        """Providers can be removed from the registry."""
        from app.providers.base import BaseProvider, UsageRecord
        from app.providers.registry import ProviderRegistry

        registry = ProviderRegistry()

        class TempProvider(BaseProvider):
            provider_name = "temp"

            def auth_headers(self, api_key):
                return {}

            async def fetch_usage(self, api_key):
                return UsageRecord(provider="temp", key_id="k", period_start=date.today(), period_end=date.today())

        registry.register(TempProvider())
        assert registry.get("temp") is not None

        registry.remove("temp")
        assert registry.get("temp") is None

    def test_remove_nonexistent_does_not_raise(self):
        """Removing a provider that doesn't exist should not raise."""
        from app.providers.registry import ProviderRegistry

        registry = ProviderRegistry()
        # Should not raise
        registry.remove("nonexistent")


# ============================================================================
# T4.2: OpenAI Provider tests
# ============================================================================

class TestOpenAIProvider:
    """Test the OpenAI provider implementation."""

    def test_openai_auth_headers(self):
        """OpenAI uses Bearer token authentication."""
        from app.providers.openai import OpenAIProvider

        provider = OpenAIProvider()
        headers = provider.auth_headers("sk-test-key-12345")
        assert headers == {"Authorization": "Bearer sk-test-key-12345"}

    def test_openai_provider_has_correct_attributes(self):
        """OpenAI provider has provider_name, base_url, and usage_endpoint set."""
        from app.providers.openai import OpenAIProvider

        provider = OpenAIProvider()
        assert provider.provider_name == "openai"
        assert provider.base_url == "https://api.openai.com"
        assert provider.usage_endpoint == "/v1/usage"

    def test_openai_normalize_response_converts_cents_to_dollars(self):
        """OpenAI usage response has current_usage_usd in cents; normalize divides by 100."""
        from app.providers.openai import OpenAIProvider
        from datetime import date

        provider = OpenAIProvider()

        raw = {
            "object": "usage",
            "daily_costs": {
                "breakdown": {}
            },
            "current_usage_usd": 5250,  # 5250 cents = $52.50
        }

        record = provider.normalize_response(raw)
        assert record.cost_estimate == 52.50
        assert record.provider == "openai"
        assert record.raw_response is raw
        assert record.calls == 0
        assert record.tokens_in == 0
        assert record.tokens_out == 0

    def test_openai_normalize_response_handles_missing_cost(self):
        """Normalize handles responses without current_usage_usd."""
        from app.providers.openai import OpenAIProvider
        from datetime import date

        provider = OpenAIProvider()

        raw = {"object": "usage", "daily_costs": {}}
        record = provider.normalize_response(raw)
        assert record.cost_estimate == 0.0
        assert record.provider == "openai"

    @pytest.mark.asyncio
    async def test_openai_fetch_usage_makes_correct_request(self):
        """fetch_usage makes a GET to the correct endpoint with Bearer auth."""
        from app.providers.openai import OpenAIProvider

        provider = OpenAIProvider()

        mock_response = httpx.Response(
            status_code=200,
            json={
                "object": "usage",
                "current_usage_usd": 1234,
                "daily_costs": {},
            },
            request=httpx.Request("GET", "https://api.openai.com/v1/usage?date=2026-06-14"),
        )

        async def mock_get(*args, **kwargs):
            return mock_response

        with patch.object(httpx.AsyncClient, "get", side_effect=mock_get) as mock_get_spy:
            record = await provider.fetch_usage("sk-test-key", date.today())

        assert record.provider == "openai"
        assert record.cost_estimate == 12.34
        assert record.raw_response is not None
        # Verify the request was made with correct params
        mock_get_spy.assert_called_once()
        call_args = mock_get_spy.call_args
        assert call_args[0][0] == "https://api.openai.com/v1/usage"
        assert "params" in call_args[1]

    @pytest.mark.asyncio
    async def test_openai_fetch_usage_handles_http_error(self):
        """fetch_usage raises an appropriate error on HTTP failure."""
        from app.providers.openai import OpenAIProvider

        provider = OpenAIProvider()

        mock_response = httpx.Response(
            status_code=401,
            json={"error": "Invalid API key"},
            request=httpx.Request("GET", "https://api.openai.com/v1/usage"),
        )

        async def mock_get(*args, **kwargs):
            return mock_response

        with patch.object(httpx.AsyncClient, "get", side_effect=mock_get):
            with pytest.raises(Exception):
                await provider.fetch_usage("bad-key")


# ============================================================================
# T4.3: Anthropic Provider tests
# ============================================================================

class TestAnthropicProvider:
    """Test the Anthropic provider (placeholder implementation)."""

    def test_anthropic_auth_headers(self):
        """Anthropic uses x-api-key header."""
        from app.providers.anthropic import AnthropicProvider

        provider = AnthropicProvider()
        headers = provider.auth_headers("sk-ant-api03-secret")
        assert headers == {"x-api-key": "sk-ant-api03-secret"}

    def test_anthropic_provider_attributes(self):
        """Anthropic provider has correct name and attributes."""
        from app.providers.anthropic import AnthropicProvider

        provider = AnthropicProvider()
        assert provider.provider_name == "anthropic"
        assert provider.base_url == "https://api.anthropic.com"

    @pytest.mark.asyncio
    async def test_anthropic_fetch_usage_returns_placeholder(self):
        """Anthropic returns empty UsageRecord with a note about manual entry."""
        from app.providers.anthropic import AnthropicProvider
        from datetime import date

        provider = AnthropicProvider()
        record = await provider.fetch_usage("sk-ant-api03-test")

        assert record.provider == "anthropic"
        assert record.calls == 0
        assert record.tokens_in == 0
        assert record.tokens_out == 0
        assert record.cost_estimate is None
        assert record.raw_response is not None
        assert "manual" in str(record.raw_response).lower()


# ============================================================================
# T4.4: DeepSeek Provider tests
# ============================================================================

class TestDeepSeekProvider:
    """Test the DeepSeek provider (OpenAI-compatible API)."""

    def test_deepseek_auth_headers(self):
        """DeepSeek uses Bearer token like OpenAI."""
        from app.providers.deepseek import DeepSeekProvider

        provider = DeepSeekProvider()
        headers = provider.auth_headers("sk-deepseek-key")
        assert headers == {"Authorization": "Bearer sk-deepseek-key"}

    def test_deepseek_provider_attributes(self):
        """DeepSeek provider has correct attributes."""
        from app.providers.deepseek import DeepSeekProvider

        provider = DeepSeekProvider()
        assert provider.provider_name == "deepseek"
        assert "api.deepseek.com" in provider.base_url

    @pytest.mark.asyncio
    async def test_deepseek_normalize_response_handles_openai_compatible_format(self):
        """DeepSeek normalize should handle the OpenAI-compatible usage response."""
        from app.providers.deepseek import DeepSeekProvider

        provider = DeepSeekProvider()

        raw = {
            "object": "usage",
            "current_usage_usd": 1500,  # $15.00
        }
        record = provider.normalize_response(raw)
        assert record.cost_estimate == 15.00
        assert record.provider == "deepseek"

    @pytest.mark.asyncio
    async def test_deepseek_fetch_usage_makes_request_to_correct_url(self):
        """fetch_usage calls the DeepSeek API with correct URL."""
        from app.providers.deepseek import DeepSeekProvider
        import httpx

        provider = DeepSeekProvider()

        mock_response = httpx.Response(
            status_code=200,
            json={"current_usage_usd": 500},
            request=httpx.Request("GET", f"{provider.base_url}{provider.usage_endpoint}"),
        )

        async def mock_get(*args, **kwargs):
            return mock_response

        with patch.object(httpx.AsyncClient, "get", side_effect=mock_get) as mock_get_spy:
            record = await provider.fetch_usage("sk-deepseek-key", date.today())

        assert record.provider == "deepseek"
        assert record.cost_estimate == 5.00
        mock_get_spy.assert_called_once()


# ============================================================================
# T4.5: Generic Provider tests
# ============================================================================

class TestGenericProvider:
    """Test the Generic (user-configured) provider."""

    def test_generic_provider_constructed_from_config(self):
        """Generic provider reads all settings from a config dict."""
        from app.providers.generic import GenericProvider

        config = {
            "provider_name": "my-custom-llm",
            "base_url": "https://my-llm.example.com",
            "usage_endpoint": "/api/usage",
            "auth_type": "bearer",
            "field_mapping": {
                "calls": "total_requests",
                "tokens_in": "input_tokens",
                "tokens_out": "output_tokens",
                "cost_estimate": "total_cost",
            },
        }

        provider = GenericProvider(config)
        assert provider.provider_name == "my-custom-llm"
        assert provider.base_url == "https://my-llm.example.com"
        assert provider.usage_endpoint == "/api/usage"
        assert provider._auth_type == "bearer"

    def test_generic_bearer_auth_headers(self):
        """Bearer auth_type produces Bearer header."""
        from app.providers.generic import GenericProvider

        config = {
            "provider_name": "custom-bear",
            "base_url": "https://example.com",
            "usage_endpoint": "/usage",
            "auth_type": "bearer",
            "field_mapping": {},
        }
        provider = GenericProvider(config)
        headers = provider.auth_headers("my-secret-key")
        assert headers == {"Authorization": "Bearer my-secret-key"}

    def test_generic_custom_header_auth(self):
        """custom_header auth_type uses the configured header name."""
        from app.providers.generic import GenericProvider

        config = {
            "provider_name": "custom-header-prov",
            "base_url": "https://example.com",
            "usage_endpoint": "/usage",
            "auth_type": "custom_header",
            "auth_header_name": "X-API-Key",
            "field_mapping": {},
        }
        provider = GenericProvider(config)
        headers = provider.auth_headers("key123")
        assert headers == {"X-API-Key": "key123"}

    def test_generic_custom_header_defaults_to_x_api_key(self):
        """custom_header auth_type defaults to X-API-Key if no header name specified."""
        from app.providers.generic import GenericProvider

        config = {
            "provider_name": "default-header",
            "base_url": "https://example.com",
            "usage_endpoint": "/usage",
            "auth_type": "custom_header",
            "field_mapping": {},
        }
        provider = GenericProvider(config)
        headers = provider.auth_headers("secret")
        assert headers == {"X-API-Key": "secret"}

    def test_generic_normalize_uses_field_mapping(self):
        """normalize_response uses field_mapping to extract values from raw response."""
        from app.providers.generic import GenericProvider

        config = {
            "provider_name": "mapped",
            "base_url": "https://example.com",
            "usage_endpoint": "/usage",
            "auth_type": "bearer",
            "field_mapping": {
                "calls": "req_count",
                "tokens_in": "prompt_tokens",
                "tokens_out": "completion_tokens",
                "cost_estimate": "price_usd",
            },
        }
        provider = GenericProvider(config)

        raw = {
            "req_count": 300,
            "prompt_tokens": 12000,
            "completion_tokens": 8000,
            "price_usd": 4.50,
        }
        record = provider.normalize_response(raw)
        assert record.calls == 300
        assert record.tokens_in == 12000
        assert record.tokens_out == 8000
        assert record.cost_estimate == 4.50
        assert record.provider == "mapped"

    def test_generic_normalize_handles_missing_fields(self):
        """normalize_response gracefully handles fields missing from the raw response."""
        from app.providers.generic import GenericProvider

        config = {
            "provider_name": "partial",
            "base_url": "https://example.com",
            "usage_endpoint": "/usage",
            "auth_type": "bearer",
            "field_mapping": {
                "calls": "c",
                "tokens_in": "ti",
            },
        }
        provider = GenericProvider(config)

        raw = {"other": "data"}  # none of the mapped fields exist
        record = provider.normalize_response(raw)
        assert record.calls == 0
        assert record.tokens_in == 0
        assert record.provider == "partial"

    @pytest.mark.asyncio
    async def test_generic_fetch_usage_makes_request(self):
        """fetch_usage makes request to configured URL with proper auth."""
        from app.providers.generic import GenericProvider
        import httpx
        from datetime import date

        config = {
            "provider_name": "fetch-test",
            "base_url": "https://api.example.com",
            "usage_endpoint": "/v2/usage",
            "auth_type": "bearer",
            "field_mapping": {},
        }
        provider = GenericProvider(config)

        mock_response = httpx.Response(
            status_code=200,
            json={"usage": "ok"},
            request=httpx.Request("GET", "https://api.example.com/v2/usage"),
        )

        async def mock_get(*args, **kwargs):
            return mock_response

        with patch.object(httpx.AsyncClient, "get", side_effect=mock_get) as mock_get_spy:
            record = await provider.fetch_usage("my-key", date.today())

        assert record.provider == "fetch-test"
        mock_get_spy.assert_called_once()


# ============================================================================
# T4.6: Provider API endpoint tests
# ============================================================================

class TestProviderAPI:
    """Integration tests for Provider API endpoints (authenticated)."""

    @pytest.mark.asyncio
    async def test_list_providers_returns_registered_providers(self, async_client):
        """GET /api/v1/providers returns list of built-in registered providers."""
        from tests.test_keys import _register_user

        access_token, _user = await _register_user(async_client, "provuser1@test.com")
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await async_client.get("/api/v1/providers", headers=headers)
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3  # At least openai, anthropic, deepseek
        names = {p["name"] for p in data}
        assert "openai" in names
        assert "anthropic" in names
        assert "deepseek" in names

    @pytest.mark.asyncio
    async def test_list_providers_shows_is_custom_flag(self, async_client):
        """Each provider entry has name, label, and is_custom fields."""
        from tests.test_keys import _register_user

        access_token, _user = await _register_user(async_client, "provuser2@test.com")
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await async_client.get("/api/v1/providers", headers=headers)
        assert response.status_code == 200

        for provider in response.json():
            assert "name" in provider
            assert "label" in provider
            assert "is_custom" in provider
            # Built-in providers are not custom
            if provider["name"] in ("openai", "anthropic", "deepseek"):
                assert provider["is_custom"] is False

    @pytest.mark.asyncio
    async def test_list_providers_unauthenticated_returns_401(self, async_client):
        """Unauthenticated access to providers list returns 401."""
        response = await async_client.get("/api/v1/providers")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_register_custom_provider(self, async_client):
        """POST /api/v1/providers/custom registers a new custom provider."""
        from tests.test_keys import _register_user

        access_token, _user = await _register_user(async_client, "provuser3@test.com")
        headers = {"Authorization": f"Bearer {access_token}"}

        payload = {
            "name": "my-provider",
            "label": "My Custom LLM",
            "base_url": "https://my-llm.example.com",
            "usage_endpoint": "/api/usage",
            "auth_type": "bearer",
            "field_mapping": {
                "calls": "total_requests",
                "tokens_in": "input_tokens",
                "tokens_out": "output_tokens",
                "cost_estimate": "total_cost",
            },
        }
        response = await async_client.post(
            "/api/v1/providers/custom", json=payload, headers=headers
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["name"] == "my-provider"
        assert data["label"] == "My Custom LLM"
        assert data["is_custom"] is True

        # Should now appear in providers list
        list_response = await async_client.get("/api/v1/providers", headers=headers)
        names = {p["name"] for p in list_response.json()}
        assert "my-provider" in names

    @pytest.mark.asyncio
    async def test_register_custom_provider_custom_header_auth(self, async_client):
        """Custom provider with custom_header auth type."""
        from tests.test_keys import _register_user

        access_token, _user = await _register_user(async_client, "provuser4@test.com")
        headers = {"Authorization": f"Bearer {access_token}"}

        payload = {
            "name": "header-auth-provider",
            "label": "Header Auth Provider",
            "base_url": "https://api.example.com",
            "usage_endpoint": "/v1/usage",
            "auth_type": "custom_header",
            "auth_header_name": "X-API-Key",
            "field_mapping": {},
        }
        response = await async_client.post(
            "/api/v1/providers/custom", json=payload, headers=headers
        )
        assert response.status_code == 201, response.text

    @pytest.mark.asyncio
    async def test_register_custom_provider_duplicate_name_returns_409(self, async_client):
        """Registering a custom provider with existing name returns 409."""
        from tests.test_keys import _register_user

        access_token, _user = await _register_user(async_client, "provuser5@test.com")
        headers = {"Authorization": f"Bearer {access_token}"}

        payload = {
            "name": "dup-provider",
            "label": "Duplicate Provider",
            "base_url": "https://example1.com",
            "usage_endpoint": "/usage",
            "auth_type": "bearer",
            "field_mapping": {},
        }
        r1 = await async_client.post(
            "/api/v1/providers/custom", json=payload, headers=headers
        )
        assert r1.status_code == 201, r1.text

        # Same name, different base_url — should conflict
        payload2 = {**payload, "base_url": "https://example2.com"}
        r2 = await async_client.post(
            "/api/v1/providers/custom", json=payload2, headers=headers
        )
        assert r2.status_code == 409

    @pytest.mark.asyncio
    async def test_register_custom_provider_builtin_name_returns_409(self, async_client):
        """Cannot register a custom provider with a built-in provider name."""
        from tests.test_keys import _register_user

        access_token, _user = await _register_user(async_client, "provuser6@test.com")
        headers = {"Authorization": f"Bearer {access_token}"}

        payload = {
            "name": "openai",
            "label": "Fake OpenAI",
            "base_url": "https://fake.example.com",
            "usage_endpoint": "/usage",
            "auth_type": "bearer",
            "field_mapping": {},
        }
        response = await async_client.post(
            "/api/v1/providers/custom", json=payload, headers=headers
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_delete_custom_provider(self, async_client):
        """DELETE /api/v1/providers/custom/{name} removes a custom provider."""
        from tests.test_keys import _register_user

        access_token, _user = await _register_user(async_client, "provuser7@test.com")
        headers = {"Authorization": f"Bearer {access_token}"}

        # First register a custom provider
        payload = {
            "name": "temp-custom",
            "label": "Temporary Custom Provider",
            "base_url": "https://temp.example.com",
            "usage_endpoint": "/usage",
            "auth_type": "bearer",
            "field_mapping": {},
        }
        r = await async_client.post(
            "/api/v1/providers/custom", json=payload, headers=headers
        )
        assert r.status_code == 201

        # Now delete it
        delete_response = await async_client.delete(
            "/api/v1/providers/custom/temp-custom", headers=headers
        )
        assert delete_response.status_code == 200, delete_response.text

        # Should no longer appear in list
        list_response = await async_client.get("/api/v1/providers", headers=headers)
        names = {p["name"] for p in list_response.json()}
        assert "temp-custom" not in names

    @pytest.mark.asyncio
    async def test_delete_custom_provider_not_found_returns_404(self, async_client):
        """Deleting a nonexistent custom provider returns 404."""
        from tests.test_keys import _register_user

        access_token, _user = await _register_user(async_client, "provuser8@test.com")
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await async_client.delete(
            "/api/v1/providers/custom/nonexistent", headers=headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_builtin_provider_returns_403(self, async_client):
        """Cannot delete a built-in provider (only custom)."""
        from tests.test_keys import _register_user

        access_token, _user = await _register_user(async_client, "provuser9@test.com")
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await async_client.delete(
            "/api/v1/providers/custom/openai", headers=headers
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_custom_provider_endpoint_requires_auth(self, async_client):
        """Custom provider endpoints require authentication."""
        # POST requires auth
        r1 = await async_client.post("/api/v1/providers/custom", json={
            "name": "noauth", "label": "No Auth", "base_url": "https://x.com",
            "usage_endpoint": "/u", "auth_type": "bearer", "field_mapping": {},
        })
        assert r1.status_code == 401

        # DELETE requires auth
        r2 = await async_client.delete("/api/v1/providers/custom/something")
        assert r2.status_code == 401
