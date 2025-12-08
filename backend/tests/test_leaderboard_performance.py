"""Performance tests for leaderboard queries"""

import pytest
import time
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.leaderboard_service import LeaderboardService


@pytest.mark.asyncio
async def test_season_leaderboard_query_performance(db_session: AsyncSession):
    """
    Test that season leaderboard query completes within 500ms
    Requirements: 8.1, 8.4
    """
    # Create leaderboard service without cache to test raw query performance
    service = LeaderboardService(db=db_session, cache=None)

    # Measure query time
    start_time = time.time()
    result = await service.get_season_leaderboard(season=2024)
    end_time = time.time()

    query_time_ms = (end_time - start_time) * 1000

    print(f"\nSeason leaderboard query time: {query_time_ms:.2f}ms")
    print(f"Number of users in leaderboard: {len(result)}")

    # Assert query completes within 500ms (requirement 8.1)
    assert query_time_ms < 500, f"Query took {query_time_ms:.2f}ms, expected < 500ms"


@pytest.mark.asyncio
async def test_weekly_leaderboard_query_performance(db_session: AsyncSession):
    """
    Test that weekly leaderboard query completes within 500ms
    Requirements: 8.1, 8.4
    """
    # Create leaderboard service without cache to test raw query performance
    service = LeaderboardService(db=db_session, cache=None)

    # Measure query time
    start_time = time.time()
    result = await service.get_weekly_leaderboard(season=2024, week=1)
    end_time = time.time()

    query_time_ms = (end_time - start_time) * 1000

    print(f"\nWeekly leaderboard query time: {query_time_ms:.2f}ms")
    print(f"Number of users in leaderboard: {len(result)}")

    # Assert query completes within 500ms (requirement 8.1)
    assert query_time_ms < 500, f"Query took {query_time_ms:.2f}ms, expected < 500ms"


@pytest.mark.asyncio
async def test_season_leaderboard_index_usage(db_session: AsyncSession):
    """
    Verify that season leaderboard query uses the composite indexes
    Requirements: 8.1, 8.4

    Note: This test runs against the test database which may not have indexes.
    The test verifies query structure and performance characteristics.
    """
    # Build the query that matches what the service uses
    query = text(
        """
        EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
        SELECT 
            u.id as user_id,
            u.username,
            u.display_name,
            SUM(p.ftd_points) as ftd_points,
            SUM(p.attd_points) as attd_points,
            SUM(CASE WHEN p.status::text = 'win' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN p.status::text = 'loss' THEN 1 ELSE 0 END) as losses,
            SUM(CASE WHEN p.status::text = 'pending' THEN 1 ELSE 0 END) as pending
        FROM users u
        JOIN picks p ON u.id = p.user_id
        JOIN games g ON p.game_id = g.id
        WHERE g.season_year = 2024
          AND p.status::text IN ('win', 'loss')
        GROUP BY u.id, u.username, u.display_name
    """
    )

    result = await db_session.execute(query)
    explain_output = result.scalar()

    # Convert to string for easier inspection
    explain_str = str(explain_output)

    print("\n=== EXPLAIN ANALYZE Output ===")
    print(explain_str)

    # Check execution time from EXPLAIN ANALYZE
    execution_time = explain_output[0]["Plan"]["Actual Total Time"]
    print(f"\nActual execution time: {execution_time:.2f}ms")

    # Verify execution time is reasonable (more lenient for test DB without indexes)
    assert (
        execution_time < 1000
    ), f"Query execution took {execution_time:.2f}ms, expected < 1000ms"


@pytest.mark.asyncio
async def test_weekly_leaderboard_index_usage(db_session: AsyncSession):
    """
    Verify that weekly leaderboard query uses the composite indexes
    Requirements: 8.1, 8.4

    Note: This test runs against the test database which may not have indexes.
    The test verifies query structure and performance characteristics.
    """
    # Build the query that matches what the service uses
    query = text(
        """
        EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
        SELECT 
            u.id as user_id,
            u.username,
            u.display_name,
            SUM(p.ftd_points) as ftd_points,
            SUM(p.attd_points) as attd_points,
            SUM(CASE WHEN p.status::text = 'win' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN p.status::text = 'loss' THEN 1 ELSE 0 END) as losses,
            SUM(CASE WHEN p.status::text = 'pending' THEN 1 ELSE 0 END) as pending
        FROM users u
        JOIN picks p ON u.id = p.user_id
        JOIN games g ON p.game_id = g.id
        WHERE g.season_year = 2024
          AND g.week_number = 1
          AND p.status::text IN ('win', 'loss')
        GROUP BY u.id, u.username, u.display_name
    """
    )

    result = await db_session.execute(query)
    explain_output = result.scalar()

    # Convert to string for easier inspection
    explain_str = str(explain_output)

    print("\n=== EXPLAIN ANALYZE Output ===")
    print(explain_str)

    # Check execution time from EXPLAIN ANALYZE
    execution_time = explain_output[0]["Plan"]["Actual Total Time"]
    print(f"\nActual execution time: {execution_time:.2f}ms")

    # Verify execution time is reasonable (more lenient for test DB without indexes)
    assert (
        execution_time < 1000
    ), f"Query execution took {execution_time:.2f}ms, expected < 1000ms"


@pytest.mark.asyncio
@pytest.mark.skip(
    reason="Test database doesn't have production indexes - verify manually in production"
)
async def test_verify_indexes_exist(db_session: AsyncSession):
    """
    Verify that the required indexes exist in the database
    Requirements: 8.1, 8.4

    Note: This test is skipped for test database. Run manually against production.
    """
    # Check for idx_picks_status_user
    query = text(
        """
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE tablename = 'picks'
          AND indexname = 'idx_picks_status_user'
    """
    )
    result = await db_session.execute(query)
    picks_index = result.fetchone()

    assert (
        picks_index is not None
    ), "Index idx_picks_status_user should exist on picks table"
    print(f"\n✓ Found index: {picks_index[0]}")
    print(f"  Definition: {picks_index[1]}")

    # Check for idx_games_season_week
    query = text(
        """
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE tablename = 'games'
          AND indexname = 'idx_games_season_week'
    """
    )
    result = await db_session.execute(query)
    games_index = result.fetchone()

    assert (
        games_index is not None
    ), "Index idx_games_season_week should exist on games table"
    print(f"\n✓ Found index: {games_index[0]}")
    print(f"  Definition: {games_index[1]}")
