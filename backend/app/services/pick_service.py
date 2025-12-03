"""Pick service"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import Optional, List
from app.db.models.pick import Pick
from app.schemas.pick import PickCreate, PickUpdate


class PickService:
    """Service for pick operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_picks(
        self,
        user_id: Optional[UUID] = None,
        game_id: Optional[UUID] = None
    ) -> List[Pick]:
        """Get picks with optional filters"""
        query = select(Pick)
        
        if user_id is not None:
            query = query.where(Pick.user_id == user_id)
        if game_id is not None:
            query = query.where(Pick.game_id == game_id)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_pick_by_id(self, pick_id: UUID) -> Pick | None:
        """Get pick by ID"""
        result = await self.db.execute(
            select(Pick).where(Pick.id == pick_id)
        )
        return result.scalar_one_or_none()

    async def create_pick(self, pick_data: PickCreate, user_id: UUID = None) -> Pick:
        """Create a new pick"""
        pick = Pick(**pick_data.model_dump(), user_id=user_id)
        self.db.add(pick)
        await self.db.commit()
        await self.db.refresh(pick)
        return pick

    async def update_pick(self, pick_id: UUID, pick_update: PickUpdate) -> Pick | None:
        """Update a pick"""
        pick = await self.get_pick_by_id(pick_id)
        if not pick:
            return None

        if pick_update.player_id is not None:
            pick.player_id = pick_update.player_id
        if pick_update.snapshot_odds is not None:
            pick.snapshot_odds = pick_update.snapshot_odds

        await self.db.commit()
        await self.db.refresh(pick)
        return pick

