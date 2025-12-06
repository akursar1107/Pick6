"""Test player API endpoints"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from app.main import app
from app.db.models.player import Player
from app.db.models.team import Team
from app.db.models.user import User
from app.core.security import create_access_token
import uuid


@pytest_asyncio.fixture
async def test_user(db_session):
    """Create a test user"""
    user = User(
        id=uuid.uuid4(),
        email="testuser@example.com",
        username="testuser",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_token(test_user):
    """Create authentication token for test user"""
    token = create_access_token(test_user.id)
    return token


@pytest_asyncio.fixture
async def auth_headers(auth_token):
    """Create authentication headers"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.mark.asyncio
async def test_search_players_endpoint(db_session, test_team, auth_headers):
    """Test the player search endpoint"""
    # Setup: Create test players
    player1 = Player(
        id=uuid.uuid4(),
        external_id="test_player_1",
        name="Patrick Mahomes",
        team_id=test_team.id,
        position="QB",
        is_active=True,
    )
    player2 = Player(
        id=uuid.uuid4(),
        external_id="test_player_2",
        name="Travis Kelce",
        team_id=test_team.id,
        position="TE",
        is_active=True,
    )
    db_session.add(player1)
    db_session.add(player2)
    await db_session.commit()

    # Test: Search for players
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/players/search?q=Patrick", headers=auth_headers
        )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(p["name"] == "Patrick Mahomes" for p in data)


@pytest.mark.asyncio
async def test_get_player_by_id_endpoint(db_session, test_team, auth_headers):
    """Test the get player by ID endpoint"""
    # Setup: Create test player
    player = Player(
        id=uuid.uuid4(),
        external_id="test_player_3",
        name="Patrick Mahomes",
        team_id=test_team.id,
        position="QB",
        is_active=True,
    )
    db_session.add(player)
    await db_session.commit()

    # Test: Get player by ID
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/players/{player.id}", headers=auth_headers
        )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Patrick Mahomes"
    assert data["position"] == "QB"
    assert data["team"] == "TST"  # Test team abbreviation


@pytest.mark.asyncio
async def test_get_player_not_found(db_session, auth_headers):
    """Test getting a non-existent player"""
    # Test: Get non-existent player
    fake_id = uuid.uuid4()
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/api/v1/players/{fake_id}", headers=auth_headers)

    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_search_players_empty_results(db_session, auth_headers):
    """Test searching with no matches"""
    # Test: Search for non-existent player
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/players/search?q=NonExistentPlayer", headers=auth_headers
        )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


@pytest.mark.asyncio
async def test_search_players_unauthenticated(db_session):
    """Test that player search requires authentication"""
    # Test: Search without authentication
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/players/search?q=Patrick")

    # Assert: Should return 403 Forbidden (HTTPBearer returns 403 when no credentials)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_player_unauthenticated(db_session, test_team):
    """Test that get player by ID requires authentication"""
    # Setup: Create test player
    player = Player(
        id=uuid.uuid4(),
        external_id="test_player_4",
        name="Test Player",
        team_id=test_team.id,
        position="QB",
        is_active=True,
    )
    db_session.add(player)
    await db_session.commit()

    # Test: Get player without authentication
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/api/v1/players/{player.id}")

    # Assert: Should return 403 Forbidden (HTTPBearer returns 403 when no credentials)
    assert response.status_code == 403
