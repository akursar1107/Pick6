"""Player service"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from uuid import UUID
from typing import List, Optional
from app.db.models.player import Player
from app.db.models.team import Team


class PlayerService:
    """Service for player operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_players(self, query: str, limit: int = 20) -> List[Player]:
        """
        Search for players by name using ILIKE search.

        Args:
            query: Search query string
            limit: Maximum number of results to return

        Returns:
            List of matching players
        """
        if not query or query.strip() == "":
            return []

        try:
            # Use ILIKE for case-insensitive search
            search_pattern = f"%{query}%"
            stmt = (
                select(Player)
                .where(Player.name.ilike(search_pattern))
                .limit(limit)
                .order_by(Player.name)
            )

            result = await self.db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            # Log the error in production
            raise Exception(f"Error searching players: {str(e)}")

    async def get_player_by_id(self, player_id: UUID) -> Optional[Player]:
        """
        Get a player by ID.

        Args:
            player_id: UUID of the player

        Returns:
            Player object if found, None otherwise
        """
        try:
            stmt = select(Player).where(Player.id == player_id)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            # Log the error in production
            raise Exception(f"Error fetching player: {str(e)}")
