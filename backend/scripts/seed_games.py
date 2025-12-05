"""Seed sample NFL games for current/upcoming week"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from app.db.models.team import Team
from app.db.models.game import Game, GameStatus, GameType

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@db:5432/first6"


def get_next_thursday():
    """Get the next Thursday from today"""
    today = datetime.now(timezone.utc)
    days_ahead = 3 - today.weekday()  # Thursday is 3
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return today + timedelta(days=days_ahead)


def get_next_sunday():
    """Get the next Sunday from today"""
    today = datetime.now(timezone.utc)
    days_ahead = 6 - today.weekday()  # Sunday is 6
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return today + timedelta(days=days_ahead)


def get_next_monday():
    """Get the next Monday from today"""
    today = datetime.now(timezone.utc)
    days_ahead = 0 - today.weekday()  # Monday is 0
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return today + timedelta(days=days_ahead)


async def seed_games():
    """Seed sample games for current/upcoming week"""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        print("🏈 Seeding NFL games...")

        # Get all teams
        result = await session.execute(select(Team))
        teams = {team.abbreviation: team for team in result.scalars().all()}

        if len(teams) < 4:
            print("❌ Not enough teams found! Please run seed_teams.py first.")
            return

        # Get dates for upcoming games
        next_thursday = get_next_thursday().replace(
            hour=20, minute=15, second=0, microsecond=0
        )
        next_sunday = get_next_sunday()
        sunday_early = next_sunday.replace(hour=13, minute=0, second=0, microsecond=0)
        sunday_afternoon = next_sunday.replace(
            hour=16, minute=25, second=0, microsecond=0
        )
        sunday_night = next_sunday.replace(hour=20, minute=20, second=0, microsecond=0)
        next_monday = get_next_monday().replace(
            hour=20, minute=15, second=0, microsecond=0
        )

        # Define sample matchups (using common team abbreviations)
        sample_games = [
            # Thursday Night Football
            {
                "external_id": "2024_week_15_tnf_1",
                "home_team": "KC",
                "away_team": "LAC",
                "kickoff_time": next_thursday,
                "game_type": GameType.TNF,
                "week_number": 15,
            },
            # Sunday Early Games
            {
                "external_id": "2024_week_15_sun_early_1",
                "home_team": "BUF",
                "away_team": "MIA",
                "kickoff_time": sunday_early,
                "game_type": GameType.SUNDAY_EARLY,
                "week_number": 15,
            },
            {
                "external_id": "2024_week_15_sun_early_2",
                "home_team": "BAL",
                "away_team": "CIN",
                "kickoff_time": sunday_early,
                "game_type": GameType.SUNDAY_EARLY,
                "week_number": 15,
            },
            {
                "external_id": "2024_week_15_sun_early_3",
                "home_team": "DET",
                "away_team": "CHI",
                "kickoff_time": sunday_early,
                "game_type": GameType.SUNDAY_EARLY,
                "week_number": 15,
            },
            # Sunday Afternoon Games
            {
                "external_id": "2024_week_15_sun_main_1",
                "home_team": "SF",
                "away_team": "SEA",
                "kickoff_time": sunday_afternoon,
                "game_type": GameType.SUNDAY_MAIN,
                "week_number": 15,
            },
            {
                "external_id": "2024_week_15_sun_main_2",
                "home_team": "DAL",
                "away_team": "PHI",
                "kickoff_time": sunday_afternoon,
                "game_type": GameType.SUNDAY_MAIN,
                "week_number": 15,
            },
            # Sunday Night Football
            {
                "external_id": "2024_week_15_snf_1",
                "home_team": "GB",
                "away_team": "MIN",
                "kickoff_time": sunday_night,
                "game_type": GameType.SNF,
                "week_number": 15,
            },
            # Monday Night Football
            {
                "external_id": "2024_week_15_mnf_1",
                "home_team": "NO",
                "away_team": "ATL",
                "kickoff_time": next_monday,
                "game_type": GameType.MNF,
                "week_number": 15,
            },
        ]

        # Check existing games
        result = await session.execute(select(Game))
        existing_games = result.scalars().all()
        existing_external_ids = {game.external_id for game in existing_games}

        games_created = 0
        games_skipped = 0

        for game_data in sample_games:
            if game_data["external_id"] in existing_external_ids:
                print(
                    f"⏭️  Skipping {game_data['away_team']} @ {game_data['home_team']} (already exists)"
                )
                games_skipped += 1
                continue

            # Check if teams exist
            if (
                game_data["home_team"] not in teams
                or game_data["away_team"] not in teams
            ):
                print(
                    f"⚠️  Skipping {game_data['away_team']} @ {game_data['home_team']} (teams not found)"
                )
                continue

            home_team = teams[game_data["home_team"]]
            away_team = teams[game_data["away_team"]]

            game = Game(
                external_id=game_data["external_id"],
                season_year=2024,
                week_number=game_data["week_number"],
                game_type=game_data["game_type"],
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                game_date=game_data["kickoff_time"].date(),
                kickoff_time=game_data["kickoff_time"],
                status=GameStatus.SCHEDULED,
            )
            session.add(game)
            games_created += 1

            kickoff_str = game_data["kickoff_time"].strftime("%a %b %d, %I:%M %p %Z")
            print(
                f"✅ Created {away_team.abbreviation} @ {home_team.abbreviation} - {kickoff_str}"
            )

        if games_created > 0:
            await session.commit()

        print(f"\n📊 Summary:")
        print(f"   Created: {games_created} games")
        print(f"   Skipped: {games_skipped} games (already exist)")
        print(f"   Total: {len(sample_games)} games")

    await engine.dispose()
    print("\n✅ Game seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_games())
