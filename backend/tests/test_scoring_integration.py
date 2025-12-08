"""Integration tests for Scoring System

These tests verify the complete end-to-end scoring flow including:
- Complete scoring flow from game completion to user score updates
- Scheduled job execution
- Manual scoring workflow
- Override workflow
"""

import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from sqlalchemy import select

from app.services.scoring import ScoringService
from app.services.nfl_ingest import NFLIngestService
from app.db.models.pick import Pick, PickResult
from app.db.models.game import Game, GameStatus, GameType
from app.db.models.team import Team
from app.db.models.player import Player
from app.db.models.user import User


@pytest.mark.asyncio
async def test_complete_scoring_flow_end_to_end(db_session):
    """
    Test complete scoring flow from game completion to user score updates.

    This test verifies:
    1. Game is created with pending picks
    2. Game completes with touchdown data
    3. Scoring service grades all picks
    4. User scores are updated correctly
    5. Pick statuses are updated
    """
    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id="home_team_integration",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    away_team = Team(
        id=uuid4(),
        external_id="away_team_integration",
        name="Away Team",
        abbreviation="AWY",
        city="Away City",
    )
    db_session.add(home_team)
    db_session.add(away_team)
    await db_session.commit()

    # Setup: Create players
    ftd_scorer = Player(
        id=uuid4(),
        external_id="ftd_scorer",
        name="FTD Scorer",
        team_id=home_team.id,
        position="RB",
        jersey_number=1,
        is_active=True,
    )
    attd_scorer = Player(
        id=uuid4(),
        external_id="attd_scorer",
        name="ATTD Scorer",
        team_id=home_team.id,
        position="WR",
        jersey_number=2,
        is_active=True,
    )
    non_scorer = Player(
        id=uuid4(),
        external_id="non_scorer",
        name="Non Scorer",
        team_id=away_team.id,
        position="TE",
        jersey_number=3,
        is_active=True,
    )
    db_session.add(ftd_scorer)
    db_session.add(attd_scorer)
    db_session.add(non_scorer)
    await db_session.commit()

    # Setup: Create game (initially scheduled)
    game = Game(
        id=uuid4(),
        external_id="integration_game_1",
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        kickoff_time=datetime.now(timezone.utc) - timedelta(hours=3),
        game_date=datetime.now(timezone.utc) - timedelta(hours=3),
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.SCHEDULED,
    )
    db_session.add(game)
    await db_session.commit()

    # Setup: Create users with picks
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

    # Setup: Create picks
    # User 1 picks FTD scorer (should get 4 points: 3 FTD + 1 ATTD)
    pick1 = Pick(
        id=uuid4(),
        user_id=user1.id,
        game_id=game.id,
        player_id=ftd_scorer.id,
        status=PickResult.PENDING,
    )
    # User 2 picks ATTD scorer (should get 1 point: 1 ATTD)
    pick2 = Pick(
        id=uuid4(),
        user_id=user2.id,
        game_id=game.id,
        player_id=attd_scorer.id,
        status=PickResult.PENDING,
    )
    # User 3 picks non-scorer (should get 0 points, loss)
    pick3 = Pick(
        id=uuid4(),
        user_id=user3.id,
        game_id=game.id,
        player_id=non_scorer.id,
        status=PickResult.PENDING,
    )
    db_session.add(pick1)
    db_session.add(pick2)
    db_session.add(pick3)
    await db_session.commit()

    # Action: Simulate game completion with touchdown data
    game.status = GameStatus.COMPLETED
    game.first_td_scorer_player_id = ftd_scorer.id
    game.all_td_scorer_player_ids = [str(ftd_scorer.id), str(attd_scorer.id)]
    await db_session.commit()

    # Action: Grade the game
    scoring_service = ScoringService(db_session)
    graded_count = await scoring_service.grade_game(game.id)

    # Assert: Verify grading results
    assert graded_count == 3, f"Expected 3 picks graded, got {graded_count}"

    # Refresh all entities
    await db_session.refresh(pick1)
    await db_session.refresh(pick2)
    await db_session.refresh(pick3)
    await db_session.refresh(user1)
    await db_session.refresh(user2)
    await db_session.refresh(user3)
    await db_session.refresh(game)

    # Assert: Verify pick 1 (FTD scorer)
    assert pick1.status == PickResult.WIN
    assert pick1.ftd_points == 3
    assert pick1.attd_points == 1
    assert pick1.total_points == 4
    assert pick1.scored_at is not None

    # Assert: Verify pick 2 (ATTD scorer)
    assert pick2.status == PickResult.WIN
    assert pick2.ftd_points == 0
    assert pick2.attd_points == 1
    assert pick2.total_points == 1
    assert pick2.scored_at is not None

    # Assert: Verify pick 3 (non-scorer)
    assert pick3.status == PickResult.LOSS
    assert pick3.ftd_points == 0
    assert pick3.attd_points == 0
    assert pick3.total_points == 0
    assert pick3.scored_at is not None

    # Assert: Verify user scores
    assert user1.total_score == 4
    assert user1.total_wins == 1
    assert user1.total_losses == 0

    assert user2.total_score == 1
    assert user2.total_wins == 1
    assert user2.total_losses == 0

    assert user3.total_score == 0
    assert user3.total_wins == 0
    assert user3.total_losses == 1

    # Assert: Verify game is marked as scored
    assert game.scored_at is not None


@pytest.mark.asyncio
async def test_manual_scoring_workflow(db_session):
    """
    Test manual scoring workflow for admin override.

    This test verifies:
    1. Admin can manually score a game
    2. Manual scoring uses same logic as automatic
    3. Game is marked as manually scored
    """
    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id="home_team_manual",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    db_session.add(home_team)
    await db_session.commit()

    # Setup: Create players
    player1 = Player(
        id=uuid4(),
        external_id="player1_manual",
        name="Player 1",
        team_id=home_team.id,
        position="RB",
        jersey_number=1,
        is_active=True,
    )
    player2 = Player(
        id=uuid4(),
        external_id="player2_manual",
        name="Player 2",
        team_id=home_team.id,
        position="WR",
        jersey_number=2,
        is_active=True,
    )
    db_session.add(player1)
    db_session.add(player2)
    await db_session.commit()

    # Setup: Create game
    game = Game(
        id=uuid4(),
        external_id="manual_game_1",
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

    # Setup: Create user and pick
    user = User(
        id=uuid4(),
        email="user_manual@test.com",
        username="user_manual",
        display_name="Manual User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    pick = Pick(
        id=uuid4(),
        user_id=user.id,
        game_id=game.id,
        player_id=player1.id,
        status=PickResult.PENDING,
    )
    db_session.add(pick)
    await db_session.commit()

    # Setup: Create admin user
    admin = User(
        id=uuid4(),
        email="admin@test.com",
        username="admin",
        display_name="Admin",
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()

    # Action: Manually score the game
    scoring_service = ScoringService(db_session)
    result = await scoring_service.manual_grade_game(
        game.id,
        first_td_scorer=player1.id,
        all_td_scorers=[player1.id, player2.id],
        admin_id=admin.id,
    )

    # Refresh entities
    await db_session.refresh(pick)
    await db_session.refresh(game)
    await db_session.refresh(user)

    # Assert: Verify manual scoring results
    assert result is not None
    assert result == 1  # manual_grade_game returns the count directly

    # Assert: Verify pick was graded correctly
    assert pick.status == PickResult.WIN
    assert pick.ftd_points == 3
    assert pick.attd_points == 1
    assert pick.total_points == 4

    # Assert: Verify game is marked as manually scored
    assert game.is_manually_scored is True
    assert game.scored_at is not None

    # Assert: Verify user score updated
    assert user.total_score == 4
    assert user.total_wins == 1


@pytest.mark.asyncio
async def test_override_workflow(db_session):
    """
    Test pick score override workflow.

    This test verifies:
    1. Admin can override a pick's score
    2. User score is recalculated
    3. Audit trail is recorded
    """
    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id="home_team_override",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    db_session.add(home_team)
    await db_session.commit()

    # Setup: Create player
    player = Player(
        id=uuid4(),
        external_id="player_override",
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
        external_id="override_game_1",
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

    # Setup: Create user with a graded pick (initially loss)
    user = User(
        id=uuid4(),
        email="user_override@test.com",
        username="user_override",
        display_name="Override User",
        is_active=True,
        total_score=0,
        total_wins=0,
        total_losses=1,
    )
    db_session.add(user)
    await db_session.commit()

    pick = Pick(
        id=uuid4(),
        user_id=user.id,
        game_id=game.id,
        player_id=player.id,
        status=PickResult.LOSS,
        ftd_points=0,
        attd_points=0,
        total_points=0,
        scored_at=datetime.now(timezone.utc),
    )
    db_session.add(pick)
    await db_session.commit()

    # Setup: Create admin user
    admin = User(
        id=uuid4(),
        email="admin_override@test.com",
        username="admin_override",
        display_name="Admin Override",
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()

    # Action: Override the pick score (change from loss to win with 4 points)
    scoring_service = ScoringService(db_session)
    updated_pick = await scoring_service.override_pick_score(
        pick.id,
        status=PickResult.WIN,
        ftd_points=3,
        attd_points=1,
        admin_id=admin.id,
    )

    # Refresh entities
    await db_session.refresh(user)

    # Assert: Verify override results
    assert updated_pick is not None
    assert updated_pick.status == PickResult.WIN
    assert updated_pick.ftd_points == 3
    assert updated_pick.attd_points == 1
    assert updated_pick.total_points == 4

    # Assert: Verify audit trail
    assert updated_pick.is_manual_override is True
    assert updated_pick.override_by_user_id == admin.id
    assert updated_pick.override_at is not None

    # Assert: Verify user score recalculated
    assert user.total_score == 4
    assert user.total_wins == 1
    assert user.total_losses == 0


@pytest.mark.asyncio
async def test_zero_touchdown_game_integration(db_session):
    """
    Test integration for games with zero touchdowns.

    This test verifies:
    1. All picks are marked as losses
    2. No points are awarded
    3. User scores remain at 0
    """
    # Setup: Create teams
    home_team = Team(
        id=uuid4(),
        external_id="home_team_zero_td",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )
    db_session.add(home_team)
    await db_session.commit()

    # Setup: Create player
    player = Player(
        id=uuid4(),
        external_id="player_zero_td",
        name="Player",
        team_id=home_team.id,
        position="RB",
        jersey_number=1,
        is_active=True,
    )
    db_session.add(player)
    await db_session.commit()

    # Setup: Create game with zero touchdowns
    game = Game(
        id=uuid4(),
        external_id="zero_td_game",
        home_team_id=home_team.id,
        away_team_id=home_team.id,
        kickoff_time=datetime.now(timezone.utc) - timedelta(hours=3),
        game_date=datetime.now(timezone.utc) - timedelta(hours=3),
        week_number=1,
        season_year=2024,
        game_type=GameType.SUNDAY_MAIN,
        status=GameStatus.COMPLETED,
        first_td_scorer_player_id=None,  # No first TD
        all_td_scorer_player_ids=[],  # No TDs at all
    )
    db_session.add(game)
    await db_session.commit()

    # Setup: Create users with picks
    users = []
    picks = []
    for i in range(3):
        user = User(
            id=uuid4(),
            email=f"user{i}@zero_td.com",
            username=f"user{i}_zero_td",
            display_name=f"User {i}",
            is_active=True,
        )
        db_session.add(user)
        users.append(user)

    await db_session.commit()

    for user in users:
        pick = Pick(
            id=uuid4(),
            user_id=user.id,
            game_id=game.id,
            player_id=player.id,
            status=PickResult.PENDING,
        )
        db_session.add(pick)
        picks.append(pick)

    await db_session.commit()

    # Action: Grade the game
    scoring_service = ScoringService(db_session)
    graded_count = await scoring_service.grade_game(game.id)

    # Assert: Verify all picks graded
    assert graded_count == 3

    # Refresh entities
    for pick in picks:
        await db_session.refresh(pick)
    for user in users:
        await db_session.refresh(user)

    # Assert: Verify all picks are losses with 0 points
    for pick in picks:
        assert pick.status == PickResult.LOSS
        assert pick.ftd_points == 0
        assert pick.attd_points == 0
        assert pick.total_points == 0
        assert pick.scored_at is not None

    # Assert: Verify all users have 0 score
    for user in users:
        assert user.total_score == 0
        assert user.total_wins == 0
        assert user.total_losses == 1
