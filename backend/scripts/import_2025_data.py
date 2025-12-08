"""
Import 2025 season data from CSV

This script imports historical pick data from the 2025 season CSV file.
It will create users, games, and picks based on the CSV data.
"""

import asyncio
import csv
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.db.models.user import User
from app.db.models.team import Team
from app.db.models.player import Player
from app.db.models.game import Game, GameStatus
from app.db.models.pick import Pick, PickResult
from app.core.config import settings

# CSV file path
CSV_FILE = "tests/TestImportData/First TD - 2025 (4).csv"

# Pre-hashed password for "password123" using bcrypt
# This avoids bcrypt issues during import
HASHED_PASSWORD = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU2xNjM3aW4W"


async def get_or_create_user(session: AsyncSession, username: str) -> User:
    """Get existing user or create new one"""
    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user:
        # Create new user with default password (password123)
        user = User(
            id=uuid4(),
            username=username,
            email=f"{username.lower().replace(' ', '')}@first6.com",
            hashed_password=HASHED_PASSWORD,
            display_name=username,
            is_active=True,
        )
        session.add(user)
        print(f"  Created user: {username}")

    return user


async def get_or_create_team(session: AsyncSession, team_name: str) -> Team:
    """Get existing team or create placeholder"""
    # Try to find team by name (case insensitive)
    result = await session.execute(
        select(Team).where(Team.name.ilike(f"%{team_name}%"))
    )
    team = result.scalar_one_or_none()

    if not team:
        # Create placeholder team with external_id
        external_id = f"import_{team_name.lower().replace(' ', '_')}"
        team = Team(
            id=uuid4(),
            external_id=external_id,
            name=team_name,
            abbreviation=team_name[:3].upper(),
            city=team_name,
        )
        session.add(team)
        print(f"  Created team: {team_name}")

    return team


async def get_or_create_player(
    session: AsyncSession, player_name: str, position: str, team: Team
) -> Player:
    """Get existing player or create placeholder"""
    # Try to find player by name
    result = await session.execute(
        select(Player).where(Player.name.ilike(f"%{player_name}%"))
    )
    player = result.scalar_one_or_none()

    if not player:
        # Create placeholder player with external_id
        external_id = (
            f"import_{player_name.lower().replace(' ', '_')}_{team.abbreviation}"
        )
        player = Player(
            id=uuid4(),
            external_id=external_id,
            name=player_name,
            position=position or "RB",
            team_id=team.id,
        )
        session.add(player)
        print(f"  Created player: {player_name} ({position})")

    return player


async def get_or_create_game(
    session: AsyncSession,
    week: int,
    home_team: Team,
    away_team: Team,
    gameday: str,
) -> Game:
    """Get existing game or create new one"""
    # Try to find game by week and teams
    result = await session.execute(
        select(Game).where(
            Game.week_number == week,
            Game.home_team_id == home_team.id,
            Game.away_team_id == away_team.id,
        )
    )
    game = result.scalar_one_or_none()

    if not game:
        # Create game with estimated kickoff time
        # Map gameday to game_type
        from app.db.models.game import GameType

        game_type_map = {
            "Thursday": GameType.TNF,
            "Sunday": GameType.SUNDAY_MAIN,
            "Monday": GameType.MNF,
            "Saturday": GameType.SATURDAY,
        }
        game_type = game_type_map.get(gameday, GameType.SUNDAY_MAIN)

        # Use a placeholder date - week 1 starts around Sept 5, 2025
        # Calculate days from week 1
        from datetime import timedelta

        base_date = datetime(2025, 9, 5, 20, 0, tzinfo=timezone.utc)
        kickoff_time = base_date + timedelta(days=(week - 1) * 7)
        game_date = kickoff_time

        game = Game(
            id=uuid4(),
            external_id=f"2025_week_{week}_{away_team.abbreviation}_{home_team.abbreviation}",
            week_number=week,
            season_year=2025,
            game_type=game_type,
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            game_date=game_date,
            kickoff_time=kickoff_time,
            status=GameStatus.COMPLETED,  # Assume completed for now
        )
        session.add(game)
        print(f"  Created game: Week {week} - {away_team.name} @ {home_team.name}")

    return game


async def import_csv_data():
    """Main import function"""
    print("Starting 2025 season data import...")
    print(f"Reading CSV: {CSV_FILE}")

    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Read CSV file
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        print(f"Found {len(rows)} rows in CSV")

        # Track stats
        stats = {
            "users": 0,
            "teams": 0,
            "players": 0,
            "games": 0,
            "picks": 0,
            "skipped": 0,
        }

        for i, row in enumerate(rows, 1):
            # Skip empty rows
            if not row.get("Week") or not row.get("Picker"):
                stats["skipped"] += 1
                continue

            try:
                week = int(row["Week"])
            except (ValueError, TypeError):
                stats["skipped"] += 1
                continue

            print(f"\nProcessing row {i}: Week {week}, {row['Picker']}")

            # Get or create user
            user = await get_or_create_user(session, row["Picker"])
            if user.id not in [u.id for u in session.new]:
                stats["users"] += 1

            # Get or create teams
            home_team = await get_or_create_team(session, row["Home"])
            away_team = await get_or_create_team(
                session, row["Vistor"]
            )  # Note: typo in CSV

            # Get or create player
            if row.get("Player"):
                player = await get_or_create_player(
                    session,
                    row["Player"],
                    row.get("Position", "RB"),
                    home_team,  # Assume player is on home team for now
                )
            else:
                print("  Skipping: No player specified")
                stats["skipped"] += 1
                continue

            # Get or create game
            game = await get_or_create_game(
                session, week, home_team, away_team, row.get("Gameday", "Sunday")
            )

            # Create pick
            result = row.get("Result", "").upper()
            if result == "W":
                status = PickResult.WIN
            elif result == "L":
                status = PickResult.LOSS
            else:
                status = PickResult.PENDING

            # Check if pick already exists
            existing_pick = await session.execute(
                select(Pick).where(
                    Pick.user_id == user.id,
                    Pick.game_id == game.id,
                )
            )
            if existing_pick.scalar_one_or_none():
                print("  Pick already exists, skipping")
                stats["skipped"] += 1
                continue

            pick = Pick(
                id=uuid4(),
                user_id=user.id,
                game_id=game.id,
                player_id=player.id,
                status=status,
                pick_submitted_at=datetime.now(timezone.utc),
            )
            session.add(pick)
            stats["picks"] += 1
            print(f"  Created pick: {user.username} -> {player.name} ({status.value})")

        # Commit all changes
        print("\nCommitting changes to database...")
        await session.commit()

        print("\n" + "=" * 60)
        print("Import Complete!")
        print("=" * 60)
        print(f"Users created: {stats['users']}")
        print(f"Picks created: {stats['picks']}")
        print(f"Rows skipped: {stats['skipped']}")
        print("\nDefault password for all users: password123")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(import_csv_data())
