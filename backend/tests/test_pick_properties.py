"""Property-based tests for Pick service

Feature: pick-submission
These tests use Hypothesis to verify correctness properties across many random inputs.
"""

import pytest
import pytest_asyncio
from hypothesis import given, settings, strategies as st, HealthCheck
from uuid import UUID, uuid4
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from app.services.pick_service import PickService
from app.services.game_service import GameService
from app.db.models.pick import Pick, PickResult
from app.db.models.game import Game, GameStatus, GameType
from app.db.models.team import Team
from app.db.models.player import Player
from app.db.models.user import User
from app.schemas.pick import PickCreate
from app.core.exceptions import GameLockedError


# Hypothesis strategies for generating test data
def future_datetime_strategy():
    """Generate random future datetimes (1 hour to 30 days from now)"""
    return st.datetimes(
        min_value=datetime.now(timezone.utc) + timedelta(hours=1),
        max_value=datetime.now(timezone.utc) + timedelta(days=30),
        timezones=st.just(timezone.utc),
    )


def past_datetime_strategy():
    """Generate random past datetimes (30 days ago to 1 hour ago)"""
    return st.datetimes(
        min_value=datetime.now(timezone.utc) - timedelta(days=30),
        max_value=datetime.now(timezone.utc) - timedelta(hours=1),
        timezones=st.just(timezone.utc),
    )


def player_name_strategy():
    """Generate random player names"""
    return st.text(
        min_size=3,
        max_size=50,
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll"), blacklist_characters=" "
        ),
    )


def team_name_strategy():
    """Generate random team names"""
    return st.text(
        min_size=3,
        max_size=30,
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll"), blacklist_characters=" "
        ),
    )


def position_strategy():
    """Generate random player positions"""
    return st.sampled_from(["QB", "RB", "WR", "TE", "K", "DEF"])


def jersey_number_strategy():
    """Generate random jersey numbers"""
    return st.integers(min_value=0, max_value=99)


@pytest.mark.asyncio
@settings(
    max_examples=35,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    kickoff_offset_hours=st.integers(min_value=1, max_value=720),  # 1 hour to 30 days
    player_name=player_name_strategy(),
    team_name=team_name_strategy(),
    position=position_strategy(),
    jersey_number=jersey_number_strategy(),
)
async def test_property_1_valid_pick_creation(
    db_session,
    kickoff_offset_hours,
    player_name,
    team_name,
    position,
    jersey_number,
):
    """
    Feature: pick-submission, Property 1: Valid pick creation

    For any valid pick submission (user, game with future kickoff, player),
    creating the pick should result in a pick record with pending status,
    correct user_id, game_id, player_id, and a submission timestamp near
    the current time.

    Validates: Requirements 1.1, 1.2, 1.3, 1.4
    """
    # Setup: Create service
    pick_service = PickService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name=f"Home {team_name}",
        abbreviation="HOM",
        city="Home City",
    )
    away_team = Team(
        id=uuid4(),
        external_id=f"away_{uuid4().hex[:8]}",
        name=f"Away {team_name}",
        abbreviation="AWY",
        city="Away City",
    )
    db_session.add(home_team)
    db_session.add(away_team)
    await db_session.commit()

    # Setup: Create game with future kickoff
    kickoff_time = datetime.now(timezone.utc) + timedelta(hours=kickoff_offset_hours)
    game = Game(
        id=uuid4(),
        external_id=f"game_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        kickoff_time=kickoff_time,
        game_date=kickoff_time,
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.SCHEDULED,
    )
    db_session.add(game)
    await db_session.commit()

    # Setup: Create player
    player = Player(
        id=uuid4(),
        external_id=f"player_{uuid4().hex[:8]}",
        name=player_name,
        team_id=home_team.id,
        position=position,
        jersey_number=jersey_number,
        is_active=True,
    )
    db_session.add(player)
    await db_session.commit()

    # Setup: Create user
    user = User(
        id=uuid4(),
        email=f"user_{uuid4().hex[:8]}@example.com",
        username=f"user_{uuid4().hex[:8]}",
        display_name=f"User {uuid4().hex[:8]}",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    # Capture time before pick creation
    time_before = datetime.now(timezone.utc)

    # Action: Create pick
    pick_data = PickCreate(
        game_id=game.id,
        player_id=player.id,
        pick_type="FTD",  # Will be removed in future tasks
        snapshot_odds=None,
    )
    pick = await pick_service.create_pick(pick_data, user_id=user.id)

    # Capture time after pick creation
    time_after = datetime.now(timezone.utc)

    # Assert: Verify all properties
    # Requirement 1.1: Pick created with PENDING status
    assert (
        pick.status == PickResult.PENDING
    ), f"Expected status PENDING, got {pick.status}"

    # Requirement 1.3: Pick associated with authenticated user's ID
    assert pick.user_id == user.id, f"Expected user_id {user.id}, got {pick.user_id}"

    # Requirement 1.4: Pick stores selected player ID and game ID
    assert pick.game_id == game.id, f"Expected game_id {game.id}, got {pick.game_id}"
    assert (
        pick.player_id == player.id
    ), f"Expected player_id {player.id}, got {pick.player_id}"

    # Requirement 1.2: Pick captures submission timestamp
    assert pick.pick_submitted_at is not None, "pick_submitted_at should not be None"

    # Verify timestamp is near current time (within 10 seconds to account for test execution)
    assert (
        time_before <= pick.pick_submitted_at <= time_after + timedelta(seconds=10)
    ), (
        f"pick_submitted_at {pick.pick_submitted_at} should be between "
        f"{time_before} and {time_after}"
    )

    # Additional verification: Pick has an ID
    assert pick.id is not None, "Pick should have an ID"
    assert isinstance(pick.id, UUID), "Pick ID should be a UUID"


@pytest.mark.asyncio
@settings(
    max_examples=35,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    kickoff_offset_hours=st.integers(
        min_value=1, max_value=720
    ),  # 1 hour to 30 days in the past
    player_name=player_name_strategy(),
    team_name=team_name_strategy(),
    position=position_strategy(),
    jersey_number=jersey_number_strategy(),
)
async def test_property_2_kickoff_time_enforcement_for_creation(
    db_session,
    kickoff_offset_hours,
    player_name,
    team_name,
    position,
    jersey_number,
):
    """
    Feature: pick-submission, Property 2: Kickoff time enforcement for creation

    For any game with a kickoff time in the past, attempting to create a pick
    for that game should be rejected with an error.

    Validates: Requirements 1.5
    """
    # Setup: Create service
    pick_service = PickService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name=f"Home {team_name}",
        abbreviation="HOM",
        city="Home City",
    )
    away_team = Team(
        id=uuid4(),
        external_id=f"away_{uuid4().hex[:8]}",
        name=f"Away {team_name}",
        abbreviation="AWY",
        city="Away City",
    )
    db_session.add(home_team)
    db_session.add(away_team)
    await db_session.commit()

    # Setup: Create game with PAST kickoff (this is the key difference from Property 1)
    kickoff_time = datetime.now(timezone.utc) - timedelta(hours=kickoff_offset_hours)
    game = Game(
        id=uuid4(),
        external_id=f"game_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        kickoff_time=kickoff_time,
        game_date=kickoff_time,
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.SCHEDULED,
    )
    db_session.add(game)
    await db_session.commit()

    # Setup: Create player
    player = Player(
        id=uuid4(),
        external_id=f"player_{uuid4().hex[:8]}",
        name=player_name,
        team_id=home_team.id,
        position=position,
        jersey_number=jersey_number,
        is_active=True,
    )
    db_session.add(player)
    await db_session.commit()

    # Setup: Create user
    user = User(
        id=uuid4(),
        email=f"user_{uuid4().hex[:8]}@example.com",
        username=f"user_{uuid4().hex[:8]}",
        display_name=f"User {uuid4().hex[:8]}",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    # Action: Attempt to create pick for game with past kickoff
    pick_data = PickCreate(
        game_id=game.id,
        player_id=player.id,
        pick_type="FTD",  # Will be removed in future tasks
        snapshot_odds=None,
    )

    # Assert: Verify that GameLockedError is raised (Requirement 1.5)
    with pytest.raises(GameLockedError) as exc_info:
        await pick_service.create_pick(pick_data, user_id=user.id)

    # Verify the error message is appropriate
    assert (
        "kickoff" in str(exc_info.value).lower()
    ), f"Error message should mention 'kickoff', got: {exc_info.value}"

    # Additional verification: Ensure no pick was created in the database
    query = select(Pick).where(Pick.user_id == user.id, Pick.game_id == game.id)
    result = await db_session.execute(query)
    created_pick = result.scalar_one_or_none()

    assert (
        created_pick is None
    ), "No pick should be created when game kickoff has passed"


@pytest.mark.asyncio
@settings(
    max_examples=35,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    kickoff_offset_hours=st.integers(min_value=1, max_value=720),  # 1 hour to 30 days
    player1_name=player_name_strategy(),
    player2_name=player_name_strategy(),
    team_name=team_name_strategy(),
    position1=position_strategy(),
    position2=position_strategy(),
    jersey_number1=jersey_number_strategy(),
    jersey_number2=jersey_number_strategy(),
)
async def test_property_12_duplicate_pick_prevention(
    db_session,
    kickoff_offset_hours,
    player1_name,
    player2_name,
    team_name,
    position1,
    position2,
    jersey_number1,
    jersey_number2,
):
    """
    Feature: pick-submission, Property 12: Duplicate pick prevention

    For any user and game combination where a pick already exists, attempting
    to create another pick for the same user and game should be rejected with
    an error.

    Validates: Requirements 5.1, 5.2
    """
    from app.core.exceptions import DuplicatePickError

    # Setup: Create service
    pick_service = PickService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name=f"Home {team_name}",
        abbreviation="HOM",
        city="Home City",
    )
    away_team = Team(
        id=uuid4(),
        external_id=f"away_{uuid4().hex[:8]}",
        name=f"Away {team_name}",
        abbreviation="AWY",
        city="Away City",
    )
    db_session.add(home_team)
    db_session.add(away_team)
    await db_session.commit()

    # Setup: Create game with future kickoff
    kickoff_time = datetime.now(timezone.utc) + timedelta(hours=kickoff_offset_hours)
    game = Game(
        id=uuid4(),
        external_id=f"game_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        kickoff_time=kickoff_time,
        game_date=kickoff_time,
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.SCHEDULED,
    )
    db_session.add(game)
    await db_session.commit()

    # Setup: Create two different players
    player1 = Player(
        id=uuid4(),
        external_id=f"player1_{uuid4().hex[:8]}",
        name=player1_name,
        team_id=home_team.id,
        position=position1,
        jersey_number=jersey_number1,
        is_active=True,
    )
    player2 = Player(
        id=uuid4(),
        external_id=f"player2_{uuid4().hex[:8]}",
        name=player2_name,
        team_id=home_team.id,
        position=position2,
        jersey_number=jersey_number2,
        is_active=True,
    )
    db_session.add(player1)
    db_session.add(player2)
    await db_session.commit()

    # Setup: Create user
    user = User(
        id=uuid4(),
        email=f"user_{uuid4().hex[:8]}@example.com",
        username=f"user_{uuid4().hex[:8]}",
        display_name=f"User {uuid4().hex[:8]}",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    # Action: Create first pick successfully
    first_pick_data = PickCreate(
        game_id=game.id,
        player_id=player1.id,
        pick_type="FTD",  # Will be removed in future tasks
        snapshot_odds=None,
    )
    first_pick = await pick_service.create_pick(first_pick_data, user_id=user.id)

    # Verify first pick was created successfully
    assert first_pick is not None, "First pick should be created successfully"
    assert first_pick.user_id == user.id
    assert first_pick.game_id == game.id
    assert first_pick.player_id == player1.id

    # Action: Attempt to create second pick for same user and game (with different player)
    # Requirement 5.1: System SHALL reject the submission
    # Requirement 5.2: Duplicate check considers only user ID and game ID combination
    second_pick_data = PickCreate(
        game_id=game.id,
        player_id=player2.id,  # Different player, but same user and game
        pick_type="FTD",
        snapshot_odds=None,
    )

    # Assert: Verify that DuplicatePickError is raised
    with pytest.raises(DuplicatePickError) as exc_info:
        await pick_service.create_pick(second_pick_data, user_id=user.id)

    # Verify the error message mentions the duplicate
    error_message = str(exc_info.value).lower()
    assert (
        "already exists" in error_message or "duplicate" in error_message
    ), f"Error message should mention duplicate or already exists, got: {exc_info.value}"

    # Additional verification: Ensure only one pick exists in the database for this user/game
    query = select(Pick).where(Pick.user_id == user.id, Pick.game_id == game.id)
    result = await db_session.execute(query)
    picks = list(result.scalars().all())

    assert len(picks) == 1, f"Expected exactly 1 pick, found {len(picks)}"
    assert picks[0].id == first_pick.id, "The only pick should be the first one created"


@pytest.mark.asyncio
@settings(
    max_examples=35,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    num_users=st.integers(min_value=2, max_value=5),  # Create 2-5 users
    num_games=st.integers(min_value=2, max_value=5),  # Create 2-5 games
    kickoff_offset_hours=st.integers(min_value=1, max_value=720),  # 1 hour to 30 days
    team_name=team_name_strategy(),
)
async def test_property_3_user_pick_filtering(
    db_session,
    num_users,
    num_games,
    kickoff_offset_hours,
    team_name,
):
    """
    Feature: pick-submission, Property 3: User pick filtering

    For any user, retrieving picks for that user should return only picks
    where the user_id matches that user.

    Validates: Requirements 2.1
    """
    # Setup: Create service
    pick_service = PickService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name=f"Home {team_name}",
        abbreviation="HOM",
        city="Home City",
    )
    away_team = Team(
        id=uuid4(),
        external_id=f"away_{uuid4().hex[:8]}",
        name=f"Away {team_name}",
        abbreviation="AWY",
        city="Away City",
    )
    db_session.add(home_team)
    db_session.add(away_team)
    await db_session.commit()

    # Setup: Create multiple games
    games = []
    for i in range(num_games):
        kickoff_time = datetime.now(timezone.utc) + timedelta(
            hours=kickoff_offset_hours + i
        )
        game = Game(
            id=uuid4(),
            external_id=f"game_{i}_{uuid4().hex[:8]}",
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            kickoff_time=kickoff_time,
            game_date=kickoff_time,
            week_number=1,
            season_year=2024,
            game_type=GameType.SUNDAY_MAIN,
            status=GameStatus.SCHEDULED,
        )
        db_session.add(game)
        games.append(game)
    await db_session.commit()

    # Setup: Create multiple players
    players = []
    for i in range(num_games):
        player = Player(
            id=uuid4(),
            external_id=f"player_{i}_{uuid4().hex[:8]}",
            name=f"Player{i}",
            team_id=home_team.id,
            position="QB",
            jersey_number=i + 1,
            is_active=True,
        )
        db_session.add(player)
        players.append(player)
    await db_session.commit()

    # Setup: Create multiple users
    users = []
    for i in range(num_users):
        user = User(
            id=uuid4(),
            email=f"user{i}_{uuid4().hex[:8]}@example.com",
            username=f"user{i}_{uuid4().hex[:8]}",
            display_name=f"User {i}",
            is_active=True,
        )
        db_session.add(user)
        users.append(user)
    await db_session.commit()

    # Setup: Create picks for each user-game combination
    # Each user gets a pick for each game
    created_picks_by_user = {user.id: [] for user in users}
    for user in users:
        for i, game in enumerate(games):
            pick_data = PickCreate(
                game_id=game.id,
                player_id=players[i].id,
                pick_type="FTD",
                snapshot_odds=None,
            )
            pick = await pick_service.create_pick(pick_data, user_id=user.id)
            created_picks_by_user[user.id].append(pick)

    # Action & Assert: For each user, verify that get_user_picks returns only their picks
    for user in users:
        # Retrieve picks for this specific user
        user_picks = await pick_service.get_user_picks(user_id=user.id)

        # Requirement 2.1: All returned picks should belong to this user
        for pick in user_picks:
            assert (
                pick.user_id == user.id
            ), f"Expected all picks to have user_id {user.id}, but found pick with user_id {pick.user_id}"

        # Verify we got the correct number of picks for this user
        expected_pick_count = len(created_picks_by_user[user.id])
        assert len(user_picks) == expected_pick_count, (
            f"Expected {expected_pick_count} picks for user {user.id}, "
            f"but got {len(user_picks)}"
        )

        # Verify the pick IDs match what we created for this user
        returned_pick_ids = {pick.id for pick in user_picks}
        expected_pick_ids = {pick.id for pick in created_picks_by_user[user.id]}
        assert returned_pick_ids == expected_pick_ids, (
            f"Returned pick IDs don't match expected picks for user {user.id}. "
            f"Expected: {expected_pick_ids}, Got: {returned_pick_ids}"
        )


@pytest.mark.asyncio
@settings(
    max_examples=35,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    num_users=st.integers(min_value=2, max_value=5),  # Create 2-5 users
    num_games=st.integers(min_value=2, max_value=5),  # Create 2-5 games
    kickoff_offset_hours=st.integers(min_value=1, max_value=720),  # 1 hour to 30 days
    team_name=team_name_strategy(),
)
async def test_property_4_game_pick_filtering(
    db_session,
    num_users,
    num_games,
    kickoff_offset_hours,
    team_name,
):
    """
    Feature: pick-submission, Property 4: Game pick filtering

    For any game, retrieving picks filtered by that game should return only
    picks where the game_id matches that game.

    Validates: Requirements 2.3
    """
    # Setup: Create service
    pick_service = PickService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name=f"Home {team_name}",
        abbreviation="HOM",
        city="Home City",
    )
    away_team = Team(
        id=uuid4(),
        external_id=f"away_{uuid4().hex[:8]}",
        name=f"Away {team_name}",
        abbreviation="AWY",
        city="Away City",
    )
    db_session.add(home_team)
    db_session.add(away_team)
    await db_session.commit()

    # Setup: Create multiple games
    games = []
    for i in range(num_games):
        kickoff_time = datetime.now(timezone.utc) + timedelta(
            hours=kickoff_offset_hours + i
        )
        game = Game(
            id=uuid4(),
            external_id=f"game_{i}_{uuid4().hex[:8]}",
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            kickoff_time=kickoff_time,
            game_date=kickoff_time,
            week_number=1,
            season_year=2024,
            game_type=GameType.SUNDAY_MAIN,
            status=GameStatus.SCHEDULED,
        )
        db_session.add(game)
        games.append(game)
    await db_session.commit()

    # Setup: Create multiple players
    players = []
    for i in range(num_games):
        player = Player(
            id=uuid4(),
            external_id=f"player_{i}_{uuid4().hex[:8]}",
            name=f"Player{i}",
            team_id=home_team.id,
            position="QB",
            jersey_number=i + 1,
            is_active=True,
        )
        db_session.add(player)
        players.append(player)
    await db_session.commit()

    # Setup: Create multiple users
    users = []
    for i in range(num_users):
        user = User(
            id=uuid4(),
            email=f"user{i}_{uuid4().hex[:8]}@example.com",
            username=f"user{i}_{uuid4().hex[:8]}",
            display_name=f"User {i}",
            is_active=True,
        )
        db_session.add(user)
        users.append(user)
    await db_session.commit()

    # Setup: Create picks for each user-game combination
    # Each user gets a pick for each game
    created_picks_by_game = {game.id: [] for game in games}
    for user in users:
        for i, game in enumerate(games):
            pick_data = PickCreate(
                game_id=game.id,
                player_id=players[i].id,
                pick_type="FTD",
                snapshot_odds=None,
            )
            pick = await pick_service.create_pick(pick_data, user_id=user.id)
            created_picks_by_game[game.id].append(pick)

    # Action & Assert: For each game, verify that get_user_picks with game_id filter
    # returns only picks for that game
    for game in games:
        # Retrieve picks for this specific game (across all users)
        # We need to get picks for each user filtered by this game
        all_picks_for_game = []
        for user in users:
            user_game_picks = await pick_service.get_user_picks(
                user_id=user.id, game_id=game.id
            )
            all_picks_for_game.extend(user_game_picks)

        # Requirement 2.3: All returned picks should be for this game
        for pick in all_picks_for_game:
            assert (
                pick.game_id == game.id
            ), f"Expected all picks to have game_id {game.id}, but found pick with game_id {pick.game_id}"

        # Verify we got the correct number of picks for this game
        expected_pick_count = len(created_picks_by_game[game.id])
        assert len(all_picks_for_game) == expected_pick_count, (
            f"Expected {expected_pick_count} picks for game {game.id}, "
            f"but got {len(all_picks_for_game)}"
        )

        # Verify the pick IDs match what we created for this game
        returned_pick_ids = {pick.id for pick in all_picks_for_game}
        expected_pick_ids = {pick.id for pick in created_picks_by_game[game.id]}
        assert returned_pick_ids == expected_pick_ids, (
            f"Returned pick IDs don't match expected picks for game {game.id}. "
            f"Expected: {expected_pick_ids}, Got: {returned_pick_ids}"
        )


@pytest.mark.asyncio
@settings(
    max_examples=35,
    deadline=None,
    suppress_health_check=[
        HealthCheck.function_scoped_fixture,
        HealthCheck.data_too_large,
    ],
)
@given(
    num_picks=st.integers(min_value=1, max_value=5),  # Create 1-5 picks
    kickoff_offset_hours=st.integers(min_value=1, max_value=720),  # 1 hour to 30 days
    player_name=player_name_strategy(),
    team_name=team_name_strategy(),
    position=position_strategy(),
    jersey_number=jersey_number_strategy(),
)
async def test_property_5_pick_response_completeness(
    db_session,
    num_picks,
    kickoff_offset_hours,
    player_name,
    team_name,
    position,
    jersey_number,
):
    """
    Feature: pick-submission, Property 5: Pick response completeness

    For any pick retrieved from the system, the response should include all
    required fields: game information, player information, and submission timestamp.

    Validates: Requirements 2.2
    """
    # Setup: Create service
    pick_service = PickService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name=f"Home {team_name}",
        abbreviation="HOM",
        city="Home City",
    )
    away_team = Team(
        id=uuid4(),
        external_id=f"away_{uuid4().hex[:8]}",
        name=f"Away {team_name}",
        abbreviation="AWY",
        city="Away City",
    )
    db_session.add(home_team)
    db_session.add(away_team)
    await db_session.commit()

    # Setup: Create user
    user = User(
        id=uuid4(),
        email=f"user_{uuid4().hex[:8]}@example.com",
        username=f"user_{uuid4().hex[:8]}",
        display_name=f"User {uuid4().hex[:8]}",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    # Setup: Create multiple games and picks
    created_picks = []
    for i in range(num_picks):
        # Create game with future kickoff
        kickoff_time = datetime.now(timezone.utc) + timedelta(
            hours=kickoff_offset_hours + i
        )
        game = Game(
            id=uuid4(),
            external_id=f"game_{i}_{uuid4().hex[:8]}",
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            kickoff_time=kickoff_time,
            game_date=kickoff_time,
            week_number=1,
            season_year=2024,
            game_type=GameType.SUNDAY_MAIN,
            status=GameStatus.SCHEDULED,
        )
        db_session.add(game)
        await db_session.commit()

        # Create player
        player = Player(
            id=uuid4(),
            external_id=f"player_{i}_{uuid4().hex[:8]}",
            name=f"{player_name}{i}",
            team_id=home_team.id,
            position=position,
            jersey_number=jersey_number + i,
            is_active=True,
        )
        db_session.add(player)
        await db_session.commit()

        # Create pick
        pick_data = PickCreate(
            game_id=game.id,
            player_id=player.id,
            pick_type="FTD",
            snapshot_odds=None,
        )
        pick = await pick_service.create_pick(pick_data, user_id=user.id)
        created_picks.append((pick, game, player))

    # Action: Retrieve all picks for the user
    retrieved_picks = await pick_service.get_user_picks(user_id=user.id)

    # Assert: Verify we got all the picks we created
    assert (
        len(retrieved_picks) == num_picks
    ), f"Expected {num_picks} picks to be retrieved, but got {len(retrieved_picks)}"

    # Assert: For each retrieved pick, verify response completeness (Requirement 2.2)
    for retrieved_pick in retrieved_picks:
        # Find the corresponding created pick data
        matching_pick = None
        for created_pick, game, player in created_picks:
            if created_pick.id == retrieved_pick.id:
                matching_pick = (created_pick, game, player)
                break

        assert (
            matching_pick is not None
        ), f"Retrieved pick {retrieved_pick.id} was not in the created picks"

        created_pick, expected_game, expected_player = matching_pick

        # Requirement 2.2: Response should include submission timestamp
        assert (
            retrieved_pick.pick_submitted_at is not None
        ), f"Pick {retrieved_pick.id} should have pick_submitted_at timestamp"
        assert isinstance(
            retrieved_pick.pick_submitted_at, datetime
        ), f"pick_submitted_at should be a datetime, got {type(retrieved_pick.pick_submitted_at)}"

        # Requirement 2.2: Response should include game information
        # The pick should have game_id that we can use to verify game data
        assert (
            retrieved_pick.game_id is not None
        ), f"Pick {retrieved_pick.id} should have game_id"
        assert retrieved_pick.game_id == expected_game.id, (
            f"Pick {retrieved_pick.id} should have game_id {expected_game.id}, "
            f"got {retrieved_pick.game_id}"
        )

        # Verify we can access game data through the database
        # (The service performs joins, so we need to verify the data is accessible)
        game_query = select(Game).where(Game.id == retrieved_pick.game_id)
        game_result = await db_session.execute(game_query)
        game_data = game_result.scalar_one_or_none()

        assert (
            game_data is not None
        ), f"Game data should be accessible for pick {retrieved_pick.id}"
        assert game_data.home_team_id is not None, f"Game should have home_team_id"
        assert game_data.away_team_id is not None, f"Game should have away_team_id"
        assert game_data.kickoff_time is not None, f"Game should have kickoff_time"

        # Requirement 2.2: Response should include player information
        # The pick should have player_id that we can use to verify player data
        assert (
            retrieved_pick.player_id is not None
        ), f"Pick {retrieved_pick.id} should have player_id"
        assert retrieved_pick.player_id == expected_player.id, (
            f"Pick {retrieved_pick.id} should have player_id {expected_player.id}, "
            f"got {retrieved_pick.player_id}"
        )

        # Verify we can access player data through the database
        player_query = select(Player).where(Player.id == retrieved_pick.player_id)
        player_result = await db_session.execute(player_query)
        player_data = player_result.scalar_one_or_none()

        assert (
            player_data is not None
        ), f"Player data should be accessible for pick {retrieved_pick.id}"
        assert player_data.name is not None, f"Player should have name"
        assert player_data.team_id is not None, f"Player should have team_id"
        assert player_data.position is not None, f"Player should have position"


@pytest.mark.asyncio
@settings(
    max_examples=35,
    deadline=None,
    suppress_health_check=[
        HealthCheck.function_scoped_fixture,
        HealthCheck.data_too_large,
    ],
)
@given(
    kickoff_offset_hours=st.integers(min_value=1, max_value=720),  # 1 hour to 30 days
    player1_name=player_name_strategy(),
    player2_name=player_name_strategy(),
    team_name=team_name_strategy(),
    position1=position_strategy(),
    position2=position_strategy(),
    jersey_number1=jersey_number_strategy(),
    jersey_number2=jersey_number_strategy(),
)
async def test_property_6_pick_update_modifies_player(
    db_session,
    kickoff_offset_hours,
    player1_name,
    player2_name,
    team_name,
    position1,
    position2,
    jersey_number1,
    jersey_number2,
):
    """
    Feature: pick-submission, Property 6: Pick update modifies player

    For any pick with a future kickoff time, updating the pick with a new
    player_id should result in the pick record having the new player_id.

    Validates: Requirements 3.1
    """
    from app.schemas.pick import PickUpdate

    # Setup: Create service
    pick_service = PickService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name=f"Home {team_name}",
        abbreviation="HOM",
        city="Home City",
    )
    away_team = Team(
        id=uuid4(),
        external_id=f"away_{uuid4().hex[:8]}",
        name=f"Away {team_name}",
        abbreviation="AWY",
        city="Away City",
    )
    db_session.add(home_team)
    db_session.add(away_team)
    await db_session.commit()

    # Setup: Create game with future kickoff
    kickoff_time = datetime.now(timezone.utc) + timedelta(hours=kickoff_offset_hours)
    game = Game(
        id=uuid4(),
        external_id=f"game_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        kickoff_time=kickoff_time,
        game_date=kickoff_time,
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.SCHEDULED,
    )
    db_session.add(game)
    await db_session.commit()

    # Setup: Create two different players
    player1 = Player(
        id=uuid4(),
        external_id=f"player1_{uuid4().hex[:8]}",
        name=player1_name,
        team_id=home_team.id,
        position=position1,
        jersey_number=jersey_number1,
        is_active=True,
    )
    player2 = Player(
        id=uuid4(),
        external_id=f"player2_{uuid4().hex[:8]}",
        name=player2_name,
        team_id=home_team.id,
        position=position2,
        jersey_number=jersey_number2,
        is_active=True,
    )
    db_session.add(player1)
    db_session.add(player2)
    await db_session.commit()

    # Setup: Create user
    user = User(
        id=uuid4(),
        email=f"user_{uuid4().hex[:8]}@example.com",
        username=f"user_{uuid4().hex[:8]}",
        display_name=f"User {uuid4().hex[:8]}",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    # Setup: Create initial pick with player1
    pick_data = PickCreate(
        game_id=game.id,
        player_id=player1.id,
        pick_type="FTD",  # Will be removed in future tasks
        snapshot_odds=None,
    )
    pick = await pick_service.create_pick(pick_data, user_id=user.id)

    # Verify initial pick was created with player1
    assert pick.player_id == player1.id, (
        f"Initial pick should have player_id {player1.id}, " f"but got {pick.player_id}"
    )

    # Action: Update the pick to use player2 (Requirement 3.1)
    pick_update = PickUpdate(player_id=player2.id)
    updated_pick = await pick_service.update_pick(
        pick_id=pick.id, user_id=user.id, pick_update=pick_update
    )

    # Assert: Verify the pick now has the new player_id (Requirement 3.1)
    assert updated_pick.player_id == player2.id, (
        f"Updated pick should have player_id {player2.id}, "
        f"but got {updated_pick.player_id}"
    )

    # Additional verification: Ensure the pick ID hasn't changed
    assert updated_pick.id == pick.id, (
        f"Pick ID should remain the same after update. "
        f"Expected {pick.id}, got {updated_pick.id}"
    )

    # Additional verification: Verify the change persisted in the database
    db_pick = await pick_service.get_pick_by_id(pick.id)
    assert db_pick is not None, "Pick should still exist in database after update"
    assert db_pick.player_id == player2.id, (
        f"Database pick should have player_id {player2.id}, "
        f"but got {db_pick.player_id}"
    )


@pytest.mark.asyncio
@settings(
    max_examples=35,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    kickoff_offset_hours=st.integers(min_value=1, max_value=720),  # 1 hour to 30 days
    player1_name=player_name_strategy(),
    player2_name=player_name_strategy(),
    team_name=team_name_strategy(),
    position1=position_strategy(),
    position2=position_strategy(),
    jersey_number1=jersey_number_strategy(),
    jersey_number2=jersey_number_strategy(),
)
async def test_property_7_update_timestamp_changes(
    db_session,
    kickoff_offset_hours,
    player1_name,
    player2_name,
    team_name,
    position1,
    position2,
    jersey_number1,
    jersey_number2,
):
    """
    Feature: pick-submission, Property 7: Update timestamp changes

    For any pick that is updated, the updated_at timestamp should change to
    reflect the modification time.

    Validates: Requirements 3.2
    """
    from app.schemas.pick import PickUpdate
    import asyncio

    # Setup: Create service
    pick_service = PickService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name=f"Home {team_name}",
        abbreviation="HOM",
        city="Home City",
    )
    away_team = Team(
        id=uuid4(),
        external_id=f"away_{uuid4().hex[:8]}",
        name=f"Away {team_name}",
        abbreviation="AWY",
        city="Away City",
    )
    db_session.add(home_team)
    db_session.add(away_team)
    await db_session.commit()

    # Setup: Create game with future kickoff
    kickoff_time = datetime.now(timezone.utc) + timedelta(hours=kickoff_offset_hours)
    game = Game(
        id=uuid4(),
        external_id=f"game_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        kickoff_time=kickoff_time,
        game_date=kickoff_time,
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.SCHEDULED,
    )
    db_session.add(game)
    await db_session.commit()

    # Setup: Create two different players
    player1 = Player(
        id=uuid4(),
        external_id=f"player1_{uuid4().hex[:8]}",
        name=player1_name,
        team_id=home_team.id,
        position=position1,
        jersey_number=jersey_number1,
        is_active=True,
    )
    player2 = Player(
        id=uuid4(),
        external_id=f"player2_{uuid4().hex[:8]}",
        name=player2_name,
        team_id=home_team.id,
        position=position2,
        jersey_number=jersey_number2,
        is_active=True,
    )
    db_session.add(player1)
    db_session.add(player2)
    await db_session.commit()

    # Setup: Create user
    user = User(
        id=uuid4(),
        email=f"user_{uuid4().hex[:8]}@example.com",
        username=f"user_{uuid4().hex[:8]}",
        display_name=f"User {uuid4().hex[:8]}",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    # Setup: Create initial pick with player1
    pick_data = PickCreate(
        game_id=game.id,
        player_id=player1.id,
        pick_type="FTD",  # Will be removed in future tasks
        snapshot_odds=None,
    )
    pick = await pick_service.create_pick(pick_data, user_id=user.id)

    # Capture the original updated_at timestamp (may be None initially)
    original_updated_at = pick.updated_at

    # Capture the creation time for comparison
    time_before_update = datetime.now(timezone.utc)

    # Wait a small amount of time to ensure timestamp difference
    # This ensures that the updated_at timestamp will be different
    await asyncio.sleep(0.1)

    # Action: Update the pick to use player2 (Requirement 3.2)
    pick_update = PickUpdate(player_id=player2.id)
    updated_pick = await pick_service.update_pick(
        pick_id=pick.id, user_id=user.id, pick_update=pick_update
    )

    # Assert: Verify the updated_at timestamp is now set (Requirement 3.2)
    assert (
        updated_pick.updated_at is not None
    ), "Updated pick should have an updated_at timestamp after update"

    # Assert: If there was an original updated_at, verify it changed
    # If there wasn't (NULL), verify it's now set to a recent time
    if original_updated_at is not None:
        assert updated_pick.updated_at > original_updated_at, (
            f"updated_at should change after update. "
            f"Original: {original_updated_at}, Updated: {updated_pick.updated_at}"
        )
    else:
        # If original was None, verify the new timestamp is after the time before update
        assert updated_pick.updated_at >= time_before_update, (
            f"updated_at should be set to a time after the update was initiated. "
            f"Time before update: {time_before_update}, Updated: {updated_pick.updated_at}"
        )

    # Additional verification: Ensure the timestamp is recent (within last 10 seconds)
    time_now = datetime.now(timezone.utc)
    time_diff = (time_now - updated_pick.updated_at).total_seconds()
    assert time_diff < 10, (
        f"updated_at should be recent (within 10 seconds). "
        f"Time difference: {time_diff} seconds"
    )

    # Additional verification: Verify the change persisted in the database
    db_pick = await pick_service.get_pick_by_id(pick.id)
    assert db_pick is not None, "Pick should still exist in database after update"
    assert (
        db_pick.updated_at is not None
    ), "Database pick should have updated_at timestamp after update"

    # Verify database timestamp matches what we got back
    assert db_pick.updated_at == updated_pick.updated_at, (
        f"Database pick updated_at should match returned pick. "
        f"Returned: {updated_pick.updated_at}, Database: {db_pick.updated_at}"
    )


@pytest.mark.asyncio
@settings(
    max_examples=35,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    kickoff_offset_hours=st.integers(
        min_value=1, max_value=720
    ),  # 1 hour to 30 days in the past
    player1_name=player_name_strategy(),
    player2_name=player_name_strategy(),
    team_name=team_name_strategy(),
    position1=position_strategy(),
    position2=position_strategy(),
    jersey_number1=jersey_number_strategy(),
    jersey_number2=jersey_number_strategy(),
)
async def test_property_8_kickoff_time_enforcement_for_updates(
    db_session,
    kickoff_offset_hours,
    player1_name,
    player2_name,
    team_name,
    position1,
    position2,
    jersey_number1,
    jersey_number2,
):
    """
    Feature: pick-submission, Property 8: Kickoff time enforcement for updates

    For any pick associated with a game that has a kickoff time in the past,
    attempting to update the pick should be rejected with an error.

    Validates: Requirements 3.3
    """
    from app.schemas.pick import PickUpdate

    # Setup: Create service
    pick_service = PickService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name=f"Home {team_name}",
        abbreviation="HOM",
        city="Home City",
    )
    away_team = Team(
        id=uuid4(),
        external_id=f"away_{uuid4().hex[:8]}",
        name=f"Away {team_name}",
        abbreviation="AWY",
        city="Away City",
    )
    db_session.add(home_team)
    db_session.add(away_team)
    await db_session.commit()

    # Setup: Create game with FUTURE kickoff initially (so we can create the pick)
    future_kickoff_time = datetime.now(timezone.utc) + timedelta(hours=1)
    game = Game(
        id=uuid4(),
        external_id=f"game_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        kickoff_time=future_kickoff_time,
        game_date=future_kickoff_time,
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.SCHEDULED,
    )
    db_session.add(game)
    await db_session.commit()

    # Setup: Create two different players
    player1 = Player(
        id=uuid4(),
        external_id=f"player1_{uuid4().hex[:8]}",
        name=player1_name,
        team_id=home_team.id,
        position=position1,
        jersey_number=jersey_number1,
        is_active=True,
    )
    player2 = Player(
        id=uuid4(),
        external_id=f"player2_{uuid4().hex[:8]}",
        name=player2_name,
        team_id=home_team.id,
        position=position2,
        jersey_number=jersey_number2,
        is_active=True,
    )
    db_session.add(player1)
    db_session.add(player2)
    await db_session.commit()

    # Setup: Create user
    user = User(
        id=uuid4(),
        email=f"user_{uuid4().hex[:8]}@example.com",
        username=f"user_{uuid4().hex[:8]}",
        display_name=f"User {uuid4().hex[:8]}",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    # Setup: Create initial pick with player1 (while game is still in the future)
    pick_data = PickCreate(
        game_id=game.id,
        player_id=player1.id,
        pick_type="FTD",  # Will be removed in future tasks
        snapshot_odds=None,
    )
    pick = await pick_service.create_pick(pick_data, user_id=user.id)

    # Verify initial pick was created successfully
    assert pick.player_id == player1.id, (
        f"Initial pick should have player_id {player1.id}, " f"but got {pick.player_id}"
    )

    # NOW: Update the game's kickoff time to be in the PAST
    # This simulates the game having started
    past_kickoff_time = datetime.now(timezone.utc) - timedelta(
        hours=kickoff_offset_hours
    )
    game.kickoff_time = past_kickoff_time
    game.game_date = past_kickoff_time
    await db_session.commit()

    # Action: Attempt to update the pick after kickoff has passed (Requirement 3.3)
    pick_update = PickUpdate(player_id=player2.id)

    # Assert: Verify that GameLockedError is raised (Requirement 3.3)
    with pytest.raises(GameLockedError) as exc_info:
        await pick_service.update_pick(
            pick_id=pick.id, user_id=user.id, pick_update=pick_update
        )

    # Verify the error message is appropriate
    assert (
        "kickoff" in str(exc_info.value).lower()
    ), f"Error message should mention 'kickoff', got: {exc_info.value}"

    # Additional verification: Ensure the pick was NOT updated in the database
    db_pick = await pick_service.get_pick_by_id(pick.id)
    assert db_pick is not None, "Pick should still exist in database"
    assert db_pick.player_id == player1.id, (
        f"Pick should still have original player_id {player1.id} after failed update, "
        f"but got {db_pick.player_id}"
    )


@pytest.mark.asyncio
@settings(
    max_examples=35,
    deadline=None,
    suppress_health_check=[
        HealthCheck.function_scoped_fixture,
        HealthCheck.data_too_large,
    ],
)
@given(
    kickoff_offset_hours=st.integers(min_value=1, max_value=720),  # 1 hour to 30 days
    player1_name=player_name_strategy(),
    player2_name=player_name_strategy(),
    team_name=team_name_strategy(),
    position1=position_strategy(),
    position2=position_strategy(),
    jersey_number1=jersey_number_strategy(),
    jersey_number2=jersey_number_strategy(),
)
async def test_property_9_submission_timestamp_invariance(
    db_session,
    kickoff_offset_hours,
    player1_name,
    player2_name,
    team_name,
    position1,
    position2,
    jersey_number1,
    jersey_number2,
):
    """
    Feature: pick-submission, Property 9: Submission timestamp invariance

    For any pick that is updated, the pick_submitted_at timestamp should remain
    unchanged from its original value.

    Validates: Requirements 3.4
    """
    from app.schemas.pick import PickUpdate
    import asyncio

    # Setup: Create service
    pick_service = PickService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name=f"Home {team_name}",
        abbreviation="HOM",
        city="Home City",
    )
    away_team = Team(
        id=uuid4(),
        external_id=f"away_{uuid4().hex[:8]}",
        name=f"Away {team_name}",
        abbreviation="AWY",
        city="Away City",
    )
    db_session.add(home_team)
    db_session.add(away_team)
    await db_session.commit()

    # Setup: Create game with future kickoff
    kickoff_time = datetime.now(timezone.utc) + timedelta(hours=kickoff_offset_hours)
    game = Game(
        id=uuid4(),
        external_id=f"game_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        kickoff_time=kickoff_time,
        game_date=kickoff_time,
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.SCHEDULED,
    )
    db_session.add(game)
    await db_session.commit()

    # Setup: Create two different players
    player1 = Player(
        id=uuid4(),
        external_id=f"player1_{uuid4().hex[:8]}",
        name=player1_name,
        team_id=home_team.id,
        position=position1,
        jersey_number=jersey_number1,
        is_active=True,
    )
    player2 = Player(
        id=uuid4(),
        external_id=f"player2_{uuid4().hex[:8]}",
        name=player2_name,
        team_id=home_team.id,
        position=position2,
        jersey_number=jersey_number2,
        is_active=True,
    )
    db_session.add(player1)
    db_session.add(player2)
    await db_session.commit()

    # Setup: Create user
    user = User(
        id=uuid4(),
        email=f"user_{uuid4().hex[:8]}@example.com",
        username=f"user_{uuid4().hex[:8]}",
        display_name=f"User {uuid4().hex[:8]}",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    # Setup: Create initial pick with player1
    pick_data = PickCreate(
        game_id=game.id,
        player_id=player1.id,
        pick_type="FTD",  # Will be removed in future tasks
        snapshot_odds=None,
    )
    pick = await pick_service.create_pick(pick_data, user_id=user.id)

    # Capture the original pick_submitted_at timestamp (Requirement 3.4)
    original_pick_submitted_at = pick.pick_submitted_at

    # Verify the original timestamp is set
    assert (
        original_pick_submitted_at is not None
    ), "Original pick should have pick_submitted_at timestamp"

    # Wait a small amount of time to ensure any timestamp changes would be detectable
    await asyncio.sleep(0.1)

    # Action: Update the pick to use player2 (Requirement 3.4)
    pick_update = PickUpdate(player_id=player2.id)
    updated_pick = await pick_service.update_pick(
        pick_id=pick.id, user_id=user.id, pick_update=pick_update
    )

    # Assert: Verify the pick_submitted_at timestamp remains unchanged (Requirement 3.4)
    assert updated_pick.pick_submitted_at == original_pick_submitted_at, (
        f"pick_submitted_at should remain unchanged after update. "
        f"Original: {original_pick_submitted_at}, After update: {updated_pick.pick_submitted_at}"
    )

    # Additional verification: Verify the change persisted in the database
    db_pick = await pick_service.get_pick_by_id(pick.id)
    assert db_pick is not None, "Pick should still exist in database after update"
    assert db_pick.pick_submitted_at == original_pick_submitted_at, (
        f"Database pick_submitted_at should remain unchanged after update. "
        f"Original: {original_pick_submitted_at}, Database: {db_pick.pick_submitted_at}"
    )

    # Additional verification: Ensure the player was actually updated
    assert updated_pick.player_id == player2.id, (
        f"Pick should have been updated to player2 ({player2.id}), "
        f"but got {updated_pick.player_id}"
    )

    # Additional verification: Ensure updated_at is set
    # Note: The exact behavior of updated_at changing is tested in Property 7
    # Here we just verify it exists, focusing on pick_submitted_at invariance
    assert updated_pick.updated_at is not None, "updated_at should be set after update"


@pytest.mark.asyncio
@settings(
    max_examples=35,
    deadline=None,
    suppress_health_check=[
        HealthCheck.function_scoped_fixture,
        HealthCheck.data_too_large,
    ],
)
@given(
    kickoff_offset_hours=st.integers(min_value=1, max_value=720),  # 1 hour to 30 days
    player1_name=player_name_strategy(),
    player2_name=player_name_strategy(),
    team_name=team_name_strategy(),
    position1=position_strategy(),
    position2=position_strategy(),
    jersey_number1=jersey_number_strategy(),
    jersey_number2=jersey_number_strategy(),
)
async def test_property_13_update_does_not_trigger_duplicate_detection(
    db_session,
    kickoff_offset_hours,
    player1_name,
    player2_name,
    team_name,
    position1,
    position2,
    jersey_number1,
    jersey_number2,
):
    """
    Feature: pick-submission, Property 13: Update does not trigger duplicate detection

    For any existing pick, updating the pick with a new player_id should succeed
    without being rejected as a duplicate.

    Validates: Requirements 5.3
    """
    from app.schemas.pick import PickUpdate
    from app.core.exceptions import DuplicatePickError

    # Setup: Create service
    pick_service = PickService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name=f"Home {team_name}",
        abbreviation="HOM",
        city="Home City",
    )
    away_team = Team(
        id=uuid4(),
        external_id=f"away_{uuid4().hex[:8]}",
        name=f"Away {team_name}",
        abbreviation="AWY",
        city="Away City",
    )
    db_session.add(home_team)
    db_session.add(away_team)
    await db_session.commit()

    # Setup: Create game with future kickoff
    kickoff_time = datetime.now(timezone.utc) + timedelta(hours=kickoff_offset_hours)
    game = Game(
        id=uuid4(),
        external_id=f"game_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        kickoff_time=kickoff_time,
        game_date=kickoff_time,
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.SCHEDULED,
    )
    db_session.add(game)
    await db_session.commit()

    # Setup: Create two different players
    player1 = Player(
        id=uuid4(),
        external_id=f"player1_{uuid4().hex[:8]}",
        name=player1_name,
        team_id=home_team.id,
        position=position1,
        jersey_number=jersey_number1,
        is_active=True,
    )
    player2 = Player(
        id=uuid4(),
        external_id=f"player2_{uuid4().hex[:8]}",
        name=player2_name,
        team_id=home_team.id,
        position=position2,
        jersey_number=jersey_number2,
        is_active=True,
    )
    db_session.add(player1)
    db_session.add(player2)
    await db_session.commit()

    # Setup: Create user
    user = User(
        id=uuid4(),
        email=f"user_{uuid4().hex[:8]}@example.com",
        username=f"user_{uuid4().hex[:8]}",
        display_name=f"User {uuid4().hex[:8]}",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    # Setup: Create initial pick with player1
    pick_data = PickCreate(
        game_id=game.id,
        player_id=player1.id,
        pick_type="FTD",  # Will be removed in future tasks
        snapshot_odds=None,
    )
    pick = await pick_service.create_pick(pick_data, user_id=user.id)

    # Verify initial pick was created successfully
    assert pick.player_id == player1.id, (
        f"Initial pick should have player_id {player1.id}, " f"but got {pick.player_id}"
    )

    # Action: Update the pick to use player2 (Requirement 5.3)
    # This should NOT trigger duplicate detection because we're updating an existing pick
    # for the same user/game combination, not creating a new one
    pick_update = PickUpdate(player_id=player2.id)

    # Assert: Verify the update succeeds without raising DuplicatePickError (Requirement 5.3)
    try:
        updated_pick = await pick_service.update_pick(
            pick_id=pick.id, user_id=user.id, pick_update=pick_update
        )
    except DuplicatePickError:
        pytest.fail(
            "Updating an existing pick should not trigger duplicate detection. "
            "Requirement 5.3 states: 'WHEN a user updates an existing pick, "
            "THE Pick System SHALL allow the modification without treating it as a duplicate'"
        )

    # Assert: Verify the pick was successfully updated
    assert updated_pick.player_id == player2.id, (
        f"Updated pick should have player_id {player2.id}, "
        f"but got {updated_pick.player_id}"
    )

    # Assert: Verify the pick ID hasn't changed (it's still the same pick)
    assert updated_pick.id == pick.id, (
        f"Pick ID should remain the same after update. "
        f"Expected {pick.id}, got {updated_pick.id}"
    )

    # Additional verification: Ensure only one pick exists for this user/game combination
    query = select(Pick).where(Pick.user_id == user.id, Pick.game_id == game.id)
    result = await db_session.execute(query)
    picks = list(result.scalars().all())

    assert len(picks) == 1, (
        f"Expected exactly 1 pick for user/game combination after update, "
        f"found {len(picks)}"
    )
    assert picks[0].id == pick.id, "The only pick should be the original one (updated)"
    assert picks[0].player_id == player2.id, (
        f"The pick should have the updated player_id {player2.id}, "
        f"but got {picks[0].player_id}"
    )


@pytest.mark.asyncio
@settings(
    max_examples=35,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    kickoff_offset_hours=st.integers(min_value=1, max_value=720),  # 1 hour to 30 days
    player_name=player_name_strategy(),
    team_name=team_name_strategy(),
    position=position_strategy(),
    jersey_number=jersey_number_strategy(),
)
async def test_property_10_pick_deletion_removes_record(
    db_session,
    kickoff_offset_hours,
    player_name,
    team_name,
    position,
    jersey_number,
):
    """
    Feature: pick-submission, Property 10: Pick deletion removes record

    For any pick with a future kickoff time, deleting the pick should result
    in the pick no longer existing in the database.

    Validates: Requirements 4.1
    """
    # Setup: Create service
    pick_service = PickService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name=f"Home {team_name}",
        abbreviation="HOM",
        city="Home City",
    )
    away_team = Team(
        id=uuid4(),
        external_id=f"away_{uuid4().hex[:8]}",
        name=f"Away {team_name}",
        abbreviation="AWY",
        city="Away City",
    )
    db_session.add(home_team)
    db_session.add(away_team)
    await db_session.commit()

    # Setup: Create game with future kickoff
    kickoff_time = datetime.now(timezone.utc) + timedelta(hours=kickoff_offset_hours)
    game = Game(
        id=uuid4(),
        external_id=f"game_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        kickoff_time=kickoff_time,
        game_date=kickoff_time,
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.SCHEDULED,
    )
    db_session.add(game)
    await db_session.commit()

    # Setup: Create player
    player = Player(
        id=uuid4(),
        external_id=f"player_{uuid4().hex[:8]}",
        name=player_name,
        team_id=home_team.id,
        position=position,
        jersey_number=jersey_number,
        is_active=True,
    )
    db_session.add(player)
    await db_session.commit()

    # Setup: Create user
    user = User(
        id=uuid4(),
        email=f"user_{uuid4().hex[:8]}@example.com",
        username=f"user_{uuid4().hex[:8]}",
        display_name=f"User {uuid4().hex[:8]}",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    # Setup: Create pick
    pick_data = PickCreate(
        game_id=game.id,
        player_id=player.id,
        pick_type="FTD",  # Will be removed in future tasks
        snapshot_odds=None,
    )
    pick = await pick_service.create_pick(pick_data, user_id=user.id)

    # Verify pick was created successfully
    assert pick is not None, "Pick should be created successfully"
    assert pick.id is not None, "Pick should have an ID"
    pick_id = pick.id

    # Verify pick exists in database before deletion
    db_pick_before = await pick_service.get_pick_by_id(pick_id)
    assert db_pick_before is not None, "Pick should exist in database before deletion"

    # Action: Delete the pick (Requirement 4.1)
    await pick_service.delete_pick(pick_id=pick_id, user_id=user.id)

    # Assert: Verify the pick no longer exists in the database (Requirement 4.1)
    db_pick_after = await pick_service.get_pick_by_id(pick_id)
    assert (
        db_pick_after is None
    ), f"Pick {pick_id} should not exist in database after deletion, but it was found"

    # Additional verification: Query directly to ensure pick is truly gone
    query = select(Pick).where(Pick.id == pick_id)
    result = await db_session.execute(query)
    deleted_pick = result.scalar_one_or_none()

    assert (
        deleted_pick is None
    ), f"Pick {pick_id} should not be found in direct database query after deletion"

    # Additional verification: Ensure no picks exist for this user/game combination
    query = select(Pick).where(Pick.user_id == user.id, Pick.game_id == game.id)
    result = await db_session.execute(query)
    picks = list(result.scalars().all())

    assert (
        len(picks) == 0
    ), f"Expected 0 picks for user/game combination after deletion, found {len(picks)}"


@pytest.mark.asyncio
@settings(
    max_examples=35,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    kickoff_offset_hours=st.integers(
        min_value=1, max_value=720
    ),  # 1 hour to 30 days in the past
    player_name=player_name_strategy(),
    team_name=team_name_strategy(),
    position=position_strategy(),
    jersey_number=jersey_number_strategy(),
)
async def test_property_11_kickoff_time_enforcement_for_deletion(
    db_session,
    kickoff_offset_hours,
    player_name,
    team_name,
    position,
    jersey_number,
):
    """
    Feature: pick-submission, Property 11: Kickoff time enforcement for deletion

    For any pick associated with a game that has a kickoff time in the past,
    attempting to delete the pick should be rejected with an error.

    Validates: Requirements 4.2
    """
    # Setup: Create service
    pick_service = PickService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name=f"Home {team_name}",
        abbreviation="HOM",
        city="Home City",
    )
    away_team = Team(
        id=uuid4(),
        external_id=f"away_{uuid4().hex[:8]}",
        name=f"Away {team_name}",
        abbreviation="AWY",
        city="Away City",
    )
    db_session.add(home_team)
    db_session.add(away_team)
    await db_session.commit()

    # Setup: Create game with FUTURE kickoff initially (so we can create the pick)
    future_kickoff_time = datetime.now(timezone.utc) + timedelta(hours=1)
    game = Game(
        id=uuid4(),
        external_id=f"game_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        kickoff_time=future_kickoff_time,
        game_date=future_kickoff_time,
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.SCHEDULED,
    )
    db_session.add(game)
    await db_session.commit()

    # Setup: Create player
    player = Player(
        id=uuid4(),
        external_id=f"player_{uuid4().hex[:8]}",
        name=player_name,
        team_id=home_team.id,
        position=position,
        jersey_number=jersey_number,
        is_active=True,
    )
    db_session.add(player)
    await db_session.commit()

    # Setup: Create user
    user = User(
        id=uuid4(),
        email=f"user_{uuid4().hex[:8]}@example.com",
        username=f"user_{uuid4().hex[:8]}",
        display_name=f"User {uuid4().hex[:8]}",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    # Setup: Create pick (while game is still in the future)
    pick_data = PickCreate(
        game_id=game.id,
        player_id=player.id,
        pick_type="FTD",  # Will be removed in future tasks
        snapshot_odds=None,
    )
    pick = await pick_service.create_pick(pick_data, user_id=user.id)

    # Verify pick was created successfully
    assert pick is not None, "Pick should be created successfully"
    assert pick.id is not None, "Pick should have an ID"
    pick_id = pick.id

    # NOW: Update the game's kickoff time to be in the PAST
    # This simulates the game having started
    past_kickoff_time = datetime.now(timezone.utc) - timedelta(
        hours=kickoff_offset_hours
    )
    game.kickoff_time = past_kickoff_time
    game.game_date = past_kickoff_time
    await db_session.commit()

    # Action: Attempt to delete the pick after kickoff has passed (Requirement 4.2)
    # Assert: Verify that GameLockedError is raised (Requirement 4.2)
    with pytest.raises(GameLockedError) as exc_info:
        await pick_service.delete_pick(pick_id=pick_id, user_id=user.id)

    # Verify the error message is appropriate
    assert (
        "kickoff" in str(exc_info.value).lower()
    ), f"Error message should mention 'kickoff', got: {exc_info.value}"

    # Additional verification: Ensure the pick was NOT deleted from the database
    db_pick = await pick_service.get_pick_by_id(pick_id)
    assert (
        db_pick is not None
    ), f"Pick {pick_id} should still exist in database after failed deletion attempt"

    # Verify the pick still has the correct attributes
    assert (
        db_pick.user_id == user.id
    ), f"Pick should still belong to user {user.id} after failed deletion"
    assert (
        db_pick.game_id == game.id
    ), f"Pick should still be for game {game.id} after failed deletion"
    assert (
        db_pick.player_id == player.id
    ), f"Pick should still have player {player.id} after failed deletion"


# ============================================================================
# Authentication Property Tests (Task 5.4, 5.6, 5.9, 5.11)
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.slow  # Mark as slow integration test
@settings(
    max_examples=5,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    kickoff_offset_hours=st.integers(min_value=1, max_value=720),  # 1 hour to 30 days
    player_name=player_name_strategy(),
    team_name=team_name_strategy(),
    position=position_strategy(),
    jersey_number=jersey_number_strategy(),
)
async def test_property_21_unauthenticated_creation_rejected(
    db_session,
    kickoff_offset_hours,
    player_name,
    team_name,
    position,
    jersey_number,
):
    """
    Feature: pick-submission, Property 21: Unauthenticated creation rejected

    For any pick creation attempt without authentication, the request should
    be rejected with an authentication error.

    Validates: Requirements 9.1
    """
    from fastapi.testclient import TestClient
    from app.main import app
    from app.db.session import get_db

    # Override the database dependency to use our test session
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name=f"Home {team_name}",
        abbreviation="HOM",
        city="Home City",
    )
    away_team = Team(
        id=uuid4(),
        external_id=f"away_{uuid4().hex[:8]}",
        name=f"Away {team_name}",
        abbreviation="AWY",
        city="Away City",
    )
    db_session.add(home_team)
    db_session.add(away_team)
    await db_session.commit()

    # Setup: Create game with future kickoff
    kickoff_time = datetime.now(timezone.utc) + timedelta(hours=kickoff_offset_hours)
    game = Game(
        id=uuid4(),
        external_id=f"game_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        kickoff_time=kickoff_time,
        game_date=kickoff_time,
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.SCHEDULED,
    )
    db_session.add(game)
    await db_session.commit()

    # Setup: Create player
    player = Player(
        id=uuid4(),
        external_id=f"player_{uuid4().hex[:8]}",
        name=player_name,
        team_id=home_team.id,
        position=position,
        jersey_number=jersey_number,
        is_active=True,
    )
    db_session.add(player)
    await db_session.commit()

    # Action: Attempt to create pick WITHOUT authentication token
    client = TestClient(app)
    response = client.post(
        "/api/v1/picks/",
        json={
            "game_id": str(game.id),
            "player_id": str(player.id),
        },
    )

    # Assert: Verify that 401 or 403 is returned (Requirement 9.1)
    # HTTPBearer returns 403 by default when credentials are missing
    assert response.status_code in [401, 403], (
        f"Expected status code 401 or 403 for unauthenticated request, "
        f"got {response.status_code}"
    )

    # Verify the response indicates authentication is required
    response_data = response.json()
    assert "detail" in response_data, "Response should include error detail"
    assert (
        "authentication" in response_data["detail"].lower()
        or "unauthorized" in response_data["detail"].lower()
        or "not authenticated" in response_data["detail"].lower()
        or "forbidden" in response_data["detail"].lower()
    ), f"Error message should mention authentication, got: {response_data['detail']}"

    # Additional verification: Ensure no pick was created in the database
    query = select(Pick).where(Pick.game_id == game.id)
    result = await db_session.execute(query)
    created_picks = list(result.scalars().all())

    assert (
        len(created_picks) == 0
    ), "No pick should be created when request is unauthenticated"

    # Clean up
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.slow  # Mark as slow integration test
@settings(
    max_examples=5,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    kickoff_offset_hours=st.integers(min_value=1, max_value=720),  # 1 hour to 30 days
    player_name=player_name_strategy(),
    team_name=team_name_strategy(),
    position=position_strategy(),
    jersey_number=jersey_number_strategy(),
)
async def test_property_22_unauthenticated_viewing_rejected(
    db_session,
    kickoff_offset_hours,
    player_name,
    team_name,
    position,
    jersey_number,
):
    """
    Feature: pick-submission, Property 22: Unauthenticated viewing rejected

    For any pick viewing attempt without authentication, the request should
    be rejected with an authentication error.

    Validates: Requirements 9.2
    """
    from fastapi.testclient import TestClient
    from app.main import app
    from app.db.session import get_db

    # Override the database dependency to use our test session
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name=f"Home {team_name}",
        abbreviation="HOM",
        city="Home City",
    )
    away_team = Team(
        id=uuid4(),
        external_id=f"away_{uuid4().hex[:8]}",
        name=f"Away {team_name}",
        abbreviation="AWY",
        city="Away City",
    )
    db_session.add(home_team)
    db_session.add(away_team)
    await db_session.commit()

    # Setup: Create game with future kickoff
    kickoff_time = datetime.now(timezone.utc) + timedelta(hours=kickoff_offset_hours)
    game = Game(
        id=uuid4(),
        external_id=f"game_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        kickoff_time=kickoff_time,
        game_date=kickoff_time,
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.SCHEDULED,
    )
    db_session.add(game)
    await db_session.commit()

    # Setup: Create player
    player = Player(
        id=uuid4(),
        external_id=f"player_{uuid4().hex[:8]}",
        name=player_name,
        team_id=home_team.id,
        position=position,
        jersey_number=jersey_number,
        is_active=True,
    )
    db_session.add(player)
    await db_session.commit()

    # Setup: Create user and pick (so there's something to view)
    user = User(
        id=uuid4(),
        email=f"user_{uuid4().hex[:8]}@example.com",
        username=f"user_{uuid4().hex[:8]}",
        display_name=f"User {uuid4().hex[:8]}",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    pick_service = PickService(db_session)
    pick_data = PickCreate(
        game_id=game.id,
        player_id=player.id,
    )
    pick = await pick_service.create_pick(pick_data, user_id=user.id)

    # Action: Attempt to view picks WITHOUT authentication token
    client = TestClient(app)

    # Test GET /api/v1/picks/
    response_list = client.get("/api/v1/picks/")

    # Assert: Verify that 401 or 403 is returned (Requirement 9.2)
    # HTTPBearer returns 403 by default when credentials are missing
    assert response_list.status_code in [401, 403], (
        f"Expected status code 401 or 403 for unauthenticated GET /picks/, "
        f"got {response_list.status_code}"
    )

    # Test GET /api/v1/picks/{pick_id}
    response_detail = client.get(f"/api/v1/picks/{pick.id}")

    # Assert: Verify that 401 or 403 is returned (Requirement 9.2)
    assert response_detail.status_code in [401, 403], (
        f"Expected status code 401 or 403 for unauthenticated GET /picks/{{id}}, "
        f"got {response_detail.status_code}"
    )

    # Verify the responses indicate authentication is required
    for response in [response_list, response_detail]:
        response_data = response.json()
        assert "detail" in response_data, "Response should include error detail"
        assert (
            "authentication" in response_data["detail"].lower()
            or "unauthorized" in response_data["detail"].lower()
            or "not authenticated" in response_data["detail"].lower()
            or "forbidden" in response_data["detail"].lower()
        ), f"Error message should mention authentication, got: {response_data['detail']}"

    # Clean up
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.slow  # Mark as slow integration test
@settings(
    max_examples=5,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    kickoff_offset_hours=st.integers(min_value=1, max_value=720),  # 1 hour to 30 days
    player1_name=player_name_strategy(),
    player2_name=player_name_strategy(),
    team_name=team_name_strategy(),
    position1=position_strategy(),
    position2=position_strategy(),
    jersey_number1=jersey_number_strategy(),
    jersey_number2=jersey_number_strategy(),
)
async def test_property_23_cross_user_modification_rejected(
    db_session,
    kickoff_offset_hours,
    player1_name,
    player2_name,
    team_name,
    position1,
    position2,
    jersey_number1,
    jersey_number2,
):
    """
    Feature: pick-submission, Property 23: Cross-user modification rejected

    For any pick owned by user A, an attempt by user B to modify that pick
    should be rejected with an authorization error.

    Validates: Requirements 9.3
    """
    from fastapi.testclient import TestClient
    from app.main import app
    from app.db.session import get_db
    from app.core.security import create_access_token

    # Override the database dependency to use our test session
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name=f"Home {team_name}",
        abbreviation="HOM",
        city="Home City",
    )
    away_team = Team(
        id=uuid4(),
        external_id=f"away_{uuid4().hex[:8]}",
        name=f"Away {team_name}",
        abbreviation="AWY",
        city="Away City",
    )
    db_session.add(home_team)
    db_session.add(away_team)
    await db_session.commit()

    # Setup: Create game with future kickoff
    kickoff_time = datetime.now(timezone.utc) + timedelta(hours=kickoff_offset_hours)
    game = Game(
        id=uuid4(),
        external_id=f"game_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        kickoff_time=kickoff_time,
        game_date=kickoff_time,
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.SCHEDULED,
    )
    db_session.add(game)
    await db_session.commit()

    # Setup: Create two different players
    player1 = Player(
        id=uuid4(),
        external_id=f"player1_{uuid4().hex[:8]}",
        name=player1_name,
        team_id=home_team.id,
        position=position1,
        jersey_number=jersey_number1,
        is_active=True,
    )
    player2 = Player(
        id=uuid4(),
        external_id=f"player2_{uuid4().hex[:8]}",
        name=player2_name,
        team_id=home_team.id,
        position=position2,
        jersey_number=jersey_number2,
        is_active=True,
    )
    db_session.add(player1)
    db_session.add(player2)
    await db_session.commit()

    # Setup: Create two different users (User A and User B)
    user_a = User(
        id=uuid4(),
        email=f"userA_{uuid4().hex[:8]}@example.com",
        username=f"userA_{uuid4().hex[:8]}",
        display_name=f"User A {uuid4().hex[:8]}",
        is_active=True,
    )
    user_b = User(
        id=uuid4(),
        email=f"userB_{uuid4().hex[:8]}@example.com",
        username=f"userB_{uuid4().hex[:8]}",
        display_name=f"User B {uuid4().hex[:8]}",
        is_active=True,
    )
    db_session.add(user_a)
    db_session.add(user_b)
    await db_session.commit()

    # Setup: Create pick owned by User A
    pick_service = PickService(db_session)
    pick_data = PickCreate(
        game_id=game.id,
        player_id=player1.id,
    )
    pick = await pick_service.create_pick(pick_data, user_id=user_a.id)

    # Verify pick is owned by User A
    assert pick.user_id == user_a.id, f"Pick should be owned by User A"

    # Action: User B attempts to modify User A's pick
    # Create authentication token for User B
    user_b_token = create_access_token(data={"sub": str(user_b.id)})

    client = TestClient(app)
    response = client.patch(
        f"/api/v1/picks/{pick.id}",
        json={"player_id": str(player2.id)},
        headers={"Authorization": f"Bearer {user_b_token}"},
    )

    # Assert: Verify that 403 Forbidden is returned (Requirement 9.3)
    assert response.status_code == 403, (
        f"Expected status code 403 for cross-user modification attempt, "
        f"got {response.status_code}"
    )

    # Verify the response indicates authorization failure
    response_data = response.json()
    assert "detail" in response_data, "Response should include error detail"
    assert (
        "authorized" in response_data["detail"].lower()
        or "forbidden" in response_data["detail"].lower()
    ), f"Error message should mention authorization, got: {response_data['detail']}"

    # Additional verification: Ensure the pick was NOT modified in the database
    db_pick = await pick_service.get_pick_by_id(pick.id)
    assert db_pick is not None, "Pick should still exist in database"
    assert db_pick.player_id == player1.id, (
        f"Pick should still have original player_id {player1.id} after failed update, "
        f"but got {db_pick.player_id}"
    )
    assert db_pick.user_id == user_a.id, (
        f"Pick should still be owned by User A, " f"but got user_id {db_pick.user_id}"
    )

    # Clean up
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.slow  # Mark as slow integration test
@settings(
    max_examples=5,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    kickoff_offset_hours=st.integers(min_value=1, max_value=720),  # 1 hour to 30 days
    player_name=player_name_strategy(),
    team_name=team_name_strategy(),
    position=position_strategy(),
    jersey_number=jersey_number_strategy(),
)
async def test_property_24_cross_user_deletion_rejected(
    db_session,
    kickoff_offset_hours,
    player_name,
    team_name,
    position,
    jersey_number,
):
    """
    Feature: pick-submission, Property 24: Cross-user deletion rejected

    For any pick owned by user A, an attempt by user B to delete that pick
    should be rejected with an authorization error.

    Validates: Requirements 9.4
    """
    from fastapi.testclient import TestClient
    from app.main import app
    from app.db.session import get_db
    from app.core.security import create_access_token

    # Override the database dependency to use our test session
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name=f"Home {team_name}",
        abbreviation="HOM",
        city="Home City",
    )
    away_team = Team(
        id=uuid4(),
        external_id=f"away_{uuid4().hex[:8]}",
        name=f"Away {team_name}",
        abbreviation="AWY",
        city="Away City",
    )
    db_session.add(home_team)
    db_session.add(away_team)
    await db_session.commit()

    # Setup: Create game with future kickoff
    kickoff_time = datetime.now(timezone.utc) + timedelta(hours=kickoff_offset_hours)
    game = Game(
        id=uuid4(),
        external_id=f"game_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        kickoff_time=kickoff_time,
        game_date=kickoff_time,
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.SCHEDULED,
    )
    db_session.add(game)
    await db_session.commit()

    # Setup: Create player
    player = Player(
        id=uuid4(),
        external_id=f"player_{uuid4().hex[:8]}",
        name=player_name,
        team_id=home_team.id,
        position=position,
        jersey_number=jersey_number,
        is_active=True,
    )
    db_session.add(player)
    await db_session.commit()

    # Setup: Create two different users (User A and User B)
    user_a = User(
        id=uuid4(),
        email=f"userA_{uuid4().hex[:8]}@example.com",
        username=f"userA_{uuid4().hex[:8]}",
        display_name=f"User A {uuid4().hex[:8]}",
        is_active=True,
    )
    user_b = User(
        id=uuid4(),
        email=f"userB_{uuid4().hex[:8]}@example.com",
        username=f"userB_{uuid4().hex[:8]}",
        display_name=f"User B {uuid4().hex[:8]}",
        is_active=True,
    )
    db_session.add(user_a)
    db_session.add(user_b)
    await db_session.commit()

    # Setup: Create pick owned by User A
    pick_service = PickService(db_session)
    pick_data = PickCreate(
        game_id=game.id,
        player_id=player.id,
    )
    pick = await pick_service.create_pick(pick_data, user_id=user_a.id)

    # Verify pick is owned by User A
    assert pick.user_id == user_a.id, f"Pick should be owned by User A"

    # Action: User B attempts to delete User A's pick
    # Create authentication token for User B
    user_b_token = create_access_token(data={"sub": str(user_b.id)})

    client = TestClient(app)
    response = client.delete(
        f"/api/v1/picks/{pick.id}",
        headers={"Authorization": f"Bearer {user_b_token}"},
    )

    # Assert: Verify that 403 Forbidden is returned (Requirement 9.4)
    assert response.status_code == 403, (
        f"Expected status code 403 for cross-user deletion attempt, "
        f"got {response.status_code}"
    )

    # Verify the response indicates authorization failure
    response_data = response.json()
    assert "detail" in response_data, "Response should include error detail"
    assert (
        "authorized" in response_data["detail"].lower()
        or "forbidden" in response_data["detail"].lower()
    ), f"Error message should mention authorization, got: {response_data['detail']}"

    # Additional verification: Ensure the pick was NOT deleted from the database
    db_pick = await pick_service.get_pick_by_id(pick.id)
    assert (
        db_pick is not None
    ), f"Pick should still exist in database after failed deletion attempt"
    assert db_pick.user_id == user_a.id, (
        f"Pick should still be owned by User A, " f"but got user_id {db_pick.user_id}"
    )

    # Clean up
    app.dependency_overrides.clear()
