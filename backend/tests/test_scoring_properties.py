"""Property-based tests for Scoring service

Feature: scoring-system
These tests use Hypothesis to verify correctness properties across many random inputs.
"""

import pytest
import pytest_asyncio
from hypothesis import given, settings, strategies as st, HealthCheck
from uuid import UUID, uuid4
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from app.services.scoring import ScoringService
from app.db.models.pick import Pick, PickResult
from app.db.models.game import Game, GameStatus, GameType
from app.db.models.team import Team
from app.db.models.player import Player
from app.db.models.user import User
from typing import List, Optional


# Hypothesis strategies for generating test data
def uuid_strategy():
    """Generate random UUIDs"""
    return st.builds(uuid4)


def uuid_list_strategy(min_size=0, max_size=10):
    """Generate random lists of UUIDs"""
    return st.lists(uuid_strategy(), min_size=min_size, max_size=max_size)


def optional_uuid_strategy():
    """Generate optional UUIDs (None or UUID)"""
    return st.one_of(st.none(), uuid_strategy())


@pytest.mark.asyncio
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    first_td_scorer_matches=st.booleans(),  # Whether pick matches first TD scorer
)
async def test_property_5_ftd_points_correctness(
    db_session,
    first_td_scorer_matches,
):
    """
    Feature: scoring-system, Property 5: FTD points correctness

    For any pick, if the pick's player_id matches the first_td_scorer_player_id,
    then ftd_points should be 3; otherwise ftd_points should be 0.

    Validates: Requirements 2.1, 2.2, 2.3
    """
    # Setup: Create service
    scoring_service = ScoringService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    away_team = Team(
        id=uuid4(),
        external_id=f"away_{uuid4().hex[:8]}",
        name="Away Team",
        abbreviation="AWY",
        city="Away City",
    )
    db_session.add(home_team)
    db_session.add(away_team)
    await db_session.commit()

    # Setup: Create game
    game = Game(
        id=uuid4(),
        external_id=f"game_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        kickoff_time=datetime.now(timezone.utc) + timedelta(hours=1),
        game_date=datetime.now(timezone.utc) + timedelta(hours=1),
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.SCHEDULED,
    )
    db_session.add(game)
    await db_session.commit()

    # Setup: Create players
    picked_player = Player(
        id=uuid4(),
        external_id=f"player_picked_{uuid4().hex[:8]}",
        name="Picked Player",
        team_id=home_team.id,
        position="RB",
        jersey_number=1,
        is_active=True,
    )
    other_player = Player(
        id=uuid4(),
        external_id=f"player_other_{uuid4().hex[:8]}",
        name="Other Player",
        team_id=home_team.id,
        position="WR",
        jersey_number=2,
        is_active=True,
    )
    db_session.add(picked_player)
    db_session.add(other_player)
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
    pick = Pick(
        id=uuid4(),
        user_id=user.id,
        game_id=game.id,
        player_id=picked_player.id,
        status=PickResult.PENDING,
    )
    db_session.add(pick)
    await db_session.commit()

    # Setup: Determine first TD scorer based on test parameter
    if first_td_scorer_matches:
        first_td_scorer = picked_player.id
    else:
        first_td_scorer = other_player.id

    # Action: Calculate FTD points
    ftd_points = await scoring_service.calculate_ftd_points(pick, first_td_scorer)

    # Assert: Verify correctness property
    if first_td_scorer_matches:
        assert ftd_points == 3, (
            f"Expected 3 FTD points when pick matches first TD scorer, "
            f"but got {ftd_points}"
        )
    else:
        assert ftd_points == 0, (
            f"Expected 0 FTD points when pick doesn't match first TD scorer, "
            f"but got {ftd_points}"
        )


@pytest.mark.asyncio
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    first_td_scorer_is_none=st.booleans(),  # Whether there's a first TD scorer
)
async def test_property_5_ftd_points_no_touchdown(
    db_session,
    first_td_scorer_is_none,
):
    """
    Feature: scoring-system, Property 5: FTD points correctness (edge case: no TDs)

    For any pick, if first_td_scorer is None (no touchdowns), ftd_points should be 0.

    Validates: Requirements 2.1, 2.2, 2.3
    """
    # Setup: Create service
    scoring_service = ScoringService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    db_session.add(home_team)
    await db_session.commit()

    # Setup: Create game
    game = Game(
        id=uuid4(),
        external_id=f"game_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=home_team.id,
        kickoff_time=datetime.now(timezone.utc) + timedelta(hours=1),
        game_date=datetime.now(timezone.utc) + timedelta(hours=1),
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
        name="Player",
        team_id=home_team.id,
        position="RB",
        jersey_number=1,
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
    pick = Pick(
        id=uuid4(),
        user_id=user.id,
        game_id=game.id,
        player_id=player.id,
        status=PickResult.PENDING,
    )
    db_session.add(pick)
    await db_session.commit()

    # Setup: Set first TD scorer (None if no touchdowns)
    first_td_scorer = None if first_td_scorer_is_none else player.id

    # Action: Calculate FTD points
    ftd_points = await scoring_service.calculate_ftd_points(pick, first_td_scorer)

    # Assert: Verify correctness property
    if first_td_scorer_is_none:
        assert ftd_points == 0, (
            f"Expected 0 FTD points when no touchdowns scored, " f"but got {ftd_points}"
        )
    else:
        assert ftd_points == 3, (
            f"Expected 3 FTD points when pick matches first TD scorer, "
            f"but got {ftd_points}"
        )


@pytest.mark.asyncio
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    num_td_scorers=st.integers(min_value=0, max_value=5),  # 0-5 TD scorers
    player_scored=st.booleans(),  # Whether picked player scored
)
async def test_property_6_attd_points_correctness(
    db_session,
    num_td_scorers,
    player_scored,
):
    """
    Feature: scoring-system, Property 6: ATTD points correctness

    For any pick, if the pick's player_id appears in all_td_scorer_player_ids,
    then attd_points should be 1; otherwise attd_points should be 0.

    Validates: Requirements 3.1, 3.2, 3.3
    """
    # Setup: Create service
    scoring_service = ScoringService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    db_session.add(home_team)
    await db_session.commit()

    # Setup: Create game
    game = Game(
        id=uuid4(),
        external_id=f"game_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=home_team.id,
        kickoff_time=datetime.now(timezone.utc) + timedelta(hours=1),
        game_date=datetime.now(timezone.utc) + timedelta(hours=1),
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.SCHEDULED,
    )
    db_session.add(game)
    await db_session.commit()

    # Setup: Create picked player
    picked_player = Player(
        id=uuid4(),
        external_id=f"player_picked_{uuid4().hex[:8]}",
        name="Picked Player",
        team_id=home_team.id,
        position="RB",
        jersey_number=1,
        is_active=True,
    )
    db_session.add(picked_player)
    await db_session.commit()

    # Setup: Create other TD scorers
    other_td_scorers = []
    for i in range(num_td_scorers):
        player = Player(
            id=uuid4(),
            external_id=f"player_other_{i}_{uuid4().hex[:8]}",
            name=f"Other Player {i}",
            team_id=home_team.id,
            position="WR",
            jersey_number=i + 10,
            is_active=True,
        )
        db_session.add(player)
        other_td_scorers.append(player)
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
    pick = Pick(
        id=uuid4(),
        user_id=user.id,
        game_id=game.id,
        player_id=picked_player.id,
        status=PickResult.PENDING,
    )
    db_session.add(pick)
    await db_session.commit()

    # Setup: Build list of all TD scorers
    all_td_scorers = [p.id for p in other_td_scorers]
    if player_scored:
        # Add picked player to TD scorers list
        all_td_scorers.append(picked_player.id)

    # Action: Calculate ATTD points
    attd_points = await scoring_service.calculate_attd_points(pick, all_td_scorers)

    # Assert: Verify correctness property
    if player_scored:
        assert attd_points == 1, (
            f"Expected 1 ATTD point when pick's player scored, "
            f"but got {attd_points}"
        )
    else:
        assert attd_points == 0, (
            f"Expected 0 ATTD points when pick's player didn't score, "
            f"but got {attd_points}"
        )


@pytest.mark.asyncio
async def test_property_6_attd_points_empty_list(db_session):
    """
    Feature: scoring-system, Property 6: ATTD points correctness (edge case: no TDs)

    For any pick, if all_td_scorers is empty (no touchdowns), attd_points should be 0.

    Validates: Requirements 3.1, 3.2, 3.3
    """
    # Setup: Create service
    scoring_service = ScoringService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    db_session.add(home_team)
    await db_session.commit()

    # Setup: Create game
    game = Game(
        id=uuid4(),
        external_id=f"game_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=home_team.id,
        kickoff_time=datetime.now(timezone.utc) + timedelta(hours=1),
        game_date=datetime.now(timezone.utc) + timedelta(hours=1),
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
        name="Player",
        team_id=home_team.id,
        position="RB",
        jersey_number=1,
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
    pick = Pick(
        id=uuid4(),
        user_id=user.id,
        game_id=game.id,
        player_id=player.id,
        status=PickResult.PENDING,
    )
    db_session.add(pick)
    await db_session.commit()

    # Setup: Empty TD scorers list (no touchdowns)
    all_td_scorers = []

    # Action: Calculate ATTD points
    attd_points = await scoring_service.calculate_attd_points(pick, all_td_scorers)

    # Assert: Verify correctness property
    assert attd_points == 0, (
        f"Expected 0 ATTD points when no touchdowns scored, " f"but got {attd_points}"
    )


@pytest.mark.asyncio
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    ftd_points=st.sampled_from([0, 3]),  # FTD points are either 0 or 3
    attd_points=st.sampled_from([0, 1]),  # ATTD points are either 0 or 1
)
async def test_property_10_total_points_calculation(
    db_session,
    ftd_points,
    attd_points,
):
    """
    Feature: scoring-system, Property 10: Total points calculation

    For any pick, total_points should equal ftd_points + attd_points.

    Validates: Requirements 5.3
    """
    # Setup: Create service
    scoring_service = ScoringService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    db_session.add(home_team)
    await db_session.commit()

    # Setup: Create game
    game = Game(
        id=uuid4(),
        external_id=f"game_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=home_team.id,
        kickoff_time=datetime.now(timezone.utc) + timedelta(hours=1),
        game_date=datetime.now(timezone.utc) + timedelta(hours=1),
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
        name="Player",
        team_id=home_team.id,
        position="RB",
        jersey_number=1,
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
    pick = Pick(
        id=uuid4(),
        user_id=user.id,
        game_id=game.id,
        player_id=player.id,
        status=PickResult.PENDING,
    )
    db_session.add(pick)
    await db_session.commit()

    # Action: Update pick result with given points
    status = PickResult.WIN if (ftd_points > 0 or attd_points > 0) else PickResult.LOSS
    await scoring_service.update_pick_result(pick, ftd_points, attd_points, status)

    # Refresh pick from database
    await db_session.refresh(pick)

    # Assert: Verify total points calculation property
    expected_total = ftd_points + attd_points
    assert pick.total_points == expected_total, (
        f"Expected total_points to be {expected_total} (ftd={ftd_points} + attd={attd_points}), "
        f"but got {pick.total_points}"
    )

    # Additional verification: Verify individual points are stored correctly
    assert (
        pick.ftd_points == ftd_points
    ), f"Expected ftd_points to be {ftd_points}, but got {pick.ftd_points}"
    assert (
        pick.attd_points == attd_points
    ), f"Expected attd_points to be {attd_points}, but got {pick.attd_points}"


@pytest.mark.asyncio
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    num_other_td_scorers=st.integers(min_value=0, max_value=5),  # 0-5 other TD scorers
)
async def test_property_13_ftd_and_attd_stacking(
    db_session,
    num_other_td_scorers,
):
    """
    Feature: scoring-system, Property 13: FTD and ATTD stacking

    For any pick where the player scored the first touchdown, both ftd_points (3)
    and attd_points (1) should be awarded, totaling 4 points.

    Validates: Requirements 16.1, 16.2, 16.3
    """
    # Setup: Create service
    scoring_service = ScoringService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    db_session.add(home_team)
    await db_session.commit()

    # Setup: Create game
    game = Game(
        id=uuid4(),
        external_id=f"game_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=home_team.id,
        kickoff_time=datetime.now(timezone.utc) + timedelta(hours=1),
        game_date=datetime.now(timezone.utc) + timedelta(hours=1),
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.SCHEDULED,
    )
    db_session.add(game)
    await db_session.commit()

    # Setup: Create picked player (who will score first TD)
    picked_player = Player(
        id=uuid4(),
        external_id=f"player_picked_{uuid4().hex[:8]}",
        name="Picked Player",
        team_id=home_team.id,
        position="RB",
        jersey_number=1,
        is_active=True,
    )
    db_session.add(picked_player)
    await db_session.commit()

    # Setup: Create other TD scorers
    other_td_scorers = []
    for i in range(num_other_td_scorers):
        player = Player(
            id=uuid4(),
            external_id=f"player_other_{i}_{uuid4().hex[:8]}",
            name=f"Other Player {i}",
            team_id=home_team.id,
            position="WR",
            jersey_number=i + 10,
            is_active=True,
        )
        db_session.add(player)
        other_td_scorers.append(player)
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
    pick = Pick(
        id=uuid4(),
        user_id=user.id,
        game_id=game.id,
        player_id=picked_player.id,
        status=PickResult.PENDING,
    )
    db_session.add(pick)
    await db_session.commit()

    # Setup: Picked player scored first TD
    first_td_scorer = picked_player.id

    # Setup: Build list of all TD scorers (picked player + others)
    all_td_scorers = [picked_player.id] + [p.id for p in other_td_scorers]

    # Action: Calculate FTD and ATTD points
    ftd_points = await scoring_service.calculate_ftd_points(pick, first_td_scorer)
    attd_points = await scoring_service.calculate_attd_points(pick, all_td_scorers)

    # Assert: Verify FTD and ATTD stacking property
    # Requirement 16.1: Both FTD and ATTD points should be awarded
    assert (
        ftd_points == 3
    ), f"Expected 3 FTD points when player scored first TD, but got {ftd_points}"
    assert (
        attd_points == 1
    ), f"Expected 1 ATTD point when player scored any TD, but got {attd_points}"

    # Requirement 16.2: Total should be 4 points
    total_points = ftd_points + attd_points
    assert total_points == 4, (
        f"Expected 4 total points (3 FTD + 1 ATTD) when player scored first TD, "
        f"but got {total_points}"
    )

    # Additional verification: Update pick and verify total_points field
    status = PickResult.WIN
    await scoring_service.update_pick_result(pick, ftd_points, attd_points, status)
    await db_session.refresh(pick)

    # Requirement 16.3: Both point types should be recorded separately
    assert (
        pick.ftd_points == 3
    ), f"Expected ftd_points to be 3, but got {pick.ftd_points}"
    assert (
        pick.attd_points == 1
    ), f"Expected attd_points to be 1, but got {pick.attd_points}"
    assert (
        pick.total_points == 4
    ), f"Expected total_points to be 4, but got {pick.total_points}"


@pytest.mark.asyncio
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    num_tds_by_player=st.integers(min_value=2, max_value=5),  # Player scores 2-5 TDs
    num_other_td_scorers=st.integers(min_value=0, max_value=3),  # 0-3 other TD scorers
)
async def test_property_12_multiple_touchdowns_by_same_player(
    db_session,
    num_tds_by_player,
    num_other_td_scorers,
):
    """
    Feature: scoring-system, Property 12: Multiple touchdowns by same player

    For any pick where the player appears multiple times in touchdown events,
    attd_points should still be 1 (not multiplied by number of TDs).

    Validates: Requirements 15.1, 15.2, 15.3
    """
    # Setup: Create service
    scoring_service = ScoringService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    db_session.add(home_team)
    await db_session.commit()

    # Setup: Create game
    game = Game(
        id=uuid4(),
        external_id=f"game_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=home_team.id,
        kickoff_time=datetime.now(timezone.utc) + timedelta(hours=1),
        game_date=datetime.now(timezone.utc) + timedelta(hours=1),
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.SCHEDULED,
    )
    db_session.add(game)
    await db_session.commit()

    # Setup: Create picked player (who will score multiple TDs)
    picked_player = Player(
        id=uuid4(),
        external_id=f"player_picked_{uuid4().hex[:8]}",
        name="Picked Player",
        team_id=home_team.id,
        position="RB",
        jersey_number=1,
        is_active=True,
    )
    db_session.add(picked_player)
    await db_session.commit()

    # Setup: Create other TD scorers
    other_td_scorers = []
    for i in range(num_other_td_scorers):
        player = Player(
            id=uuid4(),
            external_id=f"player_other_{i}_{uuid4().hex[:8]}",
            name=f"Other Player {i}",
            team_id=home_team.id,
            position="WR",
            jersey_number=i + 10,
            is_active=True,
        )
        db_session.add(player)
        other_td_scorers.append(player)
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
    pick = Pick(
        id=uuid4(),
        user_id=user.id,
        game_id=game.id,
        player_id=picked_player.id,
        status=PickResult.PENDING,
    )
    db_session.add(pick)
    await db_session.commit()

    # Setup: Build list of all TD scorers with picked player appearing multiple times
    # Requirement 15.2: Player appears multiple times in the list
    all_td_scorers = [picked_player.id] * num_tds_by_player + [
        p.id for p in other_td_scorers
    ]

    # Action: Calculate ATTD points
    attd_points = await scoring_service.calculate_attd_points(pick, all_td_scorers)

    # Assert: Verify multiple touchdowns property
    # Requirement 15.1 & 15.3: ATTD points should be 1, not multiplied by number of TDs
    assert attd_points == 1, (
        f"Expected 1 ATTD point even though player scored {num_tds_by_player} TDs, "
        f"but got {attd_points}"
    )

    # Additional verification: Verify the player appears multiple times in the list
    player_td_count = all_td_scorers.count(picked_player.id)
    assert player_td_count == num_tds_by_player, (
        f"Expected player to appear {num_tds_by_player} times in TD list, "
        f"but appears {player_td_count} times"
    )

    # Additional verification: Update pick and verify total points
    # Assume player did NOT score first TD (to isolate ATTD points)
    first_td_scorer = other_td_scorers[0].id if other_td_scorers else None
    ftd_points = await scoring_service.calculate_ftd_points(pick, first_td_scorer)

    status = PickResult.WIN if (ftd_points > 0 or attd_points > 0) else PickResult.LOSS
    await scoring_service.update_pick_result(pick, ftd_points, attd_points, status)
    await db_session.refresh(pick)

    assert (
        pick.attd_points == 1
    ), f"Expected attd_points to be 1 in database, but got {pick.attd_points}"


@pytest.mark.asyncio
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    num_pending_picks=st.integers(min_value=0, max_value=10),  # 0-10 pending picks
    num_graded_picks=st.integers(
        min_value=0, max_value=10
    ),  # 0-10 already graded picks
)
async def test_property_1_pending_pick_identification(
    db_session,
    num_pending_picks,
    num_graded_picks,
):
    """
    Feature: scoring-system, Property 1: Pending pick identification

    For any completed game, the scoring system should identify exactly the picks
    with status=pending for that game_id.

    Validates: Requirements 1.1
    """
    # Setup: Create service
    scoring_service = ScoringService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    away_team = Team(
        id=uuid4(),
        external_id=f"away_{uuid4().hex[:8]}",
        name="Away Team",
        abbreviation="AWY",
        city="Away City",
    )
    db_session.add(home_team)
    db_session.add(away_team)
    await db_session.commit()

    # Setup: Create game
    game = Game(
        id=uuid4(),
        external_id=f"game_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        kickoff_time=datetime.now(timezone.utc) - timedelta(hours=3),
        game_date=datetime.now(timezone.utc) - timedelta(hours=3),
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.COMPLETED,
        first_td_scorer_player_id=None,  # No TDs for simplicity
        all_td_scorer_player_ids=[],
    )
    db_session.add(game)
    await db_session.commit()

    # Setup: Create player
    player = Player(
        id=uuid4(),
        external_id=f"player_{uuid4().hex[:8]}",
        name="Player",
        team_id=home_team.id,
        position="RB",
        jersey_number=1,
        is_active=True,
    )
    db_session.add(player)
    await db_session.commit()

    # Setup: Create users and pending picks
    pending_pick_ids = []
    for i in range(num_pending_picks):
        user = User(
            id=uuid4(),
            email=f"user_pending_{i}_{uuid4().hex[:8]}@example.com",
            username=f"user_pending_{i}_{uuid4().hex[:8]}",
            display_name=f"Pending User {i}",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        pick = Pick(
            id=uuid4(),
            user_id=user.id,
            game_id=game.id,
            player_id=player.id,
            status=PickResult.PENDING,
        )
        db_session.add(pick)
        pending_pick_ids.append(pick.id)
    await db_session.commit()

    # Setup: Create users and already graded picks
    graded_pick_ids = []
    for i in range(num_graded_picks):
        user = User(
            id=uuid4(),
            email=f"user_graded_{i}_{uuid4().hex[:8]}@example.com",
            username=f"user_graded_{i}_{uuid4().hex[:8]}",
            display_name=f"Graded User {i}",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        pick = Pick(
            id=uuid4(),
            user_id=user.id,
            game_id=game.id,
            player_id=player.id,
            status=PickResult.LOSS,  # Already graded
            scored_at=datetime.now(timezone.utc) - timedelta(hours=1),
            ftd_points=0,
            attd_points=0,
            total_points=0,
        )
        db_session.add(pick)
        graded_pick_ids.append(pick.id)
    await db_session.commit()

    # Action: Grade the game
    graded_count = await scoring_service.grade_game(game.id)

    # Assert: Verify pending pick identification property
    # Should grade exactly the pending picks, not the already graded ones
    assert graded_count == num_pending_picks, (
        f"Expected to grade {num_pending_picks} pending picks, "
        f"but graded {graded_count}"
    )

    # Verify all pending picks are now graded
    for pick_id in pending_pick_ids:
        result = await db_session.execute(select(Pick).where(Pick.id == pick_id))
        pick = result.scalar_one()
        assert (
            pick.status != PickResult.PENDING
        ), f"Pick {pick_id} should no longer be PENDING after grading"
        assert (
            pick.scored_at is not None
        ), f"Pick {pick_id} should have scored_at timestamp"

    # Verify already graded picks remain unchanged
    for pick_id in graded_pick_ids:
        result = await db_session.execute(select(Pick).where(Pick.id == pick_id))
        pick = result.scalar_one()
        assert (
            pick.status == PickResult.LOSS
        ), f"Already graded pick {pick_id} should remain LOSS"


@pytest.mark.asyncio
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    player_scored=st.booleans(),  # Whether the picked player scored
)
async def test_property_2_pick_status_update_on_grading(
    db_session,
    player_scored,
):
    """
    Feature: scoring-system, Property 2: Pick status update on grading

    For any pick that is graded, the status should change from pending to either
    win or loss, never remaining pending.

    Validates: Requirements 1.3
    """
    # Setup: Create service
    scoring_service = ScoringService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    db_session.add(home_team)
    await db_session.commit()

    # Setup: Create players
    picked_player = Player(
        id=uuid4(),
        external_id=f"player_picked_{uuid4().hex[:8]}",
        name="Picked Player",
        team_id=home_team.id,
        position="RB",
        jersey_number=1,
        is_active=True,
    )
    other_player = Player(
        id=uuid4(),
        external_id=f"player_other_{uuid4().hex[:8]}",
        name="Other Player",
        team_id=home_team.id,
        position="WR",
        jersey_number=2,
        is_active=True,
    )
    db_session.add(picked_player)
    db_session.add(other_player)
    await db_session.commit()

    # Setup: Create game with TD data
    if player_scored:
        first_td_scorer = picked_player.id
        all_td_scorers = [str(picked_player.id)]  # Convert to string for JSON
    else:
        first_td_scorer = other_player.id
        all_td_scorers = [str(other_player.id)]  # Convert to string for JSON

    game = Game(
        id=uuid4(),
        external_id=f"game_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=home_team.id,
        kickoff_time=datetime.now(timezone.utc) - timedelta(hours=3),
        game_date=datetime.now(timezone.utc) - timedelta(hours=3),
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.COMPLETED,
        first_td_scorer_player_id=first_td_scorer,
        all_td_scorer_player_ids=all_td_scorers,
    )
    db_session.add(game)
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

    # Setup: Create pending pick
    pick = Pick(
        id=uuid4(),
        user_id=user.id,
        game_id=game.id,
        player_id=picked_player.id,
        status=PickResult.PENDING,
    )
    db_session.add(pick)
    await db_session.commit()

    # Verify pick starts as PENDING
    assert pick.status == PickResult.PENDING, "Pick should start as PENDING"

    # Action: Grade the game
    await scoring_service.grade_game(game.id)

    # Refresh pick from database
    await db_session.refresh(pick)

    # Assert: Verify pick status update property
    # Pick should no longer be PENDING
    assert pick.status != PickResult.PENDING, (
        f"Pick status should change from PENDING after grading, "
        f"but is still {pick.status}"
    )

    # Pick should be either WIN or LOSS
    assert pick.status in [PickResult.WIN, PickResult.LOSS], (
        f"Pick status should be WIN or LOSS after grading, " f"but is {pick.status}"
    )

    # Verify status matches scoring outcome
    if player_scored:
        assert (
            pick.status == PickResult.WIN
        ), f"Pick should be WIN when player scored, but is {pick.status}"
    else:
        assert (
            pick.status == PickResult.LOSS
        ), f"Pick should be LOSS when player didn't score, but is {pick.status}"


@pytest.mark.asyncio
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    num_picks=st.integers(min_value=1, max_value=5),  # 1-5 picks to grade
)
async def test_property_3_grading_timestamp_recorded(
    db_session,
    num_picks,
):
    """
    Feature: scoring-system, Property 3: Grading timestamp recorded

    For any pick that is graded, the scored_at timestamp should be set to a
    recent time (within last minute).

    Validates: Requirements 1.4
    """
    # Setup: Create service
    scoring_service = ScoringService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    db_session.add(home_team)
    await db_session.commit()

    # Setup: Create player
    player = Player(
        id=uuid4(),
        external_id=f"player_{uuid4().hex[:8]}",
        name="Player",
        team_id=home_team.id,
        position="RB",
        jersey_number=1,
        is_active=True,
    )
    db_session.add(player)
    await db_session.commit()

    # Setup: Create game (no TDs for simplicity)
    game = Game(
        id=uuid4(),
        external_id=f"game_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=home_team.id,
        kickoff_time=datetime.now(timezone.utc) - timedelta(hours=3),
        game_date=datetime.now(timezone.utc) - timedelta(hours=3),
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.COMPLETED,
        first_td_scorer_player_id=None,
        all_td_scorer_player_ids=[],
    )
    db_session.add(game)
    await db_session.commit()

    # Setup: Create users and pending picks
    pick_ids = []
    for i in range(num_picks):
        user = User(
            id=uuid4(),
            email=f"user_{i}_{uuid4().hex[:8]}@example.com",
            username=f"user_{i}_{uuid4().hex[:8]}",
            display_name=f"User {i}",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        pick = Pick(
            id=uuid4(),
            user_id=user.id,
            game_id=game.id,
            player_id=player.id,
            status=PickResult.PENDING,
        )
        db_session.add(pick)
        pick_ids.append(pick.id)
    await db_session.commit()

    # Record time before grading
    time_before_grading = datetime.now(timezone.utc)

    # Action: Grade the game
    await scoring_service.grade_game(game.id)

    # Record time after grading
    time_after_grading = datetime.now(timezone.utc)

    # Assert: Verify grading timestamp property
    for pick_id in pick_ids:
        result = await db_session.execute(select(Pick).where(Pick.id == pick_id))
        pick = result.scalar_one()

        # Pick should have scored_at timestamp
        assert (
            pick.scored_at is not None
        ), f"Pick {pick_id} should have scored_at timestamp after grading"

        # Timestamp should be recent (within the grading window)
        assert time_before_grading <= pick.scored_at <= time_after_grading, (
            f"Pick {pick_id} scored_at timestamp {pick.scored_at} should be between "
            f"{time_before_grading} and {time_after_grading}"
        )

        # Timestamp should be within last minute (reasonable window)
        time_diff = (time_after_grading - pick.scored_at).total_seconds()
        assert time_diff < 60, (
            f"Pick {pick_id} scored_at timestamp should be within last minute, "
            f"but was {time_diff} seconds ago"
        )


@pytest.mark.asyncio
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    player_scored=st.booleans(),  # Whether the picked player scored
    num_regrading_attempts=st.integers(
        min_value=1, max_value=3
    ),  # 1-3 regrading attempts
)
async def test_property_4_grading_idempotence(
    db_session,
    player_scored,
    num_regrading_attempts,
):
    """
    Feature: scoring-system, Property 4: Grading idempotence

    For any pick that has been graded, grading the same game again should not
    change the pick's status or points.

    Validates: Requirements 1.5
    """
    # Setup: Create service
    scoring_service = ScoringService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    db_session.add(home_team)
    await db_session.commit()

    # Setup: Create players
    picked_player = Player(
        id=uuid4(),
        external_id=f"player_picked_{uuid4().hex[:8]}",
        name="Picked Player",
        team_id=home_team.id,
        position="RB",
        jersey_number=1,
        is_active=True,
    )
    other_player = Player(
        id=uuid4(),
        external_id=f"player_other_{uuid4().hex[:8]}",
        name="Other Player",
        team_id=home_team.id,
        position="WR",
        jersey_number=2,
        is_active=True,
    )
    db_session.add(picked_player)
    db_session.add(other_player)
    await db_session.commit()

    # Setup: Create game with TD data
    if player_scored:
        first_td_scorer = picked_player.id
        all_td_scorers = [str(picked_player.id)]
    else:
        first_td_scorer = other_player.id
        all_td_scorers = [str(other_player.id)]

    game = Game(
        id=uuid4(),
        external_id=f"game_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=home_team.id,
        kickoff_time=datetime.now(timezone.utc) - timedelta(hours=3),
        game_date=datetime.now(timezone.utc) - timedelta(hours=3),
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.COMPLETED,
        first_td_scorer_player_id=first_td_scorer,
        all_td_scorer_player_ids=all_td_scorers,
    )
    db_session.add(game)
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

    # Setup: Create pending pick
    pick = Pick(
        id=uuid4(),
        user_id=user.id,
        game_id=game.id,
        player_id=picked_player.id,
        status=PickResult.PENDING,
    )
    db_session.add(pick)
    await db_session.commit()

    # Action: Grade the game for the first time
    await scoring_service.grade_game(game.id)

    # Capture state after first grading
    await db_session.refresh(pick)
    first_status = pick.status
    first_ftd_points = pick.ftd_points
    first_attd_points = pick.attd_points
    first_total_points = pick.total_points
    first_scored_at = pick.scored_at

    # Capture user state after first grading
    await db_session.refresh(user)
    first_user_score = user.total_score
    first_user_wins = user.total_wins
    first_user_losses = user.total_losses

    # Action: Re-grade the game multiple times
    for i in range(num_regrading_attempts):
        await scoring_service.grade_game(game.id)

        # Refresh pick and user from database
        await db_session.refresh(pick)
        await db_session.refresh(user)

        # Assert: Verify idempotence property - pick should not change
        assert pick.status == first_status, (
            f"Pick status changed from {first_status} to {pick.status} "
            f"after regrading attempt {i + 1}"
        )
        assert pick.ftd_points == first_ftd_points, (
            f"Pick ftd_points changed from {first_ftd_points} to {pick.ftd_points} "
            f"after regrading attempt {i + 1}"
        )
        assert pick.attd_points == first_attd_points, (
            f"Pick attd_points changed from {first_attd_points} to {pick.attd_points} "
            f"after regrading attempt {i + 1}"
        )
        assert pick.total_points == first_total_points, (
            f"Pick total_points changed from {first_total_points} to {pick.total_points} "
            f"after regrading attempt {i + 1}"
        )
        assert pick.scored_at == first_scored_at, (
            f"Pick scored_at changed from {first_scored_at} to {pick.scored_at} "
            f"after regrading attempt {i + 1}"
        )

        # Assert: Verify user scores don't change on regrading
        assert user.total_score == first_user_score, (
            f"User total_score changed from {first_user_score} to {user.total_score} "
            f"after regrading attempt {i + 1}"
        )
        assert user.total_wins == first_user_wins, (
            f"User total_wins changed from {first_user_wins} to {user.total_wins} "
            f"after regrading attempt {i + 1}"
        )
        assert user.total_losses == first_user_losses, (
            f"User total_losses changed from {first_user_losses} to {user.total_losses} "
            f"after regrading attempt {i + 1}"
        )


@pytest.mark.asyncio
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    num_other_td_scorers=st.integers(min_value=0, max_value=5),  # 0-5 other TD scorers
)
async def test_property_8_loss_status_for_non_scoring_picks(
    db_session,
    num_other_td_scorers,
):
    """
    Feature: scoring-system, Property 8: Loss status for non-scoring picks

    For any pick where the player did not score (ftd_points=0 and attd_points=0),
    the status should be loss.

    Validates: Requirements 4.1, 4.3
    """
    # Setup: Create service
    scoring_service = ScoringService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    db_session.add(home_team)
    await db_session.commit()

    # Setup: Create picked player (who will NOT score)
    picked_player = Player(
        id=uuid4(),
        external_id=f"player_picked_{uuid4().hex[:8]}",
        name="Picked Player",
        team_id=home_team.id,
        position="RB",
        jersey_number=1,
        is_active=True,
    )
    db_session.add(picked_player)
    await db_session.commit()

    # Setup: Create other TD scorers (not the picked player)
    other_td_scorers = []
    for i in range(num_other_td_scorers):
        player = Player(
            id=uuid4(),
            external_id=f"player_other_{i}_{uuid4().hex[:8]}",
            name=f"Other Player {i}",
            team_id=home_team.id,
            position="WR",
            jersey_number=i + 10,
            is_active=True,
        )
        db_session.add(player)
        other_td_scorers.append(player)
    await db_session.commit()

    # Setup: Create game with TD data (picked player did NOT score)
    first_td_scorer = other_td_scorers[0].id if other_td_scorers else None
    all_td_scorers = [str(p.id) for p in other_td_scorers]

    game = Game(
        id=uuid4(),
        external_id=f"game_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=home_team.id,
        kickoff_time=datetime.now(timezone.utc) - timedelta(hours=3),
        game_date=datetime.now(timezone.utc) - timedelta(hours=3),
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.COMPLETED,
        first_td_scorer_player_id=first_td_scorer,
        all_td_scorer_player_ids=all_td_scorers,
    )
    db_session.add(game)
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

    # Setup: Create pending pick
    pick = Pick(
        id=uuid4(),
        user_id=user.id,
        game_id=game.id,
        player_id=picked_player.id,
        status=PickResult.PENDING,
    )
    db_session.add(pick)
    await db_session.commit()

    # Action: Grade the game
    await scoring_service.grade_game(game.id)

    # Refresh pick from database
    await db_session.refresh(pick)

    # Assert: Verify loss status property
    # Pick should have 0 points
    assert pick.ftd_points == 0, (
        f"Expected ftd_points to be 0 when player didn't score, "
        f"but got {pick.ftd_points}"
    )
    assert pick.attd_points == 0, (
        f"Expected attd_points to be 0 when player didn't score, "
        f"but got {pick.attd_points}"
    )
    assert pick.total_points == 0, (
        f"Expected total_points to be 0 when player didn't score, "
        f"but got {pick.total_points}"
    )

    # Pick should be marked as LOSS
    assert pick.status == PickResult.LOSS, (
        f"Expected pick status to be LOSS when player didn't score, "
        f"but got {pick.status}"
    )


@pytest.mark.asyncio
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    scored_ftd=st.booleans(),  # Whether player scored FTD
    scored_attd=st.booleans(),  # Whether player scored ATTD (but not FTD)
)
async def test_property_9_win_status_for_scoring_picks(
    db_session,
    scored_ftd,
    scored_attd,
):
    """
    Feature: scoring-system, Property 9: Win status for scoring picks

    For any pick where the player scored (ftd_points>0 or attd_points>0),
    the status should be win.

    Validates: Requirements 5.1, 5.2
    """
    # Skip cases where player didn't score at all
    if not scored_ftd and not scored_attd:
        return

    # Setup: Create service
    scoring_service = ScoringService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    db_session.add(home_team)
    await db_session.commit()

    # Setup: Create picked player
    picked_player = Player(
        id=uuid4(),
        external_id=f"player_picked_{uuid4().hex[:8]}",
        name="Picked Player",
        team_id=home_team.id,
        position="RB",
        jersey_number=1,
        is_active=True,
    )
    db_session.add(picked_player)
    await db_session.commit()

    # Setup: Create other player for first TD if needed
    other_player = Player(
        id=uuid4(),
        external_id=f"player_other_{uuid4().hex[:8]}",
        name="Other Player",
        team_id=home_team.id,
        position="WR",
        jersey_number=2,
        is_active=True,
    )
    db_session.add(other_player)
    await db_session.commit()

    # Setup: Create game with TD data based on test parameters
    if scored_ftd:
        # Player scored first TD (and also ATTD)
        first_td_scorer = picked_player.id
        all_td_scorers = [str(picked_player.id)]
    elif scored_attd:
        # Player scored ATTD but not first TD
        first_td_scorer = other_player.id
        all_td_scorers = [str(other_player.id), str(picked_player.id)]
    else:
        # This case is skipped above
        return

    game = Game(
        id=uuid4(),
        external_id=f"game_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=home_team.id,
        kickoff_time=datetime.now(timezone.utc) - timedelta(hours=3),
        game_date=datetime.now(timezone.utc) - timedelta(hours=3),
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.COMPLETED,
        first_td_scorer_player_id=first_td_scorer,
        all_td_scorer_player_ids=all_td_scorers,
    )
    db_session.add(game)
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

    # Setup: Create pending pick
    pick = Pick(
        id=uuid4(),
        user_id=user.id,
        game_id=game.id,
        player_id=picked_player.id,
        status=PickResult.PENDING,
    )
    db_session.add(pick)
    await db_session.commit()

    # Action: Grade the game
    await scoring_service.grade_game(game.id)

    # Refresh pick from database
    await db_session.refresh(pick)

    # Assert: Verify win status property
    # Pick should have points > 0
    assert pick.ftd_points > 0 or pick.attd_points > 0, (
        f"Expected pick to have points when player scored, "
        f"but got ftd={pick.ftd_points}, attd={pick.attd_points}"
    )
    assert pick.total_points > 0, (
        f"Expected total_points > 0 when player scored, " f"but got {pick.total_points}"
    )

    # Pick should be marked as WIN
    assert pick.status == PickResult.WIN, (
        f"Expected pick status to be WIN when player scored, " f"but got {pick.status}"
    )

    # Verify expected points based on scoring type
    if scored_ftd:
        assert pick.ftd_points == 3, (
            f"Expected ftd_points to be 3 when player scored first TD, "
            f"but got {pick.ftd_points}"
        )
        assert pick.attd_points == 1, (
            f"Expected attd_points to be 1 when player scored first TD, "
            f"but got {pick.attd_points}"
        )
        assert pick.total_points == 4, (
            f"Expected total_points to be 4 when player scored first TD, "
            f"but got {pick.total_points}"
        )
    elif scored_attd:
        assert pick.ftd_points == 0, (
            f"Expected ftd_points to be 0 when player scored ATTD only, "
            f"but got {pick.ftd_points}"
        )
        assert pick.attd_points == 1, (
            f"Expected attd_points to be 1 when player scored ATTD, "
            f"but got {pick.attd_points}"
        )
        assert pick.total_points == 1, (
            f"Expected total_points to be 1 when player scored ATTD only, "
            f"but got {pick.total_points}"
        )


@pytest.mark.asyncio
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    num_picks=st.integers(min_value=1, max_value=10),  # 1-10 picks for the game
)
async def test_property_11_zero_touchdown_game_handling(
    db_session,
    num_picks,
):
    """
    Feature: scoring-system, Property 11: Zero touchdown game handling

    For any game with zero touchdowns (first_td_scorer_player_id is null),
    all picks for that game should have status=loss and total_points=0.

    Validates: Requirements 6.1
    """
    # Setup: Create service
    scoring_service = ScoringService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    db_session.add(home_team)
    await db_session.commit()

    # Setup: Create players
    players = []
    for i in range(num_picks):
        player = Player(
            id=uuid4(),
            external_id=f"player_{i}_{uuid4().hex[:8]}",
            name=f"Player {i}",
            team_id=home_team.id,
            position="RB",
            jersey_number=i + 1,
            is_active=True,
        )
        db_session.add(player)
        players.append(player)
    await db_session.commit()

    # Setup: Create game with ZERO touchdowns
    game = Game(
        id=uuid4(),
        external_id=f"game_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=home_team.id,
        kickoff_time=datetime.now(timezone.utc) - timedelta(hours=3),
        game_date=datetime.now(timezone.utc) - timedelta(hours=3),
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.COMPLETED,
        first_td_scorer_player_id=None,  # No first TD scorer
        all_td_scorer_player_ids=[],  # No TD scorers at all
    )
    db_session.add(game)
    await db_session.commit()

    # Setup: Create users and pending picks
    pick_ids = []
    for i in range(num_picks):
        user = User(
            id=uuid4(),
            email=f"user_{i}_{uuid4().hex[:8]}@example.com",
            username=f"user_{i}_{uuid4().hex[:8]}",
            display_name=f"User {i}",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        pick = Pick(
            id=uuid4(),
            user_id=user.id,
            game_id=game.id,
            player_id=players[i].id,
            status=PickResult.PENDING,
        )
        db_session.add(pick)
        pick_ids.append(pick.id)
    await db_session.commit()

    # Action: Grade the game
    graded_count = await scoring_service.grade_game(game.id)

    # Assert: Verify all picks were graded
    assert (
        graded_count == num_picks
    ), f"Expected to grade {num_picks} picks, but graded {graded_count}"

    # Assert: Verify zero touchdown game handling property
    for pick_id in pick_ids:
        result = await db_session.execute(select(Pick).where(Pick.id == pick_id))
        pick = result.scalar_one()

        # All picks should be marked as LOSS
        assert pick.status == PickResult.LOSS, (
            f"Pick {pick_id} should be LOSS in zero touchdown game, "
            f"but is {pick.status}"
        )

        # All picks should have 0 points
        assert pick.ftd_points == 0, (
            f"Pick {pick_id} should have 0 ftd_points in zero touchdown game, "
            f"but has {pick.ftd_points}"
        )
        assert pick.attd_points == 0, (
            f"Pick {pick_id} should have 0 attd_points in zero touchdown game, "
            f"but has {pick.attd_points}"
        )
        assert pick.total_points == 0, (
            f"Pick {pick_id} should have 0 total_points in zero touchdown game, "
            f"but has {pick.total_points}"
        )

        # Pick should have been graded (scored_at set)
        assert (
            pick.scored_at is not None
        ), f"Pick {pick_id} should have scored_at timestamp"


@pytest.mark.asyncio
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    ftd_points=st.sampled_from([0, 3]),  # FTD points are either 0 or 3
    attd_points=st.sampled_from([0, 1]),  # ATTD points are either 0 or 1
)
async def test_property_7_user_score_update(
    db_session,
    ftd_points,
    attd_points,
):
    """
    Feature: scoring-system, Property 7: User score update

    For any pick that is graded, the user's total_score should increase by the
    pick's total_points (ftd_points + attd_points).

    Validates: Requirements 2.4, 3.4
    """
    # Setup: Create service
    scoring_service = ScoringService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    db_session.add(home_team)
    await db_session.commit()

    # Setup: Create player
    player = Player(
        id=uuid4(),
        external_id=f"player_{uuid4().hex[:8]}",
        name="Player",
        team_id=home_team.id,
        position="RB",
        jersey_number=1,
        is_active=True,
    )
    db_session.add(player)
    await db_session.commit()

    # Setup: Create game
    game = Game(
        id=uuid4(),
        external_id=f"game_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=home_team.id,
        kickoff_time=datetime.now(timezone.utc) - timedelta(hours=3),
        game_date=datetime.now(timezone.utc) - timedelta(hours=3),
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.COMPLETED,
    )
    db_session.add(game)
    await db_session.commit()

    # Setup: Create user
    user = User(
        id=uuid4(),
        email=f"user_{uuid4().hex[:8]}@example.com",
        username=f"user_{uuid4().hex[:8]}",
        display_name=f"User {uuid4().hex[:8]}",
        is_active=True,
        total_score=0,
        total_wins=0,
        total_losses=0,
    )
    db_session.add(user)
    await db_session.commit()

    # Capture initial user score
    initial_score = user.total_score
    initial_wins = user.total_wins
    initial_losses = user.total_losses

    # Setup: Create pick
    pick = Pick(
        id=uuid4(),
        user_id=user.id,
        game_id=game.id,
        player_id=player.id,
        status=PickResult.PENDING,
    )
    db_session.add(pick)
    await db_session.commit()

    # Action: Update pick result and user score
    total_points = ftd_points + attd_points
    is_win = total_points > 0
    status = PickResult.WIN if is_win else PickResult.LOSS

    await scoring_service.update_pick_result(pick, ftd_points, attd_points, status)
    await scoring_service.update_user_score(user.id, total_points, is_win)

    # Refresh user from database
    await db_session.refresh(user)

    # Assert: Verify user score update property
    expected_score = initial_score + total_points
    assert user.total_score == expected_score, (
        f"Expected user total_score to be {expected_score} "
        f"(initial {initial_score} + {total_points}), "
        f"but got {user.total_score}"
    )

    # Verify win/loss counts updated correctly
    if is_win:
        expected_wins = initial_wins + 1
        expected_losses = initial_losses
        assert user.total_wins == expected_wins, (
            f"Expected user total_wins to be {expected_wins}, "
            f"but got {user.total_wins}"
        )
        assert user.total_losses == expected_losses, (
            f"Expected user total_losses to be {expected_losses}, "
            f"but got {user.total_losses}"
        )
    else:
        expected_wins = initial_wins
        expected_losses = initial_losses + 1
        assert user.total_wins == expected_wins, (
            f"Expected user total_wins to be {expected_wins}, "
            f"but got {user.total_wins}"
        )
        assert user.total_losses == expected_losses, (
            f"Expected user total_losses to be {expected_losses}, "
            f"but got {user.total_losses}"
        )


@pytest.mark.asyncio
@settings(
    max_examples=30,  # Reduced from 100 due to heavy database operations
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    num_winning_picks=st.integers(min_value=0, max_value=10),  # 0-10 winning picks
    num_losing_picks=st.integers(min_value=0, max_value=10),  # 0-10 losing picks
)
async def test_property_14_user_total_score_accuracy(
    db_session,
    num_winning_picks,
    num_losing_picks,
):
    """
    Feature: scoring-system, Property 14: User total score accuracy

    For any user, the total_score should equal the sum of total_points from all
    picks with status=win.

    Validates: Requirements 11.1, 11.2, 11.3
    """
    # Setup: Create service
    scoring_service = ScoringService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    db_session.add(home_team)
    await db_session.commit()

    # Setup: Create player
    player = Player(
        id=uuid4(),
        external_id=f"player_{uuid4().hex[:8]}",
        name="Player",
        team_id=home_team.id,
        position="RB",
        jersey_number=1,
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
        total_score=0,
        total_wins=0,
        total_losses=0,
    )
    db_session.add(user)
    await db_session.commit()

    # Setup: Create games
    games = []
    for i in range(num_winning_picks + num_losing_picks):
        game = Game(
            id=uuid4(),
            external_id=f"game_{i}_{uuid4().hex[:8]}",
            home_team_id=home_team.id,
            away_team_id=home_team.id,
            kickoff_time=datetime.now(timezone.utc) - timedelta(hours=3),
            game_date=datetime.now(timezone.utc) - timedelta(hours=3),
            week_number=1,
            season_year=2024,
            game_type=GameType.SUNDAY_MAIN,
            status=GameStatus.COMPLETED,
        )
        db_session.add(game)
        games.append(game)
    await db_session.commit()

    # Setup: Create winning picks with varying points
    expected_total_score = 0
    point_options = [1, 3, 4]  # Possible point values for winning picks
    for i in range(num_winning_picks):
        # Cycle through point options to get variety
        points = point_options[i % len(point_options)]
        ftd_points = 3 if points >= 3 else 0
        attd_points = 1 if points in [1, 4] else 0

        pick = Pick(
            id=uuid4(),
            user_id=user.id,
            game_id=games[i].id,
            player_id=player.id,
            status=PickResult.WIN,
            ftd_points=ftd_points,
            attd_points=attd_points,
            total_points=points,
            scored_at=datetime.now(timezone.utc),
        )
        db_session.add(pick)
        expected_total_score += points

    # Setup: Create losing picks (0 points)
    for i in range(num_losing_picks):
        pick = Pick(
            id=uuid4(),
            user_id=user.id,
            game_id=games[num_winning_picks + i].id,
            player_id=player.id,
            status=PickResult.LOSS,
            ftd_points=0,
            attd_points=0,
            total_points=0,
            scored_at=datetime.now(timezone.utc),
        )
        db_session.add(pick)
        # Losing picks don't contribute to total score

    await db_session.commit()

    # Setup: Update user's total_score to match the picks
    user.total_score = expected_total_score
    user.total_wins = num_winning_picks
    user.total_losses = num_losing_picks
    await db_session.commit()

    # Action: Get user total score
    user_score = await scoring_service.get_user_total_score(user.id)

    # Assert: Verify user total score accuracy property
    assert user_score is not None, "Expected user_score to be returned"
    assert user_score.total_score == expected_total_score, (
        f"Expected total_score to be {expected_total_score}, "
        f"but got {user_score.total_score}"
    )
    assert user_score.total_wins == num_winning_picks, (
        f"Expected total_wins to be {num_winning_picks}, "
        f"but got {user_score.total_wins}"
    )
    assert user_score.total_losses == num_losing_picks, (
        f"Expected total_losses to be {num_losing_picks}, "
        f"but got {user_score.total_losses}"
    )

    # Verify win percentage calculation
    total_picks = num_winning_picks + num_losing_picks
    expected_win_percentage = (
        (num_winning_picks / total_picks * 100) if total_picks > 0 else 0.0
    )
    assert abs(user_score.win_percentage - expected_win_percentage) < 0.01, (
        f"Expected win_percentage to be {expected_win_percentage}, "
        f"but got {user_score.win_percentage}"
    )


@pytest.mark.asyncio
@settings(
    max_examples=30,  # Reduced from 100 due to heavy database operations
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    num_winning_picks=st.integers(min_value=0, max_value=10),  # 0-10 winning picks
    num_losing_picks=st.integers(min_value=0, max_value=10),  # 0-10 losing picks
)
async def test_property_15_win_loss_count_accuracy(
    db_session,
    num_winning_picks,
    num_losing_picks,
):
    """
    Feature: scoring-system, Property 15: Win/loss count accuracy

    For any user, total_wins should equal the count of picks with status=win,
    and total_losses should equal the count of picks with status=loss.

    Validates: Requirements 11.4
    """
    # Setup: Create service
    scoring_service = ScoringService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    db_session.add(home_team)
    await db_session.commit()

    # Setup: Create player
    player = Player(
        id=uuid4(),
        external_id=f"player_{uuid4().hex[:8]}",
        name="Player",
        team_id=home_team.id,
        position="RB",
        jersey_number=1,
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
        total_score=0,
        total_wins=0,
        total_losses=0,
    )
    db_session.add(user)
    await db_session.commit()

    # Setup: Create games
    games = []
    for i in range(num_winning_picks + num_losing_picks):
        game = Game(
            id=uuid4(),
            external_id=f"game_{i}_{uuid4().hex[:8]}",
            home_team_id=home_team.id,
            away_team_id=home_team.id,
            kickoff_time=datetime.now(timezone.utc) - timedelta(hours=3),
            game_date=datetime.now(timezone.utc) - timedelta(hours=3),
            week_number=1,
            season_year=2024,
            game_type=GameType.SUNDAY_MAIN,
            status=GameStatus.COMPLETED,
        )
        db_session.add(game)
        games.append(game)
    await db_session.commit()

    # Setup: Create winning picks
    for i in range(num_winning_picks):
        pick = Pick(
            id=uuid4(),
            user_id=user.id,
            game_id=games[i].id,
            player_id=player.id,
            status=PickResult.WIN,
            ftd_points=3,
            attd_points=1,
            total_points=4,
            scored_at=datetime.now(timezone.utc),
        )
        db_session.add(pick)

    # Setup: Create losing picks
    for i in range(num_losing_picks):
        pick = Pick(
            id=uuid4(),
            user_id=user.id,
            game_id=games[num_winning_picks + i].id,
            player_id=player.id,
            status=PickResult.LOSS,
            ftd_points=0,
            attd_points=0,
            total_points=0,
            scored_at=datetime.now(timezone.utc),
        )
        db_session.add(pick)

    await db_session.commit()

    # Setup: Update user's win/loss counts to match the picks
    user.total_wins = num_winning_picks
    user.total_losses = num_losing_picks
    await db_session.commit()

    # Action: Get user total score
    user_score = await scoring_service.get_user_total_score(user.id)

    # Assert: Verify win/loss count accuracy property
    assert user_score is not None, "Expected user_score to be returned"

    # Verify win count matches actual winning picks
    assert user_score.total_wins == num_winning_picks, (
        f"Expected total_wins to equal count of winning picks ({num_winning_picks}), "
        f"but got {user_score.total_wins}"
    )

    # Verify loss count matches actual losing picks
    assert user_score.total_losses == num_losing_picks, (
        f"Expected total_losses to equal count of losing picks ({num_losing_picks}), "
        f"but got {user_score.total_losses}"
    )

    # Additional verification: Query database directly to confirm counts
    winning_picks_result = await db_session.execute(
        select(func.count(Pick.id)).where(
            Pick.user_id == user.id, Pick.status == PickResult.WIN
        )
    )
    actual_winning_count = winning_picks_result.scalar()

    losing_picks_result = await db_session.execute(
        select(func.count(Pick.id)).where(
            Pick.user_id == user.id, Pick.status == PickResult.LOSS
        )
    )
    actual_losing_count = losing_picks_result.scalar()

    assert user_score.total_wins == actual_winning_count, (
        f"User total_wins ({user_score.total_wins}) should match "
        f"actual winning picks count ({actual_winning_count})"
    )
    assert user_score.total_losses == actual_losing_count, (
        f"User total_losses ({user_score.total_losses}) should match "
        f"actual losing picks count ({actual_losing_count})"
    )


@pytest.mark.asyncio
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    game_exists=st.booleans(),  # Whether game exists in database
    first_td_player_exists=st.booleans(),  # Whether first TD scorer exists
    num_valid_td_scorers=st.integers(min_value=0, max_value=3),  # 0-3 valid TD scorers
    num_invalid_td_scorers=st.integers(
        min_value=0, max_value=2
    ),  # 0-2 invalid TD scorers
)
async def test_property_18_data_validation(
    db_session,
    game_exists,
    first_td_player_exists,
    num_valid_td_scorers,
    num_invalid_td_scorers,
):
    """
    Feature: scoring-system, Property 18: Data validation

    For any game data received from nflreadpy, if the game_id doesn't exist in
    the database or player_ids don't exist, the grading should be skipped and
    an error logged.

    Validates: Requirements 14.1, 14.2, 14.3, 14.4
    """
    from app.services.nfl_ingest import NFLIngestService, TouchdownData

    # Setup: Create service
    nfl_ingest_service = NFLIngestService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    db_session.add(home_team)
    await db_session.commit()

    # Setup: Conditionally create game in database
    game_external_id = f"2024_01_TEST_{uuid4().hex[:8]}"
    if game_exists:
        game = Game(
            id=uuid4(),
            external_id=game_external_id,
            home_team_id=home_team.id,
            away_team_id=home_team.id,
            kickoff_time=datetime.now(timezone.utc) + timedelta(hours=1),
            game_date=datetime.now(timezone.utc) + timedelta(hours=1),
            week_number=1,
            season_year=2024,
            game_type=GameType.SUNDAY_MAIN,
            status=GameStatus.SCHEDULED,
        )
        db_session.add(game)
        await db_session.commit()

    # Setup: Create valid TD scorers in database
    valid_td_scorers = []
    for i in range(num_valid_td_scorers):
        player = Player(
            id=uuid4(),
            external_id=f"valid_player_{i}_{uuid4().hex[:8]}",
            name=f"Valid Player {i}",
            team_id=home_team.id,
            position="RB",
            jersey_number=i + 1,
            is_active=True,
        )
        db_session.add(player)
        valid_td_scorers.append(player)
    await db_session.commit()

    # Setup: Create first TD scorer (conditionally exists in database)
    if first_td_player_exists and num_valid_td_scorers > 0:
        first_td_scorer_id = valid_td_scorers[0].external_id
        first_td_scorer_name = valid_td_scorers[0].name
    elif first_td_player_exists:
        # Create a separate first TD scorer
        first_td_player = Player(
            id=uuid4(),
            external_id=f"first_td_player_{uuid4().hex[:8]}",
            name="First TD Player",
            team_id=home_team.id,
            position="WR",
            jersey_number=99,
            is_active=True,
        )
        db_session.add(first_td_player)
        await db_session.commit()
        first_td_scorer_id = first_td_player.external_id
        first_td_scorer_name = first_td_player.name
    else:
        # First TD scorer does NOT exist in database
        first_td_scorer_id = f"nonexistent_player_{uuid4().hex[:8]}"
        first_td_scorer_name = "Nonexistent Player"

    # Setup: Build list of all TD scorers (mix of valid and invalid)
    all_td_scorer_ids = [p.external_id for p in valid_td_scorers]
    all_td_scorer_names = [p.name for p in valid_td_scorers]

    # Add invalid TD scorers (don't exist in database)
    for i in range(num_invalid_td_scorers):
        invalid_id = f"invalid_player_{i}_{uuid4().hex[:8]}"
        all_td_scorer_ids.append(invalid_id)
        all_td_scorer_names.append(f"Invalid Player {i}")

    # Setup: Create TouchdownData
    td_data = TouchdownData(
        game_id=game_external_id,
        first_td_scorer_id=first_td_scorer_id if first_td_scorer_id else None,
        first_td_scorer_name=first_td_scorer_name if first_td_scorer_name else None,
        all_td_scorer_ids=all_td_scorer_ids,
        all_td_scorer_names=all_td_scorer_names,
    )

    # Action: Validate game data
    is_valid, errors = await nfl_ingest_service.validate_game_data(
        game_external_id, td_data
    )

    # Assert: Verify data validation property
    # Requirement 14.1: Game must exist in database
    if not game_exists:
        assert not is_valid, (
            f"Expected validation to fail when game doesn't exist, "
            f"but validation passed"
        )
        assert len(errors) > 0, "Expected error messages when game doesn't exist"
        assert any(
            "Game not found" in error for error in errors
        ), "Expected 'Game not found' error message"
        return  # Stop here if game doesn't exist

    # Requirement 14.2: All player_ids must exist in database
    expected_errors = 0

    # Count expected errors for first TD scorer
    if first_td_scorer_id and not first_td_player_exists:
        expected_errors += 1

    # Count expected errors for invalid TD scorers
    expected_errors += num_invalid_td_scorers

    if expected_errors > 0:
        # Validation should fail if any players don't exist
        assert not is_valid, (
            f"Expected validation to fail when {expected_errors} player(s) don't exist, "
            f"but validation passed"
        )
        # Requirement 14.3: Validation errors should be logged
        assert len(errors) >= expected_errors, (
            f"Expected at least {expected_errors} error(s) for missing players, "
            f"but got {len(errors)}"
        )
    else:
        # Validation should pass if game and all players exist
        assert is_valid, (
            f"Expected validation to pass when game and all players exist, "
            f"but validation failed with errors: {errors}"
        )
        assert len(errors) == 0, (
            f"Expected no errors when validation passes, " f"but got {len(errors)}"
        )

    # Additional verification: Check error messages contain player information
    if not first_td_player_exists and first_td_scorer_id:
        assert any(
            first_td_scorer_id in error or "First TD scorer not found" in error
            for error in errors
        ), "Expected error message about first TD scorer not found"

    if num_invalid_td_scorers > 0:
        assert any(
            "TD scorer not found" in error for error in errors
        ), "Expected error message about TD scorer not found"


@pytest.mark.asyncio
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    num_picks=st.integers(min_value=1, max_value=5),  # 1-5 picks to grade
    num_td_scorers=st.integers(min_value=0, max_value=5),  # 0-5 TD scorers
    first_td_scorer_index=st.integers(
        min_value=-1, max_value=4
    ),  # -1 means no first TD
)
async def test_property_16_manual_scoring_equivalence(
    db_session,
    num_picks,
    num_td_scorers,
    first_td_scorer_index,
):
    """
    Feature: scoring-system, Property 16: Manual scoring equivalence

    For any game that is manually scored, the grading logic should produce the
    same results as automatic scoring given the same touchdown data.

    Validates: Requirements 9.1, 9.2
    """
    # Setup: Create service
    scoring_service = ScoringService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    away_team = Team(
        id=uuid4(),
        external_id=f"away_{uuid4().hex[:8]}",
        name="Away Team",
        abbreviation="AWY",
        city="Away City",
    )
    db_session.add(home_team)
    db_session.add(away_team)
    await db_session.commit()

    # Setup: Create TD scorer players
    td_scorer_players = []
    for i in range(max(num_td_scorers, 1)):  # At least 1 player
        player = Player(
            id=uuid4(),
            external_id=f"player_td_{i}_{uuid4().hex[:8]}",
            name=f"TD Scorer {i}",
            team_id=home_team.id,
            position="RB" if i % 2 == 0 else "WR",
            jersey_number=i + 1,
            is_active=True,
        )
        db_session.add(player)
        td_scorer_players.append(player)
    await db_session.commit()

    # Setup: Determine first TD scorer
    if first_td_scorer_index >= 0 and first_td_scorer_index < len(td_scorer_players):
        first_td_scorer = td_scorer_players[first_td_scorer_index].id
    else:
        first_td_scorer = None

    # Setup: Build list of all TD scorers
    all_td_scorers = [p.id for p in td_scorer_players[:num_td_scorers]]

    # Setup: Create two identical games for comparison
    game_auto = Game(
        id=uuid4(),
        external_id=f"game_auto_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        kickoff_time=datetime.now(timezone.utc) - timedelta(hours=3),
        game_date=datetime.now(timezone.utc) - timedelta(hours=3),
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.COMPLETED,
        first_td_scorer_player_id=first_td_scorer,
        all_td_scorer_player_ids=[str(scorer) for scorer in all_td_scorers],
    )
    game_manual = Game(
        id=uuid4(),
        external_id=f"game_manual_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        kickoff_time=datetime.now(timezone.utc) - timedelta(hours=3),
        game_date=datetime.now(timezone.utc) - timedelta(hours=3),
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.COMPLETED,
    )
    db_session.add(game_auto)
    db_session.add(game_manual)
    await db_session.commit()

    # Setup: Create admin user
    admin = User(
        id=uuid4(),
        email=f"admin_{uuid4().hex[:8]}@example.com",
        username=f"admin_{uuid4().hex[:8]}",
        display_name="Admin User",
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()

    # Setup: Create identical picks for both games
    pick_pairs = []  # List of (auto_pick, manual_pick) tuples
    for i in range(num_picks):
        user = User(
            id=uuid4(),
            email=f"user_{i}_{uuid4().hex[:8]}@example.com",
            username=f"user_{i}_{uuid4().hex[:8]}",
            display_name=f"User {i}",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        # Pick a random player from available TD scorers
        picked_player = td_scorer_players[i % len(td_scorer_players)]

        # Create pick for auto game
        pick_auto = Pick(
            id=uuid4(),
            user_id=user.id,
            game_id=game_auto.id,
            player_id=picked_player.id,
            status=PickResult.PENDING,
        )
        db_session.add(pick_auto)

        # Create identical pick for manual game
        pick_manual = Pick(
            id=uuid4(),
            user_id=user.id,
            game_id=game_manual.id,
            player_id=picked_player.id,
            status=PickResult.PENDING,
        )
        db_session.add(pick_manual)

        pick_pairs.append((pick_auto, pick_manual))
    await db_session.commit()

    # Action: Grade auto game using automatic scoring
    await scoring_service.grade_game(game_auto.id)

    # Action: Grade manual game using manual scoring with same TD data
    await scoring_service.manual_grade_game(
        game_manual.id, first_td_scorer, all_td_scorers, admin.id
    )

    # Assert: Verify manual scoring equivalence property
    # Both games should have same TD data
    await db_session.refresh(game_auto)
    await db_session.refresh(game_manual)

    assert (
        game_manual.first_td_scorer_player_id == game_auto.first_td_scorer_player_id
    ), (
        f"Manual game first TD scorer {game_manual.first_td_scorer_player_id} "
        f"should match auto game {game_auto.first_td_scorer_player_id}"
    )

    # Compare all TD scorers (convert to sets for comparison)
    auto_td_scorers = set(game_auto.all_td_scorer_player_ids or [])
    manual_td_scorers = set(game_manual.all_td_scorer_player_ids or [])
    assert manual_td_scorers == auto_td_scorers, (
        f"Manual game TD scorers {manual_td_scorers} "
        f"should match auto game {auto_td_scorers}"
    )

    # Verify manual game is marked as manually scored
    assert (
        game_manual.is_manually_scored is True
    ), "Manual game should be marked as manually scored"

    # Compare pick results for each pair
    for pick_auto, pick_manual in pick_pairs:
        await db_session.refresh(pick_auto)
        await db_session.refresh(pick_manual)

        # Status should be the same
        assert pick_manual.status == pick_auto.status, (
            f"Manual pick status {pick_manual.status} should match "
            f"auto pick status {pick_auto.status}"
        )

        # FTD points should be the same
        assert pick_manual.ftd_points == pick_auto.ftd_points, (
            f"Manual pick FTD points {pick_manual.ftd_points} should match "
            f"auto pick FTD points {pick_auto.ftd_points}"
        )

        # ATTD points should be the same
        assert pick_manual.attd_points == pick_auto.attd_points, (
            f"Manual pick ATTD points {pick_manual.attd_points} should match "
            f"auto pick ATTD points {pick_auto.attd_points}"
        )

        # Total points should be the same
        assert pick_manual.total_points == pick_auto.total_points, (
            f"Manual pick total points {pick_manual.total_points} should match "
            f"auto pick total points {pick_auto.total_points}"
        )

        # Both picks should have scored_at timestamp
        assert (
            pick_manual.scored_at is not None
        ), "Manual pick should have scored_at timestamp"
        assert (
            pick_auto.scored_at is not None
        ), "Auto pick should have scored_at timestamp"

    # Verify user scores are updated correctly for both games
    for pick_auto, pick_manual in pick_pairs:
        await db_session.refresh(pick_auto)
        await db_session.refresh(pick_manual)

        # Get user
        result = await db_session.execute(
            select(User).where(User.id == pick_auto.user_id)
        )
        user = result.scalar_one()

        # User should have points from both picks
        expected_total = pick_auto.total_points + pick_manual.total_points
        assert (
            user.total_score >= expected_total
        ), f"User total score {user.total_score} should be at least {expected_total}"


@pytest.mark.asyncio
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    old_status=st.sampled_from([PickResult.WIN, PickResult.LOSS, PickResult.PENDING]),
    new_status=st.sampled_from([PickResult.WIN, PickResult.LOSS, PickResult.VOID]),
    old_ftd_points=st.sampled_from([0, 3]),
    old_attd_points=st.sampled_from([0, 1]),
    new_ftd_points=st.sampled_from([0, 3]),
    new_attd_points=st.sampled_from([0, 1]),
)
async def test_property_17_override_audit_trail(
    db_session,
    old_status,
    new_status,
    old_ftd_points,
    old_attd_points,
    new_ftd_points,
    new_attd_points,
):
    """
    Feature: scoring-system, Property 17: Override audit trail

    For any pick that is overridden by an admin, is_manual_override should be true,
    override_by_user_id should be set, and override_at should be recent.

    Validates: Requirements 10.3, 10.4
    """
    # Setup: Create service
    scoring_service = ScoringService(db_session)

    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id=f"home_{uuid4().hex[:8]}",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    db_session.add(home_team)
    await db_session.commit()

    # Setup: Create game
    game = Game(
        id=uuid4(),
        external_id=f"game_{uuid4().hex[:8]}",
        home_team_id=home_team.id,
        away_team_id=home_team.id,
        kickoff_time=datetime.now(timezone.utc) - timedelta(hours=3),
        game_date=datetime.now(timezone.utc) - timedelta(hours=3),
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.COMPLETED,
    )
    db_session.add(game)
    await db_session.commit()

    # Setup: Create player
    player = Player(
        id=uuid4(),
        external_id=f"player_{uuid4().hex[:8]}",
        name="Player",
        team_id=home_team.id,
        position="RB",
        jersey_number=1,
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

    # Setup: Create admin user
    admin = User(
        id=uuid4(),
        email=f"admin_{uuid4().hex[:8]}@example.com",
        username=f"admin_{uuid4().hex[:8]}",
        display_name="Admin User",
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()

    # Setup: Create pick with old values
    pick = Pick(
        id=uuid4(),
        user_id=user.id,
        game_id=game.id,
        player_id=player.id,
        status=old_status,
        ftd_points=old_ftd_points,
        attd_points=old_attd_points,
        total_points=old_ftd_points + old_attd_points,
    )
    db_session.add(pick)
    await db_session.commit()

    # Update user scores based on old pick status
    if old_status == PickResult.WIN:
        user.total_score = old_ftd_points + old_attd_points
        user.total_wins = 1
    elif old_status == PickResult.LOSS:
        user.total_losses = 1
    await db_session.commit()

    # Verify pick starts without override
    assert pick.is_manual_override is False, "Pick should start without override"
    assert (
        pick.override_by_user_id is None
    ), "Pick should start without override_by_user_id"
    assert pick.override_at is None, "Pick should start without override_at"

    # Record time before override
    time_before_override = datetime.now(timezone.utc)

    # Action: Override the pick score
    updated_pick = await scoring_service.override_pick_score(
        pick.id, new_status, new_ftd_points, new_attd_points, admin.id
    )

    # Record time after override
    time_after_override = datetime.now(timezone.utc)

    # Assert: Verify override audit trail property
    assert updated_pick is not None, "Override should return updated pick"

    # Requirement 10.3: is_manual_override should be true
    assert (
        updated_pick.is_manual_override is True
    ), "Pick should be marked as manually overridden"

    # Requirement 10.4: override_by_user_id should be set to admin
    assert updated_pick.override_by_user_id == admin.id, (
        f"Pick override_by_user_id should be {admin.id}, "
        f"but got {updated_pick.override_by_user_id}"
    )

    # Requirement 10.4: override_at should be recent
    assert (
        updated_pick.override_at is not None
    ), "Pick should have override_at timestamp"
    assert time_before_override <= updated_pick.override_at <= time_after_override, (
        f"Pick override_at timestamp {updated_pick.override_at} should be between "
        f"{time_before_override} and {time_after_override}"
    )

    # Additional verification: Verify pick values are updated
    assert (
        updated_pick.status == new_status
    ), f"Pick status should be {new_status}, but got {updated_pick.status}"
    assert (
        updated_pick.ftd_points == new_ftd_points
    ), f"Pick ftd_points should be {new_ftd_points}, but got {updated_pick.ftd_points}"
    assert (
        updated_pick.attd_points == new_attd_points
    ), f"Pick attd_points should be {new_attd_points}, but got {updated_pick.attd_points}"
    assert updated_pick.total_points == new_ftd_points + new_attd_points, (
        f"Pick total_points should be {new_ftd_points + new_attd_points}, "
        f"but got {updated_pick.total_points}"
    )

    # Additional verification: Verify user score is recalculated
    await db_session.refresh(user)

    # Calculate expected user score based on status changes
    expected_score = 0
    expected_wins = 0
    expected_losses = 0

    if new_status == PickResult.WIN:
        expected_score = new_ftd_points + new_attd_points
        expected_wins = 1
    elif new_status == PickResult.LOSS:
        expected_losses = 1

    assert (
        user.total_score == expected_score
    ), f"User total_score should be {expected_score}, but got {user.total_score}"
    assert (
        user.total_wins == expected_wins
    ), f"User total_wins should be {expected_wins}, but got {user.total_wins}"
    assert (
        user.total_losses == expected_losses
    ), f"User total_losses should be {expected_losses}, but got {user.total_losses}"
