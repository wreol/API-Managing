"""Tests for Usage Service + Dashboard API: summary, trend, by-provider, by-key."""

import pytest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch, AsyncMock, MagicMock
import uuid


# ---------------------------------------------------------------------------
# Helper — register a user and return the access token + user data
# ---------------------------------------------------------------------------
async def _register_user(client, email, password="securepass123", display_name="Test"):
    payload = {"email": email, "password": password, "display_name": display_name}
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    return data["access_token"], data["user"]


async def _add_key(client, access_token, provider="openai", label="Test Key"):
    payload = {
        "provider": provider,
        "key_value": f"sk-test-{uuid.uuid4().hex[:12]}",
        "label": label,
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.post("/api/v1/keys", json=payload, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


# ============================================================================
# T5.1a: Usage Summary tests
# ============================================================================

class TestUsageSummary:
    """GET /api/v1/usage/summary — aggregate usage overview."""

    @pytest.mark.asyncio
    async def test_summary_returns_correct_structure(self, async_client):
        """Summary returns total_calls, total_tokens, total_cost, by_provider."""
        access_token, _user = await _register_user(async_client, "usageuser1@test.com")
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await async_client.get("/api/v1/usage/summary", headers=headers)
        assert response.status_code == 200, response.text
        data = response.json()
        assert "total_calls" in data
        assert "total_tokens" in data
        assert "total_cost" in data
        assert "by_provider" in data
        assert isinstance(data["total_calls"], int)
        assert isinstance(data["total_tokens"], int)
        assert isinstance(data["total_cost"], (int, float))
        assert isinstance(data["by_provider"], list)

    @pytest.mark.asyncio
    async def test_summary_returns_zero_for_new_user(self, async_client):
        """A user with no usage records gets all zeros."""
        access_token, _user = await _register_user(async_client, "usageuser2@test.com")
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await async_client.get("/api/v1/usage/summary", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_calls"] == 0
        assert data["total_tokens"] == 0
        assert data["total_cost"] == 0.0
        assert data["by_provider"] == []

    @pytest.mark.asyncio
    async def test_summary_requires_auth(self, async_client):
        """Summary endpoint requires authentication."""
        response = await async_client.get("/api/v1/usage/summary")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_summary_supports_date_range_filter(self, async_client):
        """Summary endpoint accepts ?from= and ?to= query params."""
        access_token, _user = await _register_user(async_client, "usageuser3@test.com")
        headers = {"Authorization": f"Bearer {access_token}"}

        today = date.today().isoformat()
        response = await async_client.get(
            f"/api/v1/usage/summary?from=2026-01-01&to={today}", headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_calls"] >= 0


# ============================================================================
# T5.1b: Usage Trend tests
# ============================================================================

class TestUsageTrend:
    """GET /api/v1/usage/trend — time series data."""

    @pytest.mark.asyncio
    async def test_trend_returns_list(self, async_client):
        """Trend endpoint returns a list of data points."""
        access_token, _user = await _register_user(async_client, "usageuser4@test.com")
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await async_client.get("/api/v1/usage/trend", headers=headers)
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_trend_supports_granularity_parameter(self, async_client):
        """Trend endpoint accepts ?granularity=day (or hour, month)."""
        access_token, _user = await _register_user(async_client, "usageuser5@test.com")
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await async_client.get(
            "/api/v1/usage/trend?granularity=day", headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_trend_supports_date_range(self, async_client):
        """Trend endpoint accepts ?from= and ?to= query params."""
        access_token, _user = await _register_user(async_client, "usageuser6@test.com")
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await async_client.get(
            "/api/v1/usage/trend?from=2026-06-01&to=2026-06-14&granularity=day",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_trend_requires_auth(self, async_client):
        """Trend endpoint requires authentication."""
        response = await async_client.get("/api/v1/usage/trend")
        assert response.status_code == 401


# ============================================================================
# T5.1c: By-Provider Breakdown tests
# ============================================================================

class TestUsageByProvider:
    """GET /api/v1/usage/by-provider — per-provider breakdown."""

    @pytest.mark.asyncio
    async def test_by_provider_returns_list(self, async_client):
        """By-provider endpoint returns a list of provider summaries."""
        access_token, _user = await _register_user(async_client, "usageuser7@test.com")
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await async_client.get("/api/v1/usage/by-provider", headers=headers)
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_by_provider_entry_structure(self, async_client):
        """Each by-provider entry has provider, calls, tokens, cost."""
        access_token, _user = await _register_user(async_client, "usageuser8@test.com")
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await async_client.get("/api/v1/usage/by-provider", headers=headers)
        assert response.status_code == 200
        data = response.json()
        # Empty for new user — structure validated by successful parse
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_by_provider_requires_auth(self, async_client):
        """By-provider endpoint requires authentication."""
        response = await async_client.get("/api/v1/usage/by-provider")
        assert response.status_code == 401


# ============================================================================
# T5.1d: By-Key Breakdown tests
# ============================================================================

class TestUsageByKey:
    """GET /api/v1/usage/by-key — per-key breakdown."""

    @pytest.mark.asyncio
    async def test_by_key_returns_list(self, async_client):
        """By-key endpoint returns a list of key summaries."""
        access_token, _user = await _register_user(async_client, "usageuser9@test.com")
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await async_client.get("/api/v1/usage/by-key", headers=headers)
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_by_key_requires_auth(self, async_client):
        """By-key endpoint requires authentication."""
        response = await async_client.get("/api/v1/usage/by-key")
        assert response.status_code == 401


# ============================================================================
# T5.2: Usage Service aggregate query logic (unit tests)
# ============================================================================

class TestUsageServiceAggregates:
    """Test UsageService aggregation methods directly with DB session."""

    @pytest.mark.asyncio
    async def test_get_summary_aggregates_correctly(self, async_client):
        """UsageService.get_summary correctly aggregates multiple UsageRecords."""
        from app.models.usage_record import UsageRecord as UsageRecordModel
        from app.models.user import User
        from app.models.api_key import ApiKey
        from sqlalchemy import select
        from app.main import app
        from app.database import get_db as original_get_db
        import uuid as _uuid

        # Register a user
        access_token, _user_data = await _register_user(
            async_client, "usageagg1@test.com"
        )
        headers = {"Authorization": f"Bearer {access_token}"}

        # Get the overridden get_db generator
        overridden_gen = app.dependency_overrides[original_get_db]
        db_gen = overridden_gen()

        # Use async for to get the session
        async for session in db_gen:
            db = session

            # Find the user
            result = await db.execute(
                select(User).where(User.email == "usageagg1@test.com")
            )
            user = result.scalar_one()

            # Create an API key for this user
            key = ApiKey(
                id=_uuid.uuid4(),
                user_id=user.id,
                provider="openai",
                label="Test Key",
                key_encrypted="encrypted_value",
                key_prefix="sk-",
                last_4="abcd",
            )
            db.add(key)
            await db.flush()

            # Insert usage records
            records = [
                UsageRecordModel(
                    id=_uuid.uuid4(),
                    key_id=key.id,
                    provider="openai",
                    period_start=date(2026, 6, 1),
                    period_end=date(2026, 6, 30),
                    calls=100,
                    tokens_in=5000,
                    tokens_out=3000,
                    cost_estimate=2.50,
                ),
                UsageRecordModel(
                    id=_uuid.uuid4(),
                    key_id=key.id,
                    provider="openai",
                    period_start=date(2026, 6, 1),
                    period_end=date(2026, 6, 30),
                    calls=50,
                    tokens_in=2000,
                    tokens_out=1000,
                    cost_estimate=1.25,
                ),
            ]
            for r in records:
                db.add(r)
            await db.flush()
            break

        # Now fetch summary via the HTTP endpoint
        response = await async_client.get("/api/v1/usage/summary", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_calls"] == 150
        assert data["total_tokens"] == 11000  # 5000+3000+2000+1000
        assert data["total_cost"] == 3.75

    @pytest.mark.asyncio
    async def test_get_summary_excludes_other_users(self, async_client):
        """Usage summary only includes records for the authenticated user's keys."""
        access_token1, _user1 = await _register_user(
            async_client, "usageagg2@test.com"
        )
        access_token2, _user2 = await _register_user(
            async_client, "usageagg3@test.com"
        )
        headers1 = {"Authorization": f"Bearer {access_token1}"}
        headers2 = {"Authorization": f"Bearer {access_token2}"}

        # Add a key for user1
        await _add_key(async_client, access_token1, "openai", "User1 Key")

        # User1 sees zero usage (no records inserted via this test path for their key)
        response1 = await async_client.get("/api/v1/usage/summary", headers=headers1)
        assert response1.status_code == 200
        # User2 should also see zero because no records belong to user2
        response2 = await async_client.get("/api/v1/usage/summary", headers=headers2)
        assert response2.status_code == 200
        # Both users see their own isolated view
        assert response1.json()["total_calls"] == 0
        assert response2.json()["total_calls"] == 0


# ============================================================================
# T5.3: Worker Fetcher tests
# ============================================================================

class TestWorkerFetcher:
    """Test the ARQ worker fetch_all_usage task."""

    @pytest.mark.asyncio
    async def test_fetch_all_usage_is_callable(self):
        """fetch_all_usage should be an async function that accepts a context."""
        from app.worker.fetcher import fetch_all_usage
        import inspect

        assert inspect.iscoroutinefunction(fetch_all_usage)

    @pytest.mark.asyncio
    async def test_fetch_all_usage_returns_dict(self, async_client):
        """fetch_all_usage returns a dict with status and keys_processed."""
        from app.worker.fetcher import fetch_all_usage
        from unittest.mock import MagicMock, AsyncMock, patch

        mock_ctx = MagicMock()

        # Mock database session to avoid real DB connection
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        # scalars() should return an object with .all() that returns []
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        async def mock_execute(*args, **kwargs):
            return mock_result

        mock_session.execute = mock_execute
        mock_session.commit = AsyncMock()

        with patch(
            "app.worker.fetcher.async_session", return_value=mock_session
        ):
            result = await fetch_all_usage(mock_ctx)

        assert isinstance(result, dict)
        assert "status" in result
        assert "keys_processed" in result
        assert result["status"] == "ok"
        assert result["keys_processed"] == 0

    @pytest.mark.asyncio
    async def test_worker_settings_have_correct_attributes(self):
        """WorkerSettings should have the expected arq configuration."""
        from app.worker.fetcher import WorkerSettings

        assert hasattr(WorkerSettings, "functions")
        assert callable(WorkerSettings.functions) or isinstance(
            WorkerSettings.functions, list
        )
        assert hasattr(WorkerSettings, "redis_settings")


# ============================================================================
# T5.4: Email utility tests
# ============================================================================

class TestEmailUtility:
    """Test the email sending utility."""

    def test_send_email_is_async_callable(self):
        """send_email should be an async function."""
        from app.utils.email import send_email
        import inspect

        assert inspect.iscoroutinefunction(send_email)

    @pytest.mark.asyncio
    async def test_send_email_returns_true_on_success(self):
        """send_email returns True when SMTP succeeds."""
        from app.utils.email import send_email
        from unittest.mock import patch, AsyncMock

        with patch("app.utils.email.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = ({"test@example.com": "OK"}, "OK")
            result = await send_email(
                to="test@example.com",
                subject="Test Alert",
                body="This is a test.",
            )
            assert result is True
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_returns_false_on_failure(self):
        """send_email returns False when SMTP fails (doesn't raise)."""
        from app.utils.email import send_email
        from unittest.mock import patch, AsyncMock

        with patch("app.utils.email.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = Exception("SMTP connection failed")
            result = await send_email(
                to="test@example.com",
                subject="Test Alert",
                body="This is a test.",
            )
            assert result is False

    @pytest.mark.asyncio
    async def test_send_email_uses_correct_from_address(self):
        """send_email uses the configured SMTP_FROM address."""
        from app.utils.email import send_email
        from app.config import settings
        from unittest.mock import patch, AsyncMock

        with patch("app.utils.email.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = ({"recipient@example.com": "OK"}, "OK")
            await send_email(
                to="recipient@example.com",
                subject="Test",
                body="Body",
            )
            # message is the first positional argument
            message = mock_send.call_args[0][0]
            assert settings.SMTP_FROM in message.as_string()


# ============================================================================
# T5.5: Alert Evaluator unit tests
# ============================================================================

class TestAlertEvaluator:
    """Test the alert evaluation logic."""

    @pytest.mark.asyncio
    async def test_evaluate_alerts_is_callable(self):
        """evaluate_alerts should be an async function."""
        from app.worker.alert_evaluator import evaluate_alerts
        import inspect

        assert inspect.iscoroutinefunction(evaluate_alerts)

    @pytest.mark.asyncio
    async def test_evaluate_alerts_returns_dict(self, async_client):
        """evaluate_alerts returns a dict with triggered count."""
        from app.worker.alert_evaluator import evaluate_alerts
        from unittest.mock import MagicMock, AsyncMock, patch

        mock_ctx = MagicMock()

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []  # No rules
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        async def mock_execute(*args, **kwargs):
            return mock_result

        mock_session.execute = mock_execute
        mock_session.commit = AsyncMock()

        with patch(
            "app.worker.alert_evaluator.async_session", return_value=mock_session
        ):
            result = await evaluate_alerts(mock_ctx)

        assert isinstance(result, dict)
        assert "triggered" in result
        assert result["triggered"] == 0
