"""Unit tests for Leaderboard service"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from app.services.leaderboard_service import LeaderboardService
from app.db.models.pick import Pick, PickResult
from app.db.models.user import User


@pytest.mark.asyncio
async def test_empty_week_scenario(db_session):
    """
    Test that empty week returns empty leaderboard

    Validates: Requirements 2.3, 9.2
    """
    from app.db.models.game import Game, GameStatus, GameType
    from app.db.models.team import Team

    # Setup: Create service
    leaderboard_service = LeaderboardService(db_session)

    # Create teams
    home_team = Team(
        id=uuid4(),
        external_id="team_home_empty",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    away_team = Team(
        id=uuid4(),
        external_id="team_away_empty",
        name="Away Team",
        abbreviation="AWY",
        city="Away City",
    )
    db_session.add(home_team)
    db_session.add(away_team)
    await db_session.commit()

    # Create a game for week 1 but with no graded picks
    game = Game(
        id=uuid4(),
        external_id="game_empty_week",
        season_year=2024,
        week_number=1,
        game_type=GameType.SUNDAY_MAIN,
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        game_date=datetime(2024, 9, 1, 13, 0, tzinfo=timezone.utc),
        kickoff_time=datetime(2024, 9, 1, 13, 0, tzinfo=timezone.utc),
        status=GameStatus.SCHEDULED,  # Not completed yet
    )
    db_session.add(game)
    await db_session.commit()

    # Action: Get weekly leaderboard for week with no graded picks
    leaderboard = await leaderboard_service.get_weekly_leaderboard(2024, 1)

    # Assert: Should return empty list
    assert leaderboard == [], "Empty week should return empty leaderboard"

    # Test week with no games at all
    leaderboard_no_games = await leaderboard_service.get_weekly_leaderboard(2024, 18)
    assert (
        leaderboard_no_games == []
    ), "Week with no games should return empty leaderboard"


@pytest.mark.asyncio
async def test_ranking_order_correctness(db_session):
    """
    Test that rankings are in descending order by total points

    Validates: Requirements 1.1
    """
    # Setup: Create service
    leaderboard_service = LeaderboardService(db_session)

    # Create users
    user1 = User(
        id=uuid4(),
        email="user1@test.com",
        username="user1",
        display_name="User 1",
        is_active=True,
    )
    user2 = User(
        id=uuid4(),
        email="user2@test.com",
        username="user2",
        display_name="User 2",
        is_active=True,
    )
    user3 = User(
        id=uuid4(),
        email="user3@test.com",
        username="user3",
        display_name="User 3",
        is_active=True,
    )
    db_session.add(user1)
    db_session.add(user2)
    db_session.add(user3)
    await db_session.commit()

    # Create picks with different point totals
    # User 1: 9 points (3 FTD wins)
    # User 2: 6 points (2 FTD wins)
    # User 3: 3 points (1 FTD win)
    picks = [
        # User 1 picks
        Pick(
            id=uuid4(),
            user_id=user1.id,
            game_id=uuid4(),
            player_id=uuid4(),
            status=PickResult.WIN,
            ftd_points=3,
            attd_points=0,
            total_points=3,
            scored_at=datetime.now(timezone.utc),
        ),
        Pick(
            id=uuid4(),
            user_id=user1.id,
            game_id=uuid4(),
            player_id=uuid4(),
            status=PickResult.WIN,
            ftd_points=3,
            attd_points=0,
            total_points=3,
            scored_at=datetime.now(timezone.utc),
        ),
        Pick(
            id=uuid4(),
            user_id=user1.id,
            game_id=uuid4(),
            player_id=uuid4(),
            status=PickResult.WIN,
            ftd_points=3,
            attd_points=0,
            total_points=3,
            scored_at=datetime.now(timezone.utc),
        ),
        # User 2 picks
        Pick(
            id=uuid4(),
            user_id=user2.id,
            game_id=uuid4(),
            player_id=uuid4(),
            status=PickResult.WIN,
            ftd_points=3,
            attd_points=0,
            total_points=3,
            scored_at=datetime.now(timezone.utc),
        ),
        Pick(
            id=uuid4(),
            user_id=user2.id,
            game_id=uuid4(),
            player_id=uuid4(),
            status=PickResult.WIN,
            ftd_points=3,
            attd_points=0,
            total_points=3,
            scored_at=datetime.now(timezone.utc),
        ),
        # User 3 picks
        Pick(
            id=uuid4(),
            user_id=user3.id,
            game_id=uuid4(),
            player_id=uuid4(),
            status=PickResult.WIN,
            ftd_points=3,
            attd_points=0,
            total_points=3,
            scored_at=datetime.now(timezone.utc),
        ),
    ]

    # Action: Calculate rankings
    leaderboard = await leaderboard_service.calculate_rankings(picks)

    # Assert: Verify ranking order
    assert len(leaderboard) == 3

    # User 1 should be rank 1 with 9 points
    assert leaderboard[0].rank == 1
    assert leaderboard[0].user_id == user1.id
    assert leaderboard[0].total_points == 9
    assert leaderboard[0].wins == 3

    # User 2 should be rank 2 with 6 points
    assert leaderboard[1].rank == 2
    assert leaderboard[1].user_id == user2.id
    assert leaderboard[1].total_points == 6
    assert leaderboard[1].wins == 2

    # User 3 should be rank 3 with 3 points
    assert leaderboard[2].rank == 3
    assert leaderboard[2].user_id == user3.id
    assert leaderboard[2].total_points == 3
    assert leaderboard[2].wins == 1

    # Verify descending order
    for i in range(len(leaderboard) - 1):
        assert leaderboard[i].total_points >= leaderboard[i + 1].total_points
