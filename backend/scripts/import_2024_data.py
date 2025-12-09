"""
Import 2024 NFL season data from nflreadpy

This script imports real 2024 NFL game data from nflreadpy to populate the database
with actual games, teams, and players for testing the scoring and leaderboard systems.

Usage:
    # Import specific weeks (recommended for testing)
    python backend/scripts/import_2024_data.py --weeks 13 14 15

    # Import entire season
    python backend/scripts/import_2024_data.py --all

    # Import and grade completed games
    python backend/scripts/import_2024_data.py --weeks 13 14 --grade

Requirements:
    - nflreadpy library
    - Database must be running
    - Teams and players should be seeded first (or will be created)
"""

import asyncio
import argparse
from datetime import datetime, timezone
from uuid import uuid4
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

import nflreadpy as nfl

from app.db.models.user import User
from app.db.models.team import Team
from app.db.models.player import Player
from app.db.models.game import Game, GameStatus, GameType
from app.core.config import settings


class NFLDataImporter:
    """Handles importing NFL data from nflreadpy to database"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.stats = {
            "teams_created": 0,
            "players_created": 0,
            "games_created": 0,
            "games_updated": 0,
            "games_graded": 0,
            "errors": 0,
        }

    async def get_or_create_team(
        self, team_abbr: str, team_data: Optional[Dict[str, Any]] = None
    ) -> Team:
        """Get existing team or create new one"""
        # Try to find team by abbreviation
        result = await self.session.execute(
            select(Team).where(Team.abbreviation == team_abbr)
        )
        team = result.scalar_one_or_none()

        if not team:
            # Create new team
            # Use team_data if provided, otherwise use abbreviation as placeholder
            team_name = team_data.get("name", team_abbr) if team_data else team_abbr
            team_city = team_data.get("city", team_abbr) if team_data else team_abbr

            team = Team(
                id=uuid4(),
                external_id=f"nfl_{team_abbr.lower()}",
                name=team_name,
                abbreviation=team_abbr,
                city=team_city,
            )
            self.session.add(team)
            self.stats["teams_created"] += 1
            print(f"  ✓ Created team: {team_abbr}")

        return team

    async def get_or_create_player(
        self,
        player_id: str,
        player_name: str,
        position: str,
        team: Team,
    ) -> Player:
        """Get existing player or create new one"""
        # Try to find player by external_id
        result = await self.session.execute(
            select(Player).where(Player.external_id == player_id)
        )
        player = result.scalar_one_or_none()

        if not player:
            # Create new player
            player = Player(
                id=uuid4(),
                external_id=player_id,
                name=player_name,
                position=position or "RB",
                team_id=team.id,
            )
            self.session.add(player)
            self.stats["players_created"] += 1
            print(f"  ✓ Created player: {player_name} ({position})")

        return player

    async def import_game(self, game_data: Dict[str, Any]) -> Optional[Game]:
        """Import a single game from nflreadpy data"""
        try:
            game_id = game_data.get("game_id")
            if not game_id:
                print("  ✗ Game missing game_id, skipping")
                self.stats["errors"] += 1
                return None

            # Check if game already exists
            result = await self.session.execute(
                select(Game).where(Game.external_id == game_id)
            )
            existing_game = result.scalar_one_or_none()

            # Get or create teams
            home_team = await self.get_or_create_team(game_data.get("home_team"))
            away_team = await self.get_or_create_team(game_data.get("away_team"))

            # Parse game date and kickoff time
            game_date_str = game_data.get("gameday")
            if game_date_str:
                try:
                    game_date = datetime.fromisoformat(
                        game_date_str.replace("Z", "+00:00")
                    )
                except (ValueError, AttributeError):
                    # Fallback to current time if parsing fails
                    game_date = datetime.now(timezone.utc)
            else:
                game_date = datetime.now(timezone.utc)

            # Map game type
            game_type_map = {
                "REG": GameType.SUNDAY_MAIN,
                "WC": GameType.WILDCARD,
                "DIV": GameType.DIVISIONAL,
                "CON": GameType.CONFERENCE,
                "SB": GameType.SUPERBOWL,
            }
            season_type = game_data.get("season_type", "REG")
            game_type = game_type_map.get(season_type, GameType.SUNDAY_MAIN)

            # Determine game status
            # nflreadpy doesn't have a direct status field, infer from scores
            home_score = game_data.get("home_score")
            away_score = game_data.get("away_score")

            if home_score is not None and away_score is not None:
                status = GameStatus.COMPLETED
            elif game_date < datetime.now(timezone.utc):
                status = GameStatus.IN_PROGRESS
            else:
                status = GameStatus.SCHEDULED

            if existing_game:
                # Update existing game
                existing_game.status = status
                existing_game.final_score_home = home_score
                existing_game.final_score_away = away_score
                existing_game.game_date = game_date
                existing_game.kickoff_time = game_date
                self.stats["games_updated"] += 1
                print(f"  ↻ Updated game: {game_id}")
                return existing_game
            else:
                # Create new game
                game = Game(
                    id=uuid4(),
                    external_id=game_id,
                    week_number=game_data.get("week", 1),
                    season_year=game_data.get("season", 2024),
                    game_type=game_type,
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    game_date=game_date,
                    kickoff_time=game_date,
                    status=status,
                    final_score_home=home_score,
                    final_score_away=away_score,
                )
                self.session.add(game)
                self.stats["games_created"] += 1
                print(
                    f"  ✓ Created game: {game_id} - {away_team.abbreviation} @ {home_team.abbreviation}"
                )
                return game

        except Exception as e:
            print(f"  ✗ Error importing game {game_data.get('game_id')}: {str(e)}")
            self.stats["errors"] += 1
            return None

    async def grade_game(self, game: Game) -> bool:
        """Grade a completed game by fetching touchdown data"""
        try:
            if game.status != GameStatus.COMPLETED:
                print(f"  ⊘ Game {game.external_id} not completed, skipping grading")
                return False

            print(f"  ⚙ Grading game: {game.external_id}")

            # Extract season from game_id
            season = int(game.external_id.split("_")[0])

            # Fetch play-by-play data for the season
            print(f"    Loading play-by-play data for season {season}...")
            pbp_df = nfl.load_pbp(seasons=[season]).to_pandas()

            # Filter to touchdown plays for this specific game
            game_tds = pbp_df[
                (pbp_df["game_id"] == game.external_id) & (pbp_df["touchdown"] == 1)
            ].copy()

            if game_tds.empty:
                print(f"    ⊘ No touchdowns found for game {game.external_id}")
                return True

            # Sort by game_seconds_remaining (descending = chronological order)
            game_tds_sorted = game_tds.sort_values(
                "game_seconds_remaining", ascending=False
            )

            # Get first TD scorer
            first_td = game_tds_sorted.iloc[0]
            first_td_player_id = (
                str(first_td["td_player_id"])
                if first_td.get("td_player_id") is not None
                else None
            )
            first_td_player_name = (
                str(first_td["td_player_name"])
                if first_td.get("td_player_name") is not None
                else None
            )

            if first_td_player_id:
                # Find or create player
                # Determine team for player
                td_team_abbr = first_td.get("td_team")
                if td_team_abbr:
                    td_team = await self.get_or_create_team(td_team_abbr)

                    # Get or create player
                    first_td_player = await self.get_or_create_player(
                        first_td_player_id,
                        first_td_player_name,
                        "RB",  # Position not available in play-by-play, use placeholder
                        td_team,
                    )

                    game.first_td_scorer_player_id = first_td_player.id
                    print(f"    ✓ First TD: {first_td_player_name}")

            # Get all unique TD scorers
            all_td_player_ids = []
            for _, td_play in game_tds_sorted.iterrows():
                td_player_id = (
                    str(td_play["td_player_id"])
                    if td_play.get("td_player_id") is not None
                    else None
                )
                td_player_name = (
                    str(td_play["td_player_name"])
                    if td_play.get("td_player_name") is not None
                    else None
                )
                td_team_abbr = td_play.get("td_team")

                if td_player_id and td_team_abbr:
                    td_team = await self.get_or_create_team(td_team_abbr)
                    td_player = await self.get_or_create_player(
                        td_player_id,
                        td_player_name,
                        "RB",
                        td_team,
                    )
                    all_td_player_ids.append(str(td_player.id))

            game.all_td_scorer_player_ids = all_td_player_ids
            game.scored_at = datetime.now(timezone.utc)

            print(f"    ✓ Graded: {len(all_td_player_ids)} TD scorers")
            self.stats["games_graded"] += 1
            return True

        except Exception as e:
            print(f"  ✗ Error grading game {game.external_id}: {str(e)}")
            self.stats["errors"] += 1
            return False


async def import_nfl_data(weeks: Optional[List[int]] = None, grade: bool = False):
    """Main import function"""
    print("=" * 70)
    print("NFL 2024 Season Data Import")
    print("=" * 70)
    print()

    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        importer = NFLDataImporter(session)

        # Fetch 2024 season schedule
        print("📡 Fetching 2024 NFL season schedule from nflreadpy...")
        schedules_df = nfl.load_schedules(seasons=[2024]).to_pandas()
        print(f"✓ Retrieved {len(schedules_df)} games")
        print()

        # Filter to specific weeks if requested
        if weeks:
            schedules_df = schedules_df[schedules_df["week"].isin(weeks)]
            print(f"📋 Filtering to weeks: {', '.join(map(str, weeks))}")
            print(f"   Games to import: {len(schedules_df)}")
            print()

        # Import games
        print("📥 Importing games...")
        print()

        games_to_grade = []

        for idx, game_data in schedules_df.iterrows():
            week = game_data.get("week")
            home = game_data.get("home_team")
            away = game_data.get("away_team")

            print(f"Week {week}: {away} @ {home}")

            game = await importer.import_game(game_data.to_dict())

            if game and grade and game.status == GameStatus.COMPLETED:
                games_to_grade.append(game)

        # Commit game imports
        print()
        print("💾 Committing game data to database...")
        await session.commit()
        print("✓ Games committed")
        print()

        # Grade completed games if requested
        if grade and games_to_grade:
            print("=" * 70)
            print(f"🎯 Grading {len(games_to_grade)} completed games...")
            print("=" * 70)
            print()

            for game in games_to_grade:
                await importer.grade_game(game)

            print()
            print("💾 Committing grading data to database...")
            await session.commit()
            print("✓ Grading data committed")
            print()

        # Print summary
        print("=" * 70)
        print("Import Complete!")
        print("=" * 70)
        print()
        print(f"Teams created:    {importer.stats['teams_created']}")
        print(f"Players created:  {importer.stats['players_created']}")
        print(f"Games created:    {importer.stats['games_created']}")
        print(f"Games updated:    {importer.stats['games_updated']}")
        if grade:
            print(f"Games graded:     {importer.stats['games_graded']}")
        print(f"Errors:           {importer.stats['errors']}")
        print()
        print("=" * 70)


def main():
    """Parse arguments and run import"""
    parser = argparse.ArgumentParser(
        description="Import 2024 NFL season data from nflreadpy"
    )
    parser.add_argument(
        "--weeks",
        type=int,
        nargs="+",
        help="Specific weeks to import (e.g., --weeks 13 14 15)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Import entire 2024 season",
    )
    parser.add_argument(
        "--grade",
        action="store_true",
        help="Grade completed games (fetch touchdown data)",
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.weeks and not args.all:
        print("Error: Must specify either --weeks or --all")
        parser.print_help()
        return

    weeks = None if args.all else args.weeks

    # Run import
    asyncio.run(import_nfl_data(weeks=weeks, grade=args.grade))


if __name__ == "__main__":
    main()
