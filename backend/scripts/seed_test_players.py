"""Seed test players and teams for testing"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.db.models.team import Team
from app.db.models.player import Player
import uuid

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@db:5432/first6"


async def seed_data():
    """Seed test teams and players"""
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Create teams
        chiefs = Team(
            id=uuid.uuid4(),
            external_id="KC",
            name="Kansas City Chiefs",
            abbreviation="KC",
            city="Kansas City",
        )
        bills = Team(
            id=uuid.uuid4(),
            external_id="BUF",
            name="Buffalo Bills",
            abbreviation="BUF",
            city="Buffalo",
        )

        session.add(chiefs)
        session.add(bills)
        await session.commit()
        await session.refresh(chiefs)
        await session.refresh(bills)

        print(f"✅ Created teams: {chiefs.name}, {bills.name}")

        # Create players for Chiefs
        players = [
            Player(
                id=uuid.uuid4(),
                external_id="mahomes_patrick",
                name="Patrick Mahomes",
                team_id=chiefs.id,
                position="QB",
                jersey_number=15,
                is_active=True,
            ),
            Player(
                id=uuid.uuid4(),
                external_id="kelce_travis",
                name="Travis Kelce",
                team_id=chiefs.id,
                position="TE",
                jersey_number=87,
                is_active=True,
            ),
            Player(
                id=uuid.uuid4(),
                external_id="hill_tyreek",
                name="Tyreek Hill",
                team_id=chiefs.id,
                position="WR",
                jersey_number=10,
                is_active=True,
            ),
            # Bills players
            Player(
                id=uuid.uuid4(),
                external_id="allen_josh",
                name="Josh Allen",
                team_id=bills.id,
                position="QB",
                jersey_number=17,
                is_active=True,
            ),
            Player(
                id=uuid.uuid4(),
                external_id="diggs_stefon",
                name="Stefon Diggs",
                team_id=bills.id,
                position="WR",
                jersey_number=14,
                is_active=True,
            ),
        ]

        for player in players:
            session.add(player)

        await session.commit()

        print(f"✅ Created {len(players)} players")
        print("\nPlayers created:")
        for player in players:
            print(f"  - {player.name} ({player.position}) - {player.team_id}")

    await engine.dispose()
    print("\n✅ Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_data())
