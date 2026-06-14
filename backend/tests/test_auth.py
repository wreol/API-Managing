"""Tests for authentication: register, login, JWT refresh, and protected routes."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.database import get_db


# Use SQLite for tests so no external PostgreSQL dependency is required.
TEST_DATABASE_URL = "sqlite+aiosqlite://"


@pytest_asyncio.fixture
async def async_client():
    """Create an HTTPX async client targeted at the FastAPI app, with an
    in-memory SQLite database fresh for every test."""
    engine = create_async_engine(TEST_DATABASE_URL)

    # Only create the users table — avoid PostgreSQL-specific types (JSONB, etc.)
    from app.models.user import User

    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create, checkfirst=True)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
    await engine.dispose()


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
class TestRegistration:
    @pytest.mark.asyncio
    async def test_register_success_returns_tokens_and_user(self, async_client):
        payload = {
            "email": "alice@example.com",
            "password": "securepass123",
            "display_name": "Alice",
        }
        response = await async_client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "alice@example.com"
        assert data["user"]["display_name"] == "Alice"
        assert data["user"]["email_verified"] is False
        assert data["user"]["oauth_provider"] is None

    @pytest.mark.asyncio
    async def test_register_duplicate_email_returns_409(self, async_client):
        payload = {
            "email": "bob@example.com",
            "password": "securepass123",
            "display_name": "Bob",
        }
        # First registration
        r1 = await async_client.post("/api/v1/auth/register", json=payload)
        assert r1.status_code == 200

        # Second registration with same email
        r2 = await async_client.post("/api/v1/auth/register", json=payload)
        assert r2.status_code == 409

    @pytest.mark.asyncio
    async def test_register_short_password_returns_422(self, async_client):
        payload = {
            "email": "short@example.com",
            "password": "1234567",  # 7 chars, minimum is 8
            "display_name": "Short",
        }
        response = await async_client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_missing_email_returns_422(self, async_client):
        payload = {
            "password": "securepass123",
            "display_name": "NoEmail",
        }
        response = await async_client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success_returns_tokens_and_user(self, async_client):
        # Register first
        reg_payload = {
            "email": "charlie@example.com",
            "password": "securepass123",
            "display_name": "Charlie",
        }
        await async_client.post("/api/v1/auth/register", json=reg_payload)

        # Now login
        login_payload = {"email": "charlie@example.com", "password": "securepass123"}
        response = await async_client.post("/api/v1/auth/login", json=login_payload)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "charlie@example.com"

    @pytest.mark.asyncio
    async def test_login_wrong_password_returns_401(self, async_client):
        # Register first
        reg_payload = {
            "email": "dave@example.com",
            "password": "securepass123",
            "display_name": "Dave",
        }
        await async_client.post("/api/v1/auth/register", json=reg_payload)

        # Try login with wrong password
        login_payload = {"email": "dave@example.com", "password": "wrongpassword"}
        response = await async_client.post("/api/v1/auth/login", json=login_payload)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_email_returns_401(self, async_client):
        login_payload = {"email": "ghost@example.com", "password": "securepass123"}
        response = await async_client.post("/api/v1/auth/login", json=login_payload)
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Token Refresh
# ---------------------------------------------------------------------------
class TestTokenRefresh:
    @pytest.mark.asyncio
    async def test_refresh_returns_new_token_pair(self, async_client):
        # Register to get tokens
        reg_payload = {
            "email": "eve@example.com",
            "password": "securepass123",
            "display_name": "Eve",
        }
        reg_response = await async_client.post("/api/v1/auth/register", json=reg_payload)
        assert reg_response.status_code == 200
        reg_data = reg_response.json()
        refresh_token = reg_data["refresh_token"]

        # Refresh
        refresh_response = await async_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        assert "access_token" in refresh_data
        assert "refresh_token" in refresh_data
        # Tokens should be different
        assert refresh_data["access_token"] != reg_data["access_token"]
        assert refresh_data["refresh_token"] != reg_data["refresh_token"]

    @pytest.mark.asyncio
    async def test_refresh_invalid_token_returns_401(self, async_client):
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "not.a.valid.token"},
        )
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Protected "me" endpoint
# ---------------------------------------------------------------------------
class TestMeEndpoint:
    @pytest.mark.asyncio
    async def test_me_returns_current_user(self, async_client):
        # Register to get access token
        reg_payload = {
            "email": "frank@example.com",
            "password": "securepass123",
            "display_name": "Frank",
        }
        reg_response = await async_client.post("/api/v1/auth/register", json=reg_payload)
        assert reg_response.status_code == 200
        access_token = reg_response.json()["access_token"]

        # Call /me
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "frank@example.com"
        assert data["display_name"] == "Frank"

    @pytest.mark.asyncio
    async def test_me_no_token_returns_401(self, async_client):
        response = await async_client.get("/api/v1/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_invalid_token_returns_401(self, async_client):
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# JWT token structure
# ---------------------------------------------------------------------------
class TestJWTStructure:
    @pytest.mark.asyncio
    async def test_access_token_has_correct_claims(self, async_client):
        import base64
        import json

        reg_payload = {
            "email": "grace@example.com",
            "password": "securepass123",
            "display_name": "Grace",
        }
        reg_response = await async_client.post("/api/v1/auth/register", json=reg_payload)
        access_token = reg_response.json()["access_token"]

        # Decode the JWT header and payload (without verifying) to check claims
        parts = access_token.split(".")
        assert len(parts) == 3

        # Add padding for base64 decoding
        def decode_jwt_part(part):
            padded = part + "=" * (4 - len(part) % 4)
            return json.loads(base64.urlsafe_b64decode(padded))

        header = decode_jwt_part(parts[0])
        payload = decode_jwt_part(parts[1])

        assert header["alg"] == "HS256"
        assert payload["type"] == "access"
        assert payload["sub"] is not None  # user id
        assert "exp" in payload

    @pytest.mark.asyncio
    async def test_refresh_token_has_correct_claims(self, async_client):
        import base64
        import json

        reg_payload = {
            "email": "heidi@example.com",
            "password": "securepass123",
            "display_name": "Heidi",
        }
        reg_response = await async_client.post("/api/v1/auth/register", json=reg_payload)
        refresh_token = reg_response.json()["refresh_token"]

        parts = refresh_token.split(".")
        assert len(parts) == 3

        def decode_jwt_part(part):
            padded = part + "=" * (4 - len(part) % 4)
            return json.loads(base64.urlsafe_b64decode(padded))

        payload = decode_jwt_part(parts[1])
        assert payload["type"] == "refresh"
        assert payload["sub"] is not None
        assert "exp" in payload
