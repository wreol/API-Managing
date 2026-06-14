"""Test fixtures for backend tests."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.models.user import Base

TEST_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/api_vault_test"
)


@pytest_asyncio.fixture
async def db_session():
    """Create a fresh test database session with all tables.

    Tables are created before the test and dropped after.
    """
    engine = create_async_engine(TEST_DATABASE_URL)

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
