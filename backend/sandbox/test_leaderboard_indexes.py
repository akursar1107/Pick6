"""
Script to test leaderboard query performance and index usage on production database.
Run with: docker compose exec api python sandbox/test_leaderboard_indexes.py
"""

import asyncio
import asyncpg
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings


async def test_season_query():
    """Test season leaderboard query performance"""
    # Parse the database URL
    db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    # Connect to database
    conn = await asyncpg.connect(db_url)

    try:
        print("\n" + "=" * 80)
        print("SEASON LEADERBOARD QUERY PERFORMANCE TEST")
        print("=" * 80)

        # Run EXPLAIN ANALYZE
        query = """
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

        result = await conn.fetchval(query)
        explain_data = json.loads(result)

        # Extract key metrics
        plan = explain_data[0]
        execution_time = plan["Execution Time"]
        planning_time = plan["Planning Time"]
        total_time = execution_time + planning_time

        print(f"\n📊 Performance Metrics:")
        print(f"   Planning Time: {planning_time:.2f}ms")
        print(f"   Execution Time: {execution_time:.2f}ms")
        print(f"   Total Time: {total_time:.2f}ms")

        # Check if indexes are being used
        plan_str = json.dumps(plan, indent=2)

        print(f"\n🔍 Index Usage:")
        if "idx_games_season_week" in plan_str:
            print("   ✓ idx_games_season_week is being used")
        else:
            print("   ✗ idx_games_season_week is NOT being used")

        if "idx_picks_status_user" in plan_str:
            print("   ✓ idx_picks_status_user is being used")
        else:
            print("   ✗ idx_picks_status_user is NOT being used")

        # Check for sequential scans (bad for performance)
        if "Seq Scan" in plan_str:
            print("   ⚠️  Sequential scans detected (may impact performance)")

        # Performance assessment
        print(f"\n✅ Performance Assessment:")
        if total_time < 500:
            print(
                f"   EXCELLENT: Query completed in {total_time:.2f}ms (< 500ms target)"
            )
        elif total_time < 1000:
            print(f"   GOOD: Query completed in {total_time:.2f}ms (< 1000ms)")
        else:
            print(f"   NEEDS OPTIMIZATION: Query took {total_time:.2f}ms (> 1000ms)")

        print(f"\n📝 Full Explain Plan:")
        print(json.dumps(plan, indent=2))

    finally:
        await conn.close()


async def test_weekly_query():
    """Test weekly leaderboard query performance"""
    # Parse the database URL
    db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    # Connect to database
    conn = await asyncpg.connect(db_url)

    try:
        print("\n" + "=" * 80)
        print("WEEKLY LEADERBOARD QUERY PERFORMANCE TEST")
        print("=" * 80)

        # Run EXPLAIN ANALYZE
        query = """
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

        result = await conn.fetchval(query)
        explain_data = json.loads(result)

        # Extract key metrics
        plan = explain_data[0]
        execution_time = plan["Execution Time"]
        planning_time = plan["Planning Time"]
        total_time = execution_time + planning_time

        print(f"\n📊 Performance Metrics:")
        print(f"   Planning Time: {planning_time:.2f}ms")
        print(f"   Execution Time: {execution_time:.2f}ms")
        print(f"   Total Time: {total_time:.2f}ms")

        # Check if indexes are being used
        plan_str = json.dumps(plan, indent=2)

        print(f"\n🔍 Index Usage:")
        if "idx_games_season_week" in plan_str:
            print("   ✓ idx_games_season_week is being used")
        else:
            print("   ✗ idx_games_season_week is NOT being used")

        if "idx_picks_status_user" in plan_str:
            print("   ✓ idx_picks_status_user is being used")
        else:
            print("   ✗ idx_picks_status_user is NOT being used")

        # Check for sequential scans (bad for performance)
        if "Seq Scan" in plan_str:
            print("   ⚠️  Sequential scans detected (may impact performance)")

        # Performance assessment
        print(f"\n✅ Performance Assessment:")
        if total_time < 500:
            print(
                f"   EXCELLENT: Query completed in {total_time:.2f}ms (< 500ms target)"
            )
        elif total_time < 1000:
            print(f"   GOOD: Query completed in {total_time:.2f}ms (< 1000ms)")
        else:
            print(f"   NEEDS OPTIMIZATION: Query took {total_time:.2f}ms (> 1000ms)")

        print(f"\n📝 Full Explain Plan:")
        print(json.dumps(plan, indent=2))

    finally:
        await conn.close()


async def verify_indexes():
    """Verify that indexes exist"""
    # Parse the database URL
    db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    # Connect to database
    conn = await asyncpg.connect(db_url)

    try:
        print("\n" + "=" * 80)
        print("INDEX VERIFICATION")
        print("=" * 80)

        # Check for indexes
        query = """
            SELECT 
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE tablename IN ('picks', 'games')
              AND indexname IN ('idx_picks_status_user', 'idx_games_season_week')
            ORDER BY tablename, indexname
        """

        rows = await conn.fetch(query)

        if len(rows) == 2:
            print("\n✅ All required indexes exist:")
            for row in rows:
                print(f"\n   Table: {row['tablename']}")
                print(f"   Index: {row['indexname']}")
                print(f"   Definition: {row['indexdef']}")
        else:
            print(f"\n❌ Missing indexes! Found {len(rows)}/2 expected indexes")
            for row in rows:
                print(f"   - {row['indexname']} on {row['tablename']}")

    finally:
        await conn.close()


async def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("LEADERBOARD INDEX AND PERFORMANCE TEST")
    print("=" * 80)

    # Verify indexes exist
    await verify_indexes()

    # Test season query
    await test_season_query()

    # Test weekly query
    await test_weekly_query()

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
