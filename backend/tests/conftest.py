"""Test fixtures and configuration"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.db.base import Base

# Import all models so they're registered with Base.metadata
from app.db.models.user import User
from app.db.models.team import Team
from app.db.models.player import Player
from app.db.models.game import Game
from app.db.models.pick import Pick
from app.services.player_service import PlayerService
import uuid
import os

# Use PostgreSQL test database
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@db:5432/first6_test",
)


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    # Drop all tables first to ensure clean state
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    """Create test database session"""
    from app.main import app
    from app.db.session import get_db

    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        # Override the get_db dependency to use test session
        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db
        yield session
        app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def player_service(db_session):
    """Create PlayerService instance"""
    return PlayerService(db_session)


@pytest_asyncio.fixture
async def test_team(db_session):
    """Create a test team"""
    team = Team(
        id=uuid.uuid4(),
        external_id="test_team_1",
        name="Test Team",
        abbreviation="TST",
        city="Test City",
    )
    db_session.add(team)
    await db_session.commit()
    await db_session.refresh(team)
    return team
