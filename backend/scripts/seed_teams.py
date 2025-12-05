"""Seed all 32 NFL teams"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from app.db.models.team import Team

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@db:5432/first6"

# All 32 NFL teams with their official data
NFL_TEAMS = [
    # AFC East
    {
        "external_id": "BUF",
        "name": "Buffalo Bills",
        "abbreviation": "BUF",
        "city": "Buffalo",
    },
    {
        "external_id": "MIA",
        "name": "Miami Dolphins",
        "abbreviation": "MIA",
        "city": "Miami",
    },
    {
        "external_id": "NE",
        "name": "New England Patriots",
        "abbreviation": "NE",
        "city": "New England",
    },
    {
        "external_id": "NYJ",
        "name": "New York Jets",
        "abbreviation": "NYJ",
        "city": "New York",
    },
    # AFC North
    {
        "external_id": "BAL",
        "name": "Baltimore Ravens",
        "abbreviation": "BAL",
        "city": "Baltimore",
    },
    {
        "external_id": "CIN",
        "name": "Cincinnati Bengals",
        "abbreviation": "CIN",
        "city": "Cincinnati",
    },
    {
        "external_id": "CLE",
        "name": "Cleveland Browns",
        "abbreviation": "CLE",
        "city": "Cleveland",
    },
    {
        "external_id": "PIT",
        "name": "Pittsburgh Steelers",
        "abbreviation": "PIT",
        "city": "Pittsburgh",
    },
    # AFC South
    {
        "external_id": "HOU",
        "name": "Houston Texans",
        "abbreviation": "HOU",
        "city": "Houston",
    },
    {
        "external_id": "IND",
        "name": "Indianapolis Colts",
        "abbreviation": "IND",
        "city": "Indianapolis",
    },
    {
        "external_id": "JAX",
        "name": "Jacksonville Jaguars",
        "abbreviation": "JAX",
        "city": "Jacksonville",
    },
    {
        "external_id": "TEN",
        "name": "Tennessee Titans",
        "abbreviation": "TEN",
        "city": "Tennessee",
    },
    # AFC West
    {
        "external_id": "DEN",
        "name": "Denver Broncos",
        "abbreviation": "DEN",
        "city": "Denver",
    },
    {
        "external_id": "KC",
        "name": "Kansas City Chiefs",
        "abbreviation": "KC",
        "city": "Kansas City",
    },
    {
        "external_id": "LV",
        "name": "Las Vegas Raiders",
        "abbreviation": "LV",
        "city": "Las Vegas",
    },
    {
        "external_id": "LAC",
        "name": "Los Angeles Chargers",
        "abbreviation": "LAC",
        "city": "Los Angeles",
    },
    # NFC East
    {
        "external_id": "DAL",
        "name": "Dallas Cowboys",
        "abbreviation": "DAL",
        "city": "Dallas",
    },
    {
        "external_id": "NYG",
        "name": "New York Giants",
        "abbreviation": "NYG",
        "city": "New York",
    },
    {
        "external_id": "PHI",
        "name": "Philadelphia Eagles",
        "abbreviation": "PHI",
        "city": "Philadelphia",
    },
    {
        "external_id": "WAS",
        "name": "Washington Commanders",
        "abbreviation": "WAS",
        "city": "Washington",
    },
    # NFC North
    {
        "external_id": "CHI",
        "name": "Chicago Bears",
        "abbreviation": "CHI",
        "city": "Chicago",
    },
    {
        "external_id": "DET",
        "name": "Detroit Lions",
        "abbreviation": "DET",
        "city": "Detroit",
    },
    {
        "external_id": "GB",
        "name": "Green Bay Packers",
        "abbreviation": "GB",
        "city": "Green Bay",
    },
    {
        "external_id": "MIN",
        "name": "Minnesota Vikings",
        "abbreviation": "MIN",
        "city": "Minnesota",
    },
    # NFC South
    {
        "external_id": "ATL",
        "name": "Atlanta Falcons",
        "abbreviation": "ATL",
        "city": "Atlanta",
    },
    {
        "external_id": "CAR",
        "name": "Carolina Panthers",
        "abbreviation": "CAR",
        "city": "Carolina",
    },
    {
        "external_id": "NO",
        "name": "New Orleans Saints",
        "abbreviation": "NO",
        "city": "New Orleans",
    },
    {
        "external_id": "TB",
        "name": "Tampa Bay Buccaneers",
        "abbreviation": "TB",
        "city": "Tampa Bay",
    },
    # NFC West
    {
        "external_id": "ARI",
        "name": "Arizona Cardinals",
        "abbreviation": "ARI",
        "city": "Arizona",
    },
    {
        "external_id": "LAR",
        "name": "Los Angeles Rams",
        "abbreviation": "LAR",
        "city": "Los Angeles",
    },
    {
        "external_id": "SF",
        "name": "San Francisco 49ers",
        "abbreviation": "SF",
        "city": "San Francisco",
    },
    {
        "external_id": "SEA",
        "name": "Seattle Seahawks",
        "abbreviation": "SEA",
        "city": "Seattle",
    },
]


async def seed_teams():
    """Seed all 32 NFL teams"""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        print("🏈 Seeding NFL teams...")

        # Check existing teams
        result = await session.execute(select(Team))
        existing_teams = result.scalars().all()
        existing_external_ids = {team.external_id for team in existing_teams}

        teams_created = 0
        teams_skipped = 0

        for team_data in NFL_TEAMS:
            if team_data["external_id"] in existing_external_ids:
                print(f"⏭️  Skipping {team_data['name']} (already exists)")
                teams_skipped += 1
                continue

            team = Team(
                external_id=team_data["external_id"],
                name=team_data["name"],
                abbreviation=team_data["abbreviation"],
                city=team_data["city"],
            )
            session.add(team)
            teams_created += 1
            print(f"✅ Created {team_data['name']}")

        if teams_created > 0:
            await session.commit()

        print(f"\n📊 Summary:")
        print(f"   Created: {teams_created} teams")
        print(f"   Skipped: {teams_skipped} teams (already exist)")
        print(f"   Total: {len(NFL_TEAMS)} teams")

    await engine.dispose()
    print("\n✅ Team seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_teams())
