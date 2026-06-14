"""Shared test fixtures for all backend test modules."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.database import get_db

TEST_DATABASE_URL = "sqlite+aiosqlite://"


@pytest_asyncio.fixture
async def async_client():
    """Create an HTTPX async client with in-memory SQLite and full schema."""
    engine = create_async_engine(TEST_DATABASE_URL)

    from app.models.user import User
    from app.models.api_key import ApiKey
    from app.models.audit_log import AuditLog
    from app.models.key_share import KeyShare
    from app.models.usage_record import UsageRecord
    from app.models.alert_rule import AlertRule
    from app.models.alert_event import AlertEvent

    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create, checkfirst=True)
        await conn.run_sync(ApiKey.__table__.create, checkfirst=True)
        await conn.run_sync(AuditLog.__table__.create, checkfirst=True)
        await conn.run_sync(KeyShare.__table__.create, checkfirst=True)
        await conn.run_sync(UsageRecord.__table__.create, checkfirst=True)
        await conn.run_sync(AlertRule.__table__.create, checkfirst=True)
        await conn.run_sync(AlertEvent.__table__.create, checkfirst=True)

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


@pytest_asyncio.fixture
async def db_session():
    """Create a fresh test database session with all tables.

    Tables are created before the test and dropped after.
    """
    from app.models.user import Base

    TEST_DATABASE_URL_ASYNC = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/api_vault_test"
    )
    engine = create_async_engine(TEST_DATABASE_URL_ASYNC)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()
