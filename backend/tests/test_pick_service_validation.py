"""Tests for PickService validation logic"""

import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from app.services.pick_service import PickService
from app.services.game_service import GameService
from app.db.models.pick import Pick, PickResult
from app.db.models.game import Game
from app.db.models.team import Team
from app.db.models.player import Player
from app.core.exceptions import DuplicatePickError, GameLockedError, NotFoundError


@pytest_asyncio.fixture
async def pick_service(db_session):
    """Create PickService instance"""
    return PickService(db_session)


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
async def future_game(db_session, test_teams):
    """Create a game with future kickoff"""
    from app.db.models.game import GameStatus, GameType

    home_team, away_team = test_teams
    kickoff = datetime.now(timezone.utc) + timedelta(hours=2)
    game = Game(
        id=uuid4(),
        external_id="future_game_1",
        home_team_id=home_team.id,
        away_team_id=away_team.id,
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


@pytest_asyncio.fixture
async def past_game(db_session, test_teams):
    """Create a game with past kickoff"""
    from app.db.models.game import GameStatus, GameType

    home_team, away_team = test_teams
    kickoff = datetime.now(timezone.utc) - timedelta(hours=2)
    game = Game(
        id=uuid4(),
        external_id="past_game_1",
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        kickoff_time=kickoff,
        game_date=kickoff,
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.IN_PROGRESS,
    )
    db_session.add(game)
    await db_session.commit()
    await db_session.refresh(game)
    return game


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
    from app.db.models.user import User

    user = User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        display_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_check_duplicate_pick_no_duplicate(pick_service, future_game):
    """Test check_duplicate_pick returns False when no duplicate exists"""
    user_id = uuid4()

    has_duplicate = await pick_service.check_duplicate_pick(user_id, future_game.id)

    assert has_duplicate is False


@pytest.mark.asyncio
async def test_check_duplicate_pick_with_duplicate(
    pick_service, db_session, future_game, test_player, test_user
):
    """Test check_duplicate_pick returns True when duplicate exists"""
    # Create an existing pick
    existing_pick = Pick(
        id=uuid4(),
        user_id=test_user.id,
        game_id=future_game.id,
        player_id=test_player.id,
        status=PickResult.PENDING,
    )
    db_session.add(existing_pick)
    await db_session.commit()

    # Check for duplicate
    has_duplicate = await pick_service.check_duplicate_pick(
        test_user.id, future_game.id
    )

    assert has_duplicate is True


@pytest.mark.asyncio
async def test_validate_pick_timing_future_game(pick_service, future_game):
    """Test validate_pick_timing succeeds for future game"""
    # Should not raise any exception
    await pick_service.validate_pick_timing(future_game.id)


@pytest.mark.asyncio
async def test_validate_pick_timing_past_game(pick_service, past_game):
    """Test validate_pick_timing raises GameLockedError for past game"""
    with pytest.raises(GameLockedError) as exc_info:
        await pick_service.validate_pick_timing(past_game.id)

    assert "Cannot modify pick after game kickoff" in str(exc_info.value)


@pytest.mark.asyncio
async def test_validate_pick_timing_nonexistent_game(pick_service):
    """Test validate_pick_timing raises NotFoundError for nonexistent game"""
    nonexistent_game_id = uuid4()

    with pytest.raises(NotFoundError) as exc_info:
        await pick_service.validate_pick_timing(nonexistent_game_id)

    assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_create_pick_success(pick_service, future_game, test_player, test_user):
    """Test create_pick successfully creates a pick with all validations"""
    from app.schemas.pick import PickCreate

    # Create pick data
    pick_data = PickCreate(
        game_id=future_game.id,
        player_id=test_player.id,
        pick_type="FTD",  # This field will be removed in future tasks
        snapshot_odds=None,
    )

    # Create the pick
    pick = await pick_service.create_pick(pick_data, user_id=test_user.id)

    # Verify the pick was created correctly
    assert pick.id is not None
    assert pick.user_id == test_user.id
    assert pick.game_id == future_game.id
    assert pick.player_id == test_player.id
    assert pick.status == PickResult.PENDING
    assert pick.pick_submitted_at is not None
    assert (
        abs((pick.pick_submitted_at - datetime.now(timezone.utc)).total_seconds()) < 5
    )


@pytest.mark.asyncio
async def test_create_pick_duplicate_error(
    pick_service, db_session, future_game, test_player, test_user
):
    """Test create_pick raises DuplicatePickError when pick already exists"""
    from app.schemas.pick import PickCreate

    # Create an existing pick
    existing_pick = Pick(
        id=uuid4(),
        user_id=test_user.id,
        game_id=future_game.id,
        player_id=test_player.id,
        status=PickResult.PENDING,
    )
    db_session.add(existing_pick)
    await db_session.commit()

    # Try to create a duplicate pick
    pick_data = PickCreate(
        game_id=future_game.id,
        player_id=test_player.id,
        pick_type="FTD",
        snapshot_odds=None,
    )

    with pytest.raises(DuplicatePickError) as exc_info:
        await pick_service.create_pick(pick_data, user_id=test_user.id)

    assert "already exists" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_create_pick_game_locked_error(
    pick_service, past_game, test_player, test_user
):
    """Test create_pick raises GameLockedError for past game"""
    from app.schemas.pick import PickCreate

    pick_data = PickCreate(
        game_id=past_game.id,
        player_id=test_player.id,
        pick_type="FTD",
        snapshot_odds=None,
    )

    with pytest.raises(GameLockedError) as exc_info:
        await pick_service.create_pick(pick_data, user_id=test_user.id)

    assert "kickoff" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_create_pick_player_not_found(pick_service, future_game, test_user):
    """Test create_pick raises NotFoundError for nonexistent player"""
    from app.schemas.pick import PickCreate

    nonexistent_player_id = uuid4()
    pick_data = PickCreate(
        game_id=future_game.id,
        player_id=nonexistent_player_id,
        pick_type="FTD",
        snapshot_odds=None,
    )

    with pytest.raises(NotFoundError) as exc_info:
        await pick_service.create_pick(pick_data, user_id=test_user.id)

    assert "player" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_create_pick_game_not_found(pick_service, test_player, test_user):
    """Test create_pick raises NotFoundError for nonexistent game"""
    from app.schemas.pick import PickCreate

    nonexistent_game_id = uuid4()
    pick_data = PickCreate(
        game_id=nonexistent_game_id,
        player_id=test_player.id,
        pick_type="FTD",
        snapshot_odds=None,
    )

    with pytest.raises(NotFoundError) as exc_info:
        await pick_service.create_pick(pick_data, user_id=test_user.id)

    assert "game" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_get_user_picks_no_picks(pick_service, test_user):
    """Test get_user_picks returns empty list when user has no picks"""
    picks = await pick_service.get_user_picks(test_user.id)

    assert picks == []


@pytest.mark.asyncio
async def test_get_user_picks_with_picks(
    pick_service, db_session, future_game, test_player, test_user
):
    """Test get_user_picks returns picks with complete data"""
    # Create a pick
    pick = Pick(
        id=uuid4(),
        user_id=test_user.id,
        game_id=future_game.id,
        player_id=test_player.id,
        status=PickResult.PENDING,
        pick_submitted_at=datetime.now(timezone.utc),
    )
    db_session.add(pick)
    await db_session.commit()

    # Get user picks
    picks = await pick_service.get_user_picks(test_user.id)

    assert len(picks) == 1
    assert picks[0].id == pick.id
    assert picks[0].user_id == test_user.id
    assert picks[0].game_id == future_game.id
    assert picks[0].player_id == test_player.id


@pytest.mark.asyncio
async def test_get_user_picks_with_game_filter(
    pick_service, db_session, test_teams, test_player, test_user
):
    """Test get_user_picks filters by game_id correctly"""
    from app.db.models.game import GameStatus, GameType

    home_team, away_team = test_teams

    # Create two games
    game1 = Game(
        id=uuid4(),
        external_id="game_1",
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        kickoff_time=datetime.now(timezone.utc) + timedelta(hours=2),
        game_date=datetime.now(timezone.utc) + timedelta(hours=2),
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.SCHEDULED,
    )
    game2 = Game(
        id=uuid4(),
        external_id="game_2",
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        kickoff_time=datetime.now(timezone.utc) + timedelta(hours=4),
        game_date=datetime.now(timezone.utc) + timedelta(hours=4),
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.SCHEDULED,
    )
    db_session.add(game1)
    db_session.add(game2)
    await db_session.commit()

    # Create picks for both games
    pick1 = Pick(
        id=uuid4(),
        user_id=test_user.id,
        game_id=game1.id,
        player_id=test_player.id,
        status=PickResult.PENDING,
        pick_submitted_at=datetime.now(timezone.utc),
    )
    pick2 = Pick(
        id=uuid4(),
        user_id=test_user.id,
        game_id=game2.id,
        player_id=test_player.id,
        status=PickResult.PENDING,
        pick_submitted_at=datetime.now(timezone.utc),
    )
    db_session.add(pick1)
    db_session.add(pick2)
    await db_session.commit()

    # Get picks for game1 only
    picks = await pick_service.get_user_picks(test_user.id, game_id=game1.id)

    assert len(picks) == 1
    assert picks[0].game_id == game1.id


@pytest.mark.asyncio
async def test_get_user_picks_ordered_by_submission_time(
    pick_service, db_session, test_teams, test_player, test_user
):
    """Test get_user_picks returns picks ordered by pick_submitted_at descending"""
    from app.db.models.game import GameStatus, GameType

    home_team, away_team = test_teams

    # Create three games
    games = []
    for i in range(3):
        game = Game(
            id=uuid4(),
            external_id=f"game_{i}",
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            kickoff_time=datetime.now(timezone.utc) + timedelta(hours=2 + i),
            game_date=datetime.now(timezone.utc) + timedelta(hours=2 + i),
            week_number=1,
            season_year=2024,
            game_type=GameType.SUNDAY_MAIN,
            status=GameStatus.SCHEDULED,
        )
        db_session.add(game)
        games.append(game)
    await db_session.commit()

    # Create picks with different submission times
    now = datetime.now(timezone.utc)
    picks_data = []
    for i, game in enumerate(games):
        pick = Pick(
            id=uuid4(),
            user_id=test_user.id,
            game_id=game.id,
            player_id=test_player.id,
            status=PickResult.PENDING,
            pick_submitted_at=now
            - timedelta(hours=i),  # Earlier picks have earlier times
        )
        db_session.add(pick)
        picks_data.append(pick)
    await db_session.commit()

    # Get user picks
    picks = await pick_service.get_user_picks(test_user.id)

    assert len(picks) == 3
    # Should be ordered by pick_submitted_at descending (most recent first)
    assert picks[0].pick_submitted_at > picks[1].pick_submitted_at
    assert picks[1].pick_submitted_at > picks[2].pick_submitted_at
