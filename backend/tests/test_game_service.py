"""Tests for game service"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from hypothesis import given, settings, strategies as st, HealthCheck
from app.services.game_service import GameService
from app.db.models.game import Game, GameStatus, GameType
from app.db.models.team import Team
from app.db.models.player import Player
from app.db.models.pick import Pick, PickResult
from app.db.models.user import User


@pytest_asyncio.fixture
async def game_service(db_session):
    """Create GameService instance"""
    return GameService(db_session)


@pytest_asyncio.fixture
async def test_teams(db_session):
    """Create test teams"""
    home_team = Team(
        id=uuid4(),
        external_id="home_team_1",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    away_team = Team(
        id=uuid4(),
        external_id="away_team_1",
        name="Away Team",
        abbreviation="AWY",
        city="Away City",
    )
    db_session.add(home_team)
    db_session.add(away_team)
    await db_session.commit()
    await db_session.refresh(home_team)
    await db_session.refresh(away_team)
    return home_team, away_team


@pytest_asyncio.fixture
async def test_player(db_session, test_teams):
    """Create a test player"""
    home_team, _ = test_teams
    player = Player(
        id=uuid4(),
        external_id="player_1",
        name="Test Player",
        team_id=home_team.id,
        position="QB",
        jersey_number=12,
        is_active=True,
    )
    db_session.add(player)
    await db_session.commit()
    await db_session.refresh(player)
    return player


@pytest_asyncio.fixture
async def test_user(db_session):
    """Create a test user"""
    user = User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def future_game(db_session, test_teams):
    """Create a game with future kickoff"""
    home_team, away_team = test_teams
    future_time = datetime.now(timezone.utc) + timedelta(days=1)
    game = Game(
        id=uuid4(),
        external_id="game_future_1",
        season_year=2024,
        week_number=1,
        game_type=GameType.SUNDAY_MAIN,
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        game_date=future_time,
        kickoff_time=future_time,
        status=GameStatus.SCHEDULED,
    )
    db_session.add(game)
    await db_session.commit()
    await db_session.refresh(game)
    return game


@pytest_asyncio.fixture
async def past_game(db_session, test_teams):
    """Create a game with past kickoff"""
    home_team, away_team = test_teams
    past_time = datetime.now(timezone.utc) - timedelta(days=1)
    game = Game(
        id=uuid4(),
        external_id="game_past_1",
        season_year=2024,
        week_number=1,
        game_type=GameType.SUNDAY_MAIN,
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        game_date=past_time,
        kickoff_time=past_time,
        status=GameStatus.COMPLETED,
    )
    db_session.add(game)
    await db_session.commit()
    await db_session.refresh(game)
    return game


@pytest.mark.asyncio
async def test_get_available_games_returns_only_future_games(
    game_service, future_game, past_game
):
    """Test that get_available_games returns only games with future kickoffs"""
    games = await game_service.get_available_games()

    assert len(games) == 1
    assert games[0]["id"] == future_game.id


@pytest.mark.asyncio
async def test_get_available_games_ordered_by_kickoff(
    game_service, db_session, test_teams
):
    """Test that available games are ordered by kickoff time ascending"""
    home_team, away_team = test_teams

    # Create games with different kickoff times
    game1_time = datetime.now(timezone.utc) + timedelta(days=3)
    game2_time = datetime.now(timezone.utc) + timedelta(days=1)
    game3_time = datetime.now(timezone.utc) + timedelta(days=2)

    game1 = Game(
        id=uuid4(),
        external_id="game_1",
        season_year=2024,
        week_number=1,
        game_type=GameType.SUNDAY_MAIN,
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        game_date=game1_time,
        kickoff_time=game1_time,
        status=GameStatus.SCHEDULED,
    )
    game2 = Game(
        id=uuid4(),
        external_id="game_2",
        season_year=2024,
        week_number=1,
        game_type=GameType.SUNDAY_MAIN,
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        game_date=game2_time,
        kickoff_time=game2_time,
        status=GameStatus.SCHEDULED,
    )
    game3 = Game(
        id=uuid4(),
        external_id="game_3",
        season_year=2024,
        week_number=1,
        game_type=GameType.SUNDAY_MAIN,
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        game_date=game3_time,
        kickoff_time=game3_time,
        status=GameStatus.SCHEDULED,
    )

    db_session.add(game1)
    db_session.add(game2)
    db_session.add(game3)
    await db_session.commit()

    games = await game_service.get_available_games()

    assert len(games) == 3
    assert games[0]["id"] == game2.id  # Earliest
    assert games[1]["id"] == game3.id  # Middle
    assert games[2]["id"] == game1.id  # Latest


@pytest.mark.asyncio
async def test_get_available_games_includes_user_pick(
    game_service, db_session, future_game, test_player, test_user
):
    """Test that available games include user's existing picks"""
    # Create a pick for the user
    pick = Pick(
        id=uuid4(),
        user_id=test_user.id,
        game_id=future_game.id,
        player_id=test_player.id,
        status=PickResult.PENDING,
    )
    db_session.add(pick)
    await db_session.commit()

    games = await game_service.get_available_games(user_id=test_user.id)

    assert len(games) == 1
    assert games[0]["id"] == future_game.id
    assert games[0]["user_pick"] is not None
    assert games[0]["user_pick"]["id"] == pick.id
    assert games[0]["user_pick"]["player_name"] == test_player.name


@pytest.mark.asyncio
async def test_get_available_games_without_user_pick(
    game_service, future_game, test_user
):
    """Test that available games show no pick when user hasn't made one"""
    games = await game_service.get_available_games(user_id=test_user.id)

    assert len(games) == 1
    assert games[0]["id"] == future_game.id
    assert games[0]["user_pick"] is None


@pytest.mark.asyncio
async def test_is_game_locked_returns_true_for_past_kickoff(game_service, past_game):
    """Test that is_game_locked returns True for games with past kickoff"""
    is_locked = await game_service.is_game_locked(past_game.id)
    assert is_locked is True


@pytest.mark.asyncio
async def test_is_game_locked_returns_false_for_future_kickoff(
    game_service, future_game
):
    """Test that is_game_locked returns False for games with future kickoff"""
    is_locked = await game_service.is_game_locked(future_game.id)
    assert is_locked is False


@pytest.mark.asyncio
async def test_is_game_locked_returns_true_for_nonexistent_game(game_service):
    """Test that is_game_locked returns True for non-existent games"""
    fake_game_id = uuid4()
    is_locked = await game_service.is_game_locked(fake_game_id)
    assert is_locked is True


# Property-based tests


@st.composite
def future_datetime_strategy(draw):
    """Generate random future datetimes"""
    # Generate datetimes between 1 hour and 30 days in the future
    hours_ahead = draw(st.integers(min_value=1, max_value=720))  # 1 hour to 30 days
    return datetime.now(timezone.utc) + timedelta(hours=hours_ahead)


@st.composite
def past_datetime_strategy(draw):
    """Generate random past datetimes"""
    # Generate datetimes between 1 hour and 30 days in the past
    hours_ago = draw(st.integers(min_value=1, max_value=720))  # 1 hour to 30 days
    return datetime.now(timezone.utc) - timedelta(hours=hours_ago)


@pytest_asyncio.fixture
async def create_test_game(db_session, test_teams):
    """Factory fixture for creating test games"""

    async def _create_game(kickoff_time: datetime):
        home_team, away_team = test_teams
        game = Game(
            id=uuid4(),
            external_id=f"test_game_{uuid4()}",
            season_year=2024,
            week_number=1,
            game_type=GameType.SUNDAY_MAIN,
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            game_date=kickoff_time,
            kickoff_time=kickoff_time,
            status=GameStatus.SCHEDULED,
        )
        db_session.add(game)
        await db_session.commit()
        await db_session.refresh(game)
        return game

    return _create_game


@pytest.mark.asyncio
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=timedelta(milliseconds=1000),
)
@given(
    future_kickoff=future_datetime_strategy(),
    past_kickoff=past_datetime_strategy(),
)
async def test_property_17_available_games_are_future_games(
    future_kickoff, past_kickoff, game_service, create_test_game, db_session
):
    """
    Feature: pick-submission, Property 17: Available games are future games
    For any game returned as available, the kickoff time should be in the future relative to the current time.
    Validates: Requirements 7.1
    """
    # Setup: Create one game with future kickoff and one with past kickoff
    future_game = await create_test_game(future_kickoff)
    past_game = await create_test_game(past_kickoff)

    # Action: Get available games
    available_games = await game_service.get_available_games()

    # Assert: All returned games should have future kickoff times
    now = datetime.now(timezone.utc)
    for game in available_games:
        assert (
            game["kickoff_time"] > now
        ), f"Game {game['id']} has kickoff time {game['kickoff_time']} which is not in the future (now: {now})"

    # Assert: Future game should be in results, past game should not
    game_ids = [game["id"] for game in available_games]
    assert (
        future_game.id in game_ids
    ), f"Future game {future_game.id} should be in available games"
    assert (
        past_game.id not in game_ids
    ), f"Past game {past_game.id} should not be in available games"


@pytest.mark.asyncio
async def test_property_17_available_games_are_future_games_unit(
    game_service, db_session, test_teams
):
    """
    Unit test version of Property 17 with specific examples
    """
    home_team, away_team = test_teams

    # Setup: Create games with specific kickoff times
    now = datetime.now(timezone.utc)

    # Game 1: 1 hour in the future
    future_game_1 = Game(
        id=uuid4(),
        external_id="future_1",
        season_year=2024,
        week_number=1,
        game_type=GameType.SUNDAY_MAIN,
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        game_date=now + timedelta(hours=1),
        kickoff_time=now + timedelta(hours=1),
        status=GameStatus.SCHEDULED,
    )

    # Game 2: 1 day in the future
    future_game_2 = Game(
        id=uuid4(),
        external_id="future_2",
        season_year=2024,
        week_number=1,
        game_type=GameType.SUNDAY_MAIN,
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        game_date=now + timedelta(days=1),
        kickoff_time=now + timedelta(days=1),
        status=GameStatus.SCHEDULED,
    )

    # Game 3: 1 hour in the past
    past_game_1 = Game(
        id=uuid4(),
        external_id="past_1",
        season_year=2024,
        week_number=1,
        game_type=GameType.SUNDAY_MAIN,
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        game_date=now - timedelta(hours=1),
        kickoff_time=now - timedelta(hours=1),
        status=GameStatus.IN_PROGRESS,
    )

    # Game 4: 1 day in the past
    past_game_2 = Game(
        id=uuid4(),
        external_id="past_2",
        season_year=2024,
        week_number=1,
        game_type=GameType.SUNDAY_MAIN,
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        game_date=now - timedelta(days=1),
        kickoff_time=now - timedelta(days=1),
        status=GameStatus.COMPLETED,
    )

    db_session.add(future_game_1)
    db_session.add(future_game_2)
    db_session.add(past_game_1)
    db_session.add(past_game_2)
    await db_session.commit()

    # Action: Get available games
    available_games = await game_service.get_available_games()

    # Assert: Only future games should be returned
    game_ids = [game["id"] for game in available_games]
    assert future_game_1.id in game_ids, "Future game 1 should be available"
    assert future_game_2.id in game_ids, "Future game 2 should be available"
    assert past_game_1.id not in game_ids, "Past game 1 should not be available"
    assert past_game_2.id not in game_ids, "Past game 2 should not be available"

    # Assert: All returned games have future kickoff times
    current_time = datetime.now(timezone.utc)
    for game in available_games:
        assert (
            game["kickoff_time"] > current_time
        ), f"Game {game['id']} should have future kickoff time"


@pytest.mark.asyncio
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=timedelta(milliseconds=1000),
)
@given(
    kickoff_times=st.lists(
        future_datetime_strategy(),
        min_size=2,
        max_size=10,
        unique=True,
    )
)
async def test_property_19_available_games_ordered_by_kickoff(
    kickoff_times, game_service, db_session, test_teams
):
    """
    Feature: pick-submission, Property 19: Available games ordered by kickoff
    For any list of available games returned, the games should be ordered by kickoff_time in ascending order.
    Validates: Requirements 7.4
    """
    home_team, away_team = test_teams

    # Setup: Create games with random future kickoff times
    created_games = []
    for kickoff_time in kickoff_times:
        game = Game(
            id=uuid4(),
            external_id=f"test_game_{uuid4()}",
            season_year=2024,
            week_number=1,
            game_type=GameType.SUNDAY_MAIN,
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            game_date=kickoff_time,
            kickoff_time=kickoff_time,
            status=GameStatus.SCHEDULED,
        )
        db_session.add(game)
        created_games.append(game)

    await db_session.commit()

    # Action: Get available games
    available_games = await game_service.get_available_games()

    # Assert: Games should be ordered by kickoff_time in ascending order
    assert len(available_games) >= len(
        kickoff_times
    ), "Should return at least the games we created"

    # Extract kickoff times from the returned games
    returned_kickoff_times = [game["kickoff_time"] for game in available_games]

    # Verify that the list is sorted in ascending order
    for i in range(len(returned_kickoff_times) - 1):
        assert (
            returned_kickoff_times[i] <= returned_kickoff_times[i + 1]
        ), f"Games not ordered correctly: {returned_kickoff_times[i]} should be <= {returned_kickoff_times[i + 1]}"

    # Verify that all our created games are in the results and in the correct order
    created_game_ids = {game.id for game in created_games}
    returned_game_ids = [game["id"] for game in available_games]

    # Filter to only our created games
    our_games_in_result = [
        game for game in available_games if game["id"] in created_game_ids
    ]

    # Verify they are sorted
    our_kickoff_times = [game["kickoff_time"] for game in our_games_in_result]
    sorted_kickoff_times = sorted(kickoff_times)

    assert (
        our_kickoff_times == sorted_kickoff_times
    ), f"Our games not in correct order. Expected: {sorted_kickoff_times}, Got: {our_kickoff_times}"


@pytest.mark.asyncio
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=timedelta(milliseconds=1000),
)
@given(
    num_games=st.integers(min_value=2, max_value=10),
    num_picks=st.integers(min_value=0, max_value=5),
)
async def test_property_20_games_with_picks_are_indicated(
    num_games, num_picks, game_service, db_session, test_teams, test_user
):
    """
    Feature: pick-submission, Property 20: Games with picks are indicated
    For any user viewing available games, games where that user has submitted a pick
    should be indicated with the pick information including player name.
    Validates: Requirements 8.1, 8.2
    """
    home_team, away_team = test_teams

    # Ensure num_picks doesn't exceed num_games
    num_picks = min(num_picks, num_games)

    # Setup: Create random number of future games
    created_games = []
    now = datetime.now(timezone.utc)

    for i in range(num_games):
        kickoff_time = now + timedelta(hours=i + 1)
        game = Game(
            id=uuid4(),
            external_id=f"test_game_{uuid4()}",
            season_year=2024,
            week_number=1,
            game_type=GameType.SUNDAY_MAIN,
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            game_date=kickoff_time,
            kickoff_time=kickoff_time,
            status=GameStatus.SCHEDULED,
        )
        db_session.add(game)
        created_games.append(game)

    await db_session.commit()

    # Refresh games to get IDs
    for game in created_games:
        await db_session.refresh(game)

    # Setup: Create players for picks
    created_players = []
    for i in range(num_picks):
        player = Player(
            id=uuid4(),
            external_id=f"player_{uuid4()}",
            name=f"Test Player {i}",
            team_id=home_team.id,
            position="QB",
            jersey_number=10 + i,
            is_active=True,
        )
        db_session.add(player)
        created_players.append(player)

    await db_session.commit()

    # Refresh players to get IDs
    for player in created_players:
        await db_session.refresh(player)

    # Setup: Create picks for a subset of games
    games_with_picks = set()
    pick_to_player = {}

    for i in range(num_picks):
        game = created_games[i]
        player = created_players[i]

        pick = Pick(
            id=uuid4(),
            user_id=test_user.id,
            game_id=game.id,
            player_id=player.id,
            status=PickResult.PENDING,
        )
        db_session.add(pick)
        games_with_picks.add(game.id)
        pick_to_player[game.id] = player.name

    await db_session.commit()

    # Action: Get available games for the user
    available_games = await game_service.get_available_games(user_id=test_user.id)

    # Assert: All created games should be in the results
    returned_game_ids = {game["id"] for game in available_games}
    created_game_ids = {game.id for game in created_games}

    assert created_game_ids.issubset(
        returned_game_ids
    ), f"Not all created games returned. Created: {created_game_ids}, Returned: {returned_game_ids}"

    # Assert: Games with picks should have user_pick populated
    for game in available_games:
        if game["id"] in games_with_picks:
            # This game should have a pick
            assert (
                game["user_pick"] is not None
            ), f"Game {game['id']} should have user_pick populated"

            # The pick should include the player name
            assert (
                "player_name" in game["user_pick"]
            ), f"Game {game['id']} user_pick should include player_name"

            # The player name should match what we created
            expected_player_name = pick_to_player[game["id"]]
            assert (
                game["user_pick"]["player_name"] == expected_player_name
            ), f"Game {game['id']} player_name should be {expected_player_name}, got {game['user_pick']['player_name']}"

        elif game["id"] in created_game_ids:
            # This is one of our created games without a pick
            assert (
                game["user_pick"] is None
            ), f"Game {game['id']} should not have user_pick (no pick was created)"

    # Assert: Games without picks should have user_pick as None
    games_without_picks = created_game_ids - games_with_picks
    for game in available_games:
        if game["id"] in games_without_picks:
            assert (
                game["user_pick"] is None
            ), f"Game {game['id']} without pick should have user_pick=None"
