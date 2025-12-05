"""Game service"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import Optional, List
from datetime import datetime, timezone
from app.db.models.game import Game
from app.db.models.pick import Pick
from app.db.models.team import Team
from app.db.models.player import Player
from app.schemas.game import GameCreate


class GameService:
    """Service for game operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_games(
        self,
        week: Optional[int] = None,
        season: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[Game]:
        """Get games with optional filters"""
        query = select(Game)

        if week is not None:
            query = query.where(Game.week_number == week)
        if season is not None:
            query = query.where(Game.season_year == season)
        if status is not None:
            query = query.where(Game.status == status)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_game_by_id(self, game_id: UUID) -> Game | None:
        """Get game by ID"""
        result = await self.db.execute(select(Game).where(Game.id == game_id))
        return result.scalar_one_or_none()

    async def create_game(self, game_data: GameCreate) -> Game:
        """Create a new game"""
        game = Game(**game_data.model_dump())
        self.db.add(game)
        await self.db.commit()
        await self.db.refresh(game)
        return game

    async def get_available_games(self, user_id: Optional[UUID] = None) -> List[dict]:
        """
        Get games available for picks (future kickoffs).
        Includes user's existing picks if user_id is provided.

        Requirements: 7.1, 7.2, 7.4, 8.1, 8.2
        """
        now = datetime.now(timezone.utc)

        # Build query for games with future kickoff times
        query = (
            select(Game)
            .where(Game.kickoff_time > now)
            .order_by(Game.kickoff_time.asc())
        )

        result = await self.db.execute(query)
        games = result.scalars().all()

        # If user_id provided, fetch their picks for these games
        user_picks = {}
        if user_id:
            game_ids = [game.id for game in games]
            if game_ids:
                picks_query = (
                    select(Pick)
                    .where(Pick.user_id == user_id)
                    .where(Pick.game_id.in_(game_ids))
                )
                picks_result = await self.db.execute(picks_query)
                picks = picks_result.scalars().all()

                # Map picks by game_id
                for pick in picks:
                    user_picks[pick.game_id] = pick

        # Build response with game and pick data
        games_with_picks = []
        for game in games:
            # Fetch team data
            home_team_result = await self.db.execute(
                select(Team).where(Team.id == game.home_team_id)
            )
            home_team = home_team_result.scalar_one_or_none()

            away_team_result = await self.db.execute(
                select(Team).where(Team.id == game.away_team_id)
            )
            away_team = away_team_result.scalar_one_or_none()

            game_data = {
                "id": game.id,
                "home_team": home_team.name if home_team else "Unknown",
                "away_team": away_team.name if away_team else "Unknown",
                "kickoff_time": game.kickoff_time,
                "week_number": game.week_number,
                "user_pick": None,
            }

            # Add pick data if exists
            if game.id in user_picks:
                pick = user_picks[game.id]
                # Fetch player name
                player_result = await self.db.execute(
                    select(Player).where(Player.id == pick.player_id)
                )
                player = player_result.scalar_one_or_none()

                game_data["user_pick"] = {
                    "id": pick.id,
                    "player_name": player.name if player else "Unknown",
                }

            games_with_picks.append(game_data)

        return games_with_picks

    async def is_game_locked(self, game_id: UUID) -> bool:
        """
        Check if a game is locked (kickoff time has passed).

        Requirements: 1.5, 3.3, 4.2
        """
        game = await self.get_game_by_id(game_id)
        if not game:
            return True  # Treat non-existent games as locked

        now = datetime.now(timezone.utc)
        return game.kickoff_time <= now
