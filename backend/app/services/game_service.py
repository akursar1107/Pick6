"""Game service"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import Optional, List
from app.db.models.game import Game
from app.schemas.game import GameCreate


class GameService:
    """Service for game operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_games(
        self,
        week: Optional[int] = None,
        season: Optional[int] = None,
        status: Optional[str] = None
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
        result = await self.db.execute(
            select(Game).where(Game.id == game_id)
        )
        return result.scalar_one_or_none()

    async def create_game(self, game_data: GameCreate) -> Game:
        """Create a new game"""
        game = Game(**game_data.model_dump())
        self.db.add(game)
        await self.db.commit()
        await self.db.refresh(game)
        return game

