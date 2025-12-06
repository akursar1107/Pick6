"""Integration tests for complete pick submission flow"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from app.main import app
from app.db.models.player import Player
from app.db.models.team import Team
from app.db.models.game import Game
from app.db.models.user import User
from app.db.models.pick import Pick
from app.core.security import get_password_hash, create_access_token
from datetime import datetime, timedelta, timezone
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


@pytest_asyncio.fixture
async def test_teams(db_session):
    """Create test teams"""
    team1 = Team(
        id=uuid.uuid4(),
        external_id="team_1",
        name="Chiefs",
        abbreviation="KC",
        city="Kansas City",
    )
    team2 = Team(
        id=uuid.uuid4(),
        external_id="team_2",
        name="Bills",
        abbreviation="BUF",
        city="Buffalo",
    )
    db_session.add(team1)
    db_session.add(team2)
    await db_session.commit()
    await db_session.refresh(team1)
    await db_session.refresh(team2)
    return team1, team2


@pytest_asyncio.fixture
async def test_players(db_session, test_teams):
    """Create test players"""
    team1, team2 = test_teams
    player1 = Player(
        id=uuid.uuid4(),
        external_id="player_1",
        name="Patrick Mahomes",
        team_id=team1.id,
        position="QB",
        is_active=True,
    )
    player2 = Player(
        id=uuid.uuid4(),
        external_id="player_2",
        name="Travis Kelce",
        team_id=team1.id,
        position="TE",
        is_active=True,
    )
    player3 = Player(
        id=uuid.uuid4(),
        external_id="player_3",
        name="Josh Allen",
        team_id=team2.id,
        position="QB",
        is_active=True,
    )
    db_session.add(player1)
    db_session.add(player2)
    db_session.add(player3)
    await db_session.commit()
    await db_session.refresh(player1)
    await db_session.refresh(player2)
    await db_session.refresh(player3)
    return player1, player2, player3


@pytest_asyncio.fixture
async def test_game(db_session, test_teams):
    """Create a test game with future kickoff"""
    from app.db.models.game import GameType, GameStatus

    team1, team2 = test_teams
    kickoff = datetime.now(timezone.utc) + timedelta(hours=2)
    game = Game(
        id=uuid.uuid4(),
        external_id="game_1",
        home_team_id=team1.id,
        away_team_id=team2.id,
        kickoff_time=kickoff,
        game_date=kickoff,
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.SCHEDULED,
    )
    db_session.add(game)
    await db_session.commit()
    await db_session.refresh(game)
    return game


@pytest.mark.asyncio
async def test_complete_pick_submission_flow(
    db_session, test_user, auth_token, test_game, test_players
):
    """
    Test complete pick submission flow: create, view, update, delete
    Requirements: 1.1, 2.1, 3.1, 4.1
    """
    player1, player2, player3 = test_players
    headers = {"Authorization": f"Bearer {auth_token}"}

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Step 1: Create a pick
        create_response = await client.post(
            "/api/v1/picks/",
            json={"game_id": str(test_game.id), "player_id": str(player1.id)},
            headers=headers,
        )
        assert (
            create_response.status_code == 201
        ), f"Failed to create pick: {create_response.json()}"
        pick_data = create_response.json()
        pick_id = pick_data["id"]
        assert pick_data["status"] == "pending"
        assert pick_data["player_id"] == str(player1.id)
        assert pick_data["game_id"] == str(test_game.id)

        # Step 2: Verify pick appears in MyPicks (GET /picks)
        get_picks_response = await client.get("/api/v1/picks/", headers=headers)
        assert get_picks_response.status_code == 200
        picks = get_picks_response.json()
        assert len(picks) == 1
        assert picks[0]["id"] == pick_id
        # Note: Nested player/game data may not be loaded in all responses
        assert picks[0]["player_id"] == str(player1.id)

        # Step 3: Update the pick to a different player
        update_response = await client.patch(
            f"/api/v1/picks/{pick_id}",
            json={"player_id": str(player2.id)},
            headers=headers,
        )
        assert update_response.status_code == 200
        updated_pick = update_response.json()
        assert updated_pick["player_id"] == str(player2.id)
        assert updated_pick["id"] == pick_id

        # Step 4: Verify the update persisted
        get_pick_response = await client.get(
            f"/api/v1/picks/{pick_id}", headers=headers
        )
        assert get_pick_response.status_code == 200
        fetched_pick = get_pick_response.json()
        assert fetched_pick["player_id"] == str(player2.id)

        # Step 5: Delete the pick
        delete_response = await client.delete(
            f"/api/v1/picks/{pick_id}", headers=headers
        )
        assert delete_response.status_code == 204

        # Step 6: Verify pick is deleted
        get_deleted_response = await client.get(
            f"/api/v1/picks/{pick_id}", headers=headers
        )
        assert get_deleted_response.status_code == 404

        # Step 7: Verify pick list is empty
        final_picks_response = await client.get("/api/v1/picks/", headers=headers)
        assert final_picks_response.status_code == 200
        final_picks = final_picks_response.json()
        assert len(final_picks) == 0


@pytest.mark.asyncio
async def test_pick_appears_in_available_games(
    db_session, test_user, auth_token, test_game, test_players
):
    """
    Test that picks appear when viewing available games
    Requirements: 7.1, 8.1, 8.2
    """
    player1, _, _ = test_players
    headers = {"Authorization": f"Bearer {auth_token}"}

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Step 1: Get available games (should show no pick)
        games_response = await client.get("/api/v1/games/available", headers=headers)
        assert games_response.status_code == 200
        games = games_response.json()
        assert len(games) >= 1
        game_with_no_pick = next(g for g in games if g["id"] == str(test_game.id))
        assert game_with_no_pick["user_pick"] is None

        # Step 2: Create a pick
        create_response = await client.post(
            "/api/v1/picks/",
            json={"game_id": str(test_game.id), "player_id": str(player1.id)},
            headers=headers,
        )
        assert create_response.status_code == 201

        # Step 3: Get available games again (should show the pick)
        games_with_pick_response = await client.get(
            "/api/v1/games/available", headers=headers
        )
        assert games_with_pick_response.status_code == 200
        games_with_pick = games_with_pick_response.json()
        game_with_pick = next(
            g for g in games_with_pick if g["id"] == str(test_game.id)
        )
        assert game_with_pick["user_pick"] is not None
        # Verify the pick is associated with the game
        assert game_with_pick["user_pick"]["id"] == create_response.json()["id"]


@pytest.mark.asyncio
async def test_multiple_picks_for_different_games(
    db_session, test_user, auth_token, test_teams, test_players
):
    """
    Test creating picks for multiple games
    Requirements: 1.1, 2.1
    """
    team1, team2 = test_teams
    player1, player2, player3 = test_players
    headers = {"Authorization": f"Bearer {auth_token}"}

    # Create two games
    from app.db.models.game import GameType, GameStatus

    kickoff1 = datetime.now(timezone.utc) + timedelta(hours=2)
    kickoff2 = datetime.now(timezone.utc) + timedelta(hours=4)

    game1 = Game(
        id=uuid.uuid4(),
        external_id="game_multi_1",
        home_team_id=team1.id,
        away_team_id=team2.id,
        kickoff_time=kickoff1,
        game_date=kickoff1,
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_EARLY,
        status=GameStatus.SCHEDULED,
    )
    game2 = Game(
        id=uuid.uuid4(),
        external_id="game_multi_2",
        home_team_id=team2.id,
        away_team_id=team1.id,
        kickoff_time=kickoff2,
        game_date=kickoff2,
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.SCHEDULED,
    )
    db_session.add(game1)
    db_session.add(game2)
    await db_session.commit()

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create pick for game 1
        response1 = await client.post(
            "/api/v1/picks/",
            json={"game_id": str(game1.id), "player_id": str(player1.id)},
            headers=headers,
        )
        assert response1.status_code == 201

        # Create pick for game 2
        response2 = await client.post(
            "/api/v1/picks/",
            json={"game_id": str(game2.id), "player_id": str(player2.id)},
            headers=headers,
        )
        assert response2.status_code == 201

        # Get all picks
        get_response = await client.get("/api/v1/picks/", headers=headers)
        assert get_response.status_code == 200
        picks = get_response.json()
        assert len(picks) == 2

        # Filter picks by game
        game1_picks_response = await client.get(
            f"/api/v1/picks/?game_id={game1.id}", headers=headers
        )
        assert game1_picks_response.status_code == 200
        game1_picks = game1_picks_response.json()
        assert len(game1_picks) == 1
        assert game1_picks[0]["player_id"] == str(player1.id)


@pytest.mark.asyncio
async def test_validation_and_error_handling(
    db_session, test_user, auth_token, test_teams, test_players
):
    """
    Test validation and error handling for picks
    Requirements: 1.5, 3.3, 4.2, 5.1, 9.3, 9.4
    """
    from app.db.models.game import GameType, GameStatus

    team1, team2 = test_teams
    player1, player2, player3 = test_players
    headers = {"Authorization": f"Bearer {auth_token}"}

    # Create a game with past kickoff (locked game)
    past_kickoff = datetime.now(timezone.utc) - timedelta(hours=2)
    locked_game = Game(
        id=uuid.uuid4(),
        external_id="locked_game",
        home_team_id=team1.id,
        away_team_id=team2.id,
        kickoff_time=past_kickoff,
        game_date=past_kickoff,
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.SCHEDULED,
    )
    db_session.add(locked_game)

    # Create a game with future kickoff
    future_kickoff = datetime.now(timezone.utc) + timedelta(hours=2)
    future_game = Game(
        id=uuid.uuid4(),
        external_id="future_game",
        home_team_id=team1.id,
        away_team_id=team2.id,
        kickoff_time=future_kickoff,
        game_date=future_kickoff,
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.SCHEDULED,
    )
    db_session.add(future_game)
    await db_session.commit()
    await db_session.refresh(locked_game)
    await db_session.refresh(future_game)

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test 1: Attempt to create pick after kickoff (Requirement 1.5)
        locked_response = await client.post(
            "/api/v1/picks/",
            json={"game_id": str(locked_game.id), "player_id": str(player1.id)},
            headers=headers,
        )
        assert locked_response.status_code == 400
        assert "kickoff" in locked_response.json()["detail"].lower()

        # Test 2: Create a valid pick
        create_response = await client.post(
            "/api/v1/picks/",
            json={"game_id": str(future_game.id), "player_id": str(player1.id)},
            headers=headers,
        )
        assert create_response.status_code == 201
        pick_id = create_response.json()["id"]

        # Test 3: Attempt to create duplicate pick (Requirement 5.1)
        duplicate_response = await client.post(
            "/api/v1/picks/",
            json={"game_id": str(future_game.id), "player_id": str(player2.id)},
            headers=headers,
        )
        assert duplicate_response.status_code == 400
        assert "already exists" in duplicate_response.json()["detail"].lower()

        # Test 4: Create another user to test cross-user operations
        other_user = User(
            id=uuid.uuid4(),
            email="otheruser@example.com",
            username="otheruser",
            is_active=True,
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)

        other_token = create_access_token(other_user.id)
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # Test 5: Attempt to update another user's pick (Requirement 9.3)
        update_response = await client.patch(
            f"/api/v1/picks/{pick_id}",
            json={"player_id": str(player2.id)},
            headers=other_headers,
        )
        assert update_response.status_code == 403
        assert "not authorized" in update_response.json()["detail"].lower()

        # Test 6: Attempt to delete another user's pick (Requirement 9.4)
        delete_response = await client.delete(
            f"/api/v1/picks/{pick_id}",
            headers=other_headers,
        )
        assert delete_response.status_code == 403
        assert "not authorized" in delete_response.json()["detail"].lower()

        # Test 7: Update the game to be locked and try to update pick (Requirement 3.3)
        future_game.kickoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
        await db_session.commit()

        update_locked_response = await client.patch(
            f"/api/v1/picks/{pick_id}",
            json={"player_id": str(player2.id)},
            headers=headers,
        )
        assert update_locked_response.status_code == 400
        assert "kickoff" in update_locked_response.json()["detail"].lower()

        # Test 8: Try to delete pick after kickoff (Requirement 4.2)
        delete_locked_response = await client.delete(
            f"/api/v1/picks/{pick_id}",
            headers=headers,
        )
        assert delete_locked_response.status_code == 400
        assert "kickoff" in delete_locked_response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_player_search_functionality(db_session, test_teams, auth_headers):
    """
    Test player search functionality
    Requirements: 6.1, 6.2, 6.3, 6.4
    """
    team1, team2 = test_teams

    # Create multiple players with different names
    players = [
        Player(
            id=uuid.uuid4(),
            external_id=f"search_player_{i}",
            name=name,
            team_id=team1.id if i % 2 == 0 else team2.id,
            position=position,
            is_active=True,
        )
        for i, (name, position) in enumerate(
            [
                ("Patrick Mahomes", "QB"),
                ("Travis Kelce", "TE"),
                ("Tyreek Hill", "WR"),
                ("Josh Allen", "QB"),
                ("Stefon Diggs", "WR"),
            ]
        )
    ]
    for player in players:
        db_session.add(player)
    await db_session.commit()

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test 1: Search by partial name (Requirement 6.1)
        search_response = await client.get(
            "/api/v1/players/search?q=Patrick", headers=auth_headers
        )
        assert search_response.status_code == 200
        results = search_response.json()
        assert len(results) >= 1
        assert any("Patrick" in p["name"] for p in results)

        # Test 2: Verify results include required fields (Requirement 6.2)
        if results:
            first_result = results[0]
            assert "name" in first_result
            assert "team" in first_result
            assert "position" in first_result

        # Test 3: Search with empty query (Requirement 6.3)
        empty_response = await client.get(
            "/api/v1/players/search?q=", headers=auth_headers
        )
        assert empty_response.status_code == 200
        empty_results = empty_response.json()
        assert len(empty_results) == 0

        # Test 4: Search with no matches (Requirement 6.4)
        no_match_response = await client.get(
            "/api/v1/players/search?q=NonExistentPlayer", headers=auth_headers
        )
        assert no_match_response.status_code == 200
        no_match_results = no_match_response.json()
        assert len(no_match_results) == 0

        # Test 5: Search returns relevant results
        travis_response = await client.get(
            "/api/v1/players/search?q=Travis", headers=auth_headers
        )
        assert travis_response.status_code == 200
        travis_results = travis_response.json()
        assert len(travis_results) >= 1
        assert any("Travis" in p["name"] for p in travis_results)
