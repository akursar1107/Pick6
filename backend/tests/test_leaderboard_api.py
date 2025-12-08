"""Unit tests for Leaderboard API endpoints"""

import pytest
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime, timezone
from app.db.models.user import User
from app.db.models.game import Game, GameStatus, GameType
from app.db.models.team import Team
from app.db.models.player import Player
from app.db.models.pick import Pick, PickResult


@pytest.mark.asyncio
async def test_get_season_leaderboard_success(client: AsyncClient, db_session):
    """
    Test successful retrieval of season leaderboard

    Validates: Requirements 1.1, 1.2
    """
    # Setup: Create test data
    test_run_id = uuid4().hex[:8]
    season = 2024

    # Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"team_home_{test_run_id}",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    away_team = Team(
        id=uuid4(),
        external_id=f"team_away_{test_run_id}",
        name="Away Team",
        abbreviation="AWY",
        city="Away City",
    )
    db_session.add(home_team)
    db_session.add(away_team)
    await db_session.flush()

    # Create player
    player = Player(
        id=uuid4(),
        external_id=f"player_{test_run_id}",
        name="Test Player",
        position="RB",
        team_id=home_team.id,
    )
    db_session.add(player)
    await db_session.flush()

    # Create game
    game = Game(
        id=uuid4(),
        external_id=f"game_{test_run_id}",
        season_year=season,
        week_number=1,
        game_type=GameType.SUNDAY_MAIN,
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        game_date=datetime(2024, 9, 1, 13, 0, tzinfo=timezone.utc),
        kickoff_time=datetime(2024, 9, 1, 13, 0, tzinfo=timezone.utc),
        status=GameStatus.COMPLETED,
    )
    db_session.add(game)
    await db_session.flush()

    # Create users and picks
    user1 = User(
        id=uuid4(),
        email=f"user1_{test_run_id}@test.com",
        username=f"user1_{test_run_id}",
        display_name="User 1",
        is_active=True,
    )
    user2 = User(
        id=uuid4(),
        email=f"user2_{test_run_id}@test.com",
        username=f"user2_{test_run_id}",
        display_name="User 2",
        is_active=True,
    )
    db_session.add(user1)
    db_session.add(user2)
    await db_session.flush()

    # User 1 wins
    pick1 = Pick(
        id=uuid4(),
        user_id=user1.id,
        game_id=game.id,
        player_id=player.id,
        status=PickResult.WIN,
        ftd_points=3,
        attd_points=1,
        total_points=4,
        scored_at=datetime.now(timezone.utc),
    )
    # User 2 loses
    pick2 = Pick(
        id=uuid4(),
        user_id=user2.id,
        game_id=game.id,
        player_id=player.id,
        status=PickResult.LOSS,
        ftd_points=0,
        attd_points=0,
        total_points=0,
        scored_at=datetime.now(timezone.utc),
    )
    db_session.add(pick1)
    db_session.add(pick2)
    await db_session.commit()

    # Action: Get season leaderboard
    response = await client.get(f"/api/v1/leaderboard/season/{season}")

    # Assert: Should return 200 with leaderboard data
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2

    # Verify ranking order
    assert data[0]["rank"] == 1
    assert data[0]["username"] == f"user1_{test_run_id}"
    assert data[0]["total_points"] == 4

    assert data[1]["rank"] == 2
    assert data[1]["username"] == f"user2_{test_run_id}"
    assert data[1]["total_points"] == 0


@pytest.mark.asyncio
async def test_get_season_leaderboard_invalid_season(client: AsyncClient):
    """
    Test season leaderboard with invalid season parameter

    Validates: Error handling for invalid season (400)
    """
    # Action: Request with invalid season (too old)
    response = await client.get("/api/v1/leaderboard/season/1999")

    # Assert: Should return 400
    assert response.status_code == 400
    assert "Invalid season" in response.json()["detail"]

    # Action: Request with invalid season (too far in future)
    response = await client.get("/api/v1/leaderboard/season/2099")

    # Assert: Should return 400
    assert response.status_code == 400
    assert "Invalid season" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_weekly_leaderboard_success(client: AsyncClient, db_session):
    """
    Test successful retrieval of weekly leaderboard

    Validates: Requirements 2.1, 2.2
    """
    # Setup: Create test data
    test_run_id = uuid4().hex[:8]
    season = 2024
    week = 1

    # Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"team_home_{test_run_id}",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    away_team = Team(
        id=uuid4(),
        external_id=f"team_away_{test_run_id}",
        name="Away Team",
        abbreviation="AWY",
        city="Away City",
    )
    db_session.add(home_team)
    db_session.add(away_team)
    await db_session.flush()

    # Create player
    player = Player(
        id=uuid4(),
        external_id=f"player_{test_run_id}",
        name="Test Player",
        position="RB",
        team_id=home_team.id,
    )
    db_session.add(player)
    await db_session.flush()

    # Create game
    game = Game(
        id=uuid4(),
        external_id=f"game_{test_run_id}",
        season_year=season,
        week_number=week,
        game_type=GameType.SUNDAY_MAIN,
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        game_date=datetime(2024, 9, 1, 13, 0, tzinfo=timezone.utc),
        kickoff_time=datetime(2024, 9, 1, 13, 0, tzinfo=timezone.utc),
        status=GameStatus.COMPLETED,
    )
    db_session.add(game)
    await db_session.flush()

    # Create user and pick
    user = User(
        id=uuid4(),
        email=f"user_{test_run_id}@test.com",
        username=f"user_{test_run_id}",
        display_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    pick = Pick(
        id=uuid4(),
        user_id=user.id,
        game_id=game.id,
        player_id=player.id,
        status=PickResult.WIN,
        ftd_points=3,
        attd_points=1,
        total_points=4,
        scored_at=datetime.now(timezone.utc),
    )
    db_session.add(pick)
    await db_session.commit()

    # Action: Get weekly leaderboard
    response = await client.get(f"/api/v1/leaderboard/week/{season}/{week}")

    # Assert: Should return 200 with leaderboard data
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["username"] == f"user_{test_run_id}"
    assert data[0]["total_points"] == 4


@pytest.mark.asyncio
async def test_get_weekly_leaderboard_invalid_week(client: AsyncClient):
    """
    Test weekly leaderboard with invalid week parameter

    Validates: Error handling for invalid week (400)
    """
    season = 2024

    # Action: Request with invalid week (too low)
    response = await client.get(f"/api/v1/leaderboard/week/{season}/0")

    # Assert: Should return 400
    assert response.status_code == 400
    assert "Invalid week" in response.json()["detail"]

    # Action: Request with invalid week (too high)
    response = await client.get(f"/api/v1/leaderboard/week/{season}/19")

    # Assert: Should return 400
    assert response.status_code == 400
    assert "Invalid week" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_user_stats_success(client: AsyncClient, db_session):
    """
    Test successful retrieval of user statistics

    Validates: Requirements 3.1, 3.2
    """
    # Setup: Create test data
    test_run_id = uuid4().hex[:8]
    season = 2024

    # Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"team_home_{test_run_id}",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    away_team = Team(
        id=uuid4(),
        external_id=f"team_away_{test_run_id}",
        name="Away Team",
        abbreviation="AWY",
        city="Away City",
    )
    db_session.add(home_team)
    db_session.add(away_team)
    await db_session.flush()

    # Create player
    player = Player(
        id=uuid4(),
        external_id=f"player_{test_run_id}",
        name="Test Player",
        position="RB",
        team_id=home_team.id,
    )
    db_session.add(player)
    await db_session.flush()

    # Create game
    game = Game(
        id=uuid4(),
        external_id=f"game_{test_run_id}",
        season_year=season,
        week_number=1,
        game_type=GameType.SUNDAY_MAIN,
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        game_date=datetime(2024, 9, 1, 13, 0, tzinfo=timezone.utc),
        kickoff_time=datetime(2024, 9, 1, 13, 0, tzinfo=timezone.utc),
        status=GameStatus.COMPLETED,
    )
    db_session.add(game)
    await db_session.flush()

    # Create user and pick
    user = User(
        id=uuid4(),
        email=f"user_{test_run_id}@test.com",
        username=f"user_{test_run_id}",
        display_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    pick = Pick(
        id=uuid4(),
        user_id=user.id,
        game_id=game.id,
        player_id=player.id,
        status=PickResult.WIN,
        ftd_points=3,
        attd_points=1,
        total_points=4,
        scored_at=datetime.now(timezone.utc),
    )
    db_session.add(pick)
    await db_session.commit()

    # Action: Get user stats
    response = await client.get(f"/api/v1/leaderboard/user/{user.id}/stats")

    # Assert: Should return 200 with user stats
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == f"user_{test_run_id}"
    assert data["total_points"] == 4
    assert data["total_wins"] == 1
    assert data["total_losses"] == 0
    assert "current_streak" in data
    assert "ftd_points" in data
    assert "attd_points" in data


@pytest.mark.asyncio
async def test_get_user_stats_not_found(client: AsyncClient):
    """
    Test user stats with non-existent user

    Validates: Error handling for user not found (404)
    """
    # Action: Request stats for non-existent user
    fake_user_id = uuid4()
    response = await client.get(f"/api/v1/leaderboard/user/{fake_user_id}/stats")

    # Assert: Should return 404
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_export_leaderboard_csv(client: AsyncClient, db_session, redis_client):
    """
    Test CSV export of leaderboard

    Validates: Requirements 10.1, 10.2
    """
    # Setup: Create test data
    test_run_id = uuid4().hex[:8]
    # Use unique season to avoid conflicts with other tests (within valid range 2020-2026)
    season = 2020 + (hash(test_run_id) % 7)

    # Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"team_home_{test_run_id}",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    away_team = Team(
        id=uuid4(),
        external_id=f"team_away_{test_run_id}",
        name="Away Team",
        abbreviation="AWY",
        city="Away City",
    )
    db_session.add(home_team)
    db_session.add(away_team)
    await db_session.flush()

    # Create player
    player = Player(
        id=uuid4(),
        external_id=f"player_{test_run_id}",
        name="Test Player",
        position="RB",
        team_id=home_team.id,
    )
    db_session.add(player)
    await db_session.flush()

    # Create game
    game = Game(
        id=uuid4(),
        external_id=f"game_{test_run_id}",
        season_year=season,
        week_number=1,
        game_type=GameType.SUNDAY_MAIN,
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        game_date=datetime(2024, 9, 1, 13, 0, tzinfo=timezone.utc),
        kickoff_time=datetime(2024, 9, 1, 13, 0, tzinfo=timezone.utc),
        status=GameStatus.COMPLETED,
    )
    db_session.add(game)
    await db_session.flush()

    # Create user and pick
    user = User(
        id=uuid4(),
        email=f"user_{test_run_id}@test.com",
        username=f"user_{test_run_id}",
        display_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    pick = Pick(
        id=uuid4(),
        user_id=user.id,
        game_id=game.id,
        player_id=player.id,
        status=PickResult.WIN,
        ftd_points=3,
        attd_points=1,
        total_points=4,
        scored_at=datetime.now(timezone.utc),
    )
    db_session.add(pick)
    await db_session.commit()

    # Action: Export as CSV
    response = await client.get(f"/api/v1/leaderboard/export/{season}?format=csv")

    # Assert: Should return 200 with CSV content
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]
    assert f"leaderboard_season_{season}.csv" in response.headers["content-disposition"]

    # Verify CSV content
    content = response.text
    assert "Rank" in content
    assert "Username" in content
    assert "Total Points" in content
    assert f"user_{test_run_id}" in content


@pytest.mark.asyncio
async def test_export_leaderboard_json(client: AsyncClient, db_session, redis_client):
    """
    Test JSON export of leaderboard

    Validates: Requirements 10.1, 10.2
    """
    # Setup: Create test data
    test_run_id = uuid4().hex[:8]
    # Use unique season to avoid conflicts with other tests (within valid range 2020-2026)
    # Use a different offset than CSV test to reduce collision probability
    season = 2021 + (abs(hash(test_run_id)) % 5)

    # Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"team_home_{test_run_id}",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    away_team = Team(
        id=uuid4(),
        external_id=f"team_away_{test_run_id}",
        name="Away Team",
        abbreviation="AWY",
        city="Away City",
    )
    db_session.add(home_team)
    db_session.add(away_team)
    await db_session.flush()

    # Create player
    player = Player(
        id=uuid4(),
        external_id=f"player_{test_run_id}",
        name="Test Player",
        position="RB",
        team_id=home_team.id,
    )
    db_session.add(player)
    await db_session.flush()

    # Create game
    game = Game(
        id=uuid4(),
        external_id=f"game_{test_run_id}",
        season_year=season,
        week_number=1,
        game_type=GameType.SUNDAY_MAIN,
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        game_date=datetime(2024, 9, 1, 13, 0, tzinfo=timezone.utc),
        kickoff_time=datetime(2024, 9, 1, 13, 0, tzinfo=timezone.utc),
        status=GameStatus.COMPLETED,
    )
    db_session.add(game)
    await db_session.flush()

    # Create user and pick
    user = User(
        id=uuid4(),
        email=f"user_{test_run_id}@test.com",
        username=f"user_{test_run_id}",
        display_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    pick = Pick(
        id=uuid4(),
        user_id=user.id,
        game_id=game.id,
        player_id=player.id,
        status=PickResult.WIN,
        ftd_points=3,
        attd_points=1,
        total_points=4,
        scored_at=datetime.now(timezone.utc),
    )
    db_session.add(pick)
    await db_session.commit()

    # Action: Export as JSON
    response = await client.get(f"/api/v1/leaderboard/export/{season}?format=json")

    # Assert: Should return 200 with JSON content
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert "attachment" in response.headers["content-disposition"]
    assert (
        f"leaderboard_season_{season}.json" in response.headers["content-disposition"]
    )

    # Verify JSON content
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["username"] == f"user_{test_run_id}"
    assert data[0]["total_points"] == 4


@pytest.mark.asyncio
async def test_export_leaderboard_weekly(client: AsyncClient, db_session):
    """
    Test weekly export with week parameter

    Validates: Requirements 10.3, 10.4
    """
    # Setup: Create test data
    test_run_id = uuid4().hex[:8]
    season = 2024
    week = 5

    # Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"team_home_{test_run_id}",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    away_team = Team(
        id=uuid4(),
        external_id=f"team_away_{test_run_id}",
        name="Away Team",
        abbreviation="AWY",
        city="Away City",
    )
    db_session.add(home_team)
    db_session.add(away_team)
    await db_session.flush()

    # Create player
    player = Player(
        id=uuid4(),
        external_id=f"player_{test_run_id}",
        name="Test Player",
        position="RB",
        team_id=home_team.id,
    )
    db_session.add(player)
    await db_session.flush()

    # Create game
    game = Game(
        id=uuid4(),
        external_id=f"game_{test_run_id}",
        season_year=season,
        week_number=week,
        game_type=GameType.SUNDAY_MAIN,
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        game_date=datetime(2024, 9, week, 13, 0, tzinfo=timezone.utc),
        kickoff_time=datetime(2024, 9, week, 13, 0, tzinfo=timezone.utc),
        status=GameStatus.COMPLETED,
    )
    db_session.add(game)
    await db_session.flush()

    # Create user and pick
    user = User(
        id=uuid4(),
        email=f"user_{test_run_id}@test.com",
        username=f"user_{test_run_id}",
        display_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    pick = Pick(
        id=uuid4(),
        user_id=user.id,
        game_id=game.id,
        player_id=player.id,
        status=PickResult.WIN,
        ftd_points=3,
        attd_points=1,
        total_points=4,
        scored_at=datetime.now(timezone.utc),
    )
    db_session.add(pick)
    await db_session.commit()

    # Action: Export weekly data
    response = await client.get(
        f"/api/v1/leaderboard/export/{season}?week={week}&format=csv"
    )

    # Assert: Should return 200 with correct filename
    assert response.status_code == 200
    assert "attachment" in response.headers["content-disposition"]
    # Filename should include both season and week
    assert (
        f"leaderboard_season_{season}_week_{week}.csv"
        in response.headers["content-disposition"]
    )
