"""Scoring service for grading picks"""

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.pick import Pick, PickResult
from app.db.models.game import Game
from sqlalchemy import select
from uuid import UUID
from datetime import datetime


class ScoringService:
    """Service for scoring and grading picks"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def grade_picks_for_game(self, game_id: UUID) -> int:
        """Grade all picks for a completed game"""
        # Get the game
        result = await self.db.execute(
            select(Game).where(Game.id == game_id)
        )
        game = result.scalar_one_or_none()
        
        if not game or game.status != "completed":
            return 0
        
        # Get all pending picks for this game
        picks_result = await self.db.execute(
            select(Pick).where(
                Pick.game_id == game_id,
                Pick.status == PickResult.PENDING
            )
        )
        picks = picks_result.scalars().all()
        
        graded_count = 0
        first_td_scorer_id = game.first_td_scorer_player_id
        
        for pick in picks:
            if pick.pick_type == "FTD":
                # Check if player scored first TD
                if pick.player_id == first_td_scorer_id:
                    pick.status = PickResult.WIN
                else:
                    pick.status = PickResult.LOSS
                pick.settled_at = datetime.utcnow()
                graded_count += 1
            elif pick.pick_type == "ATTD":
                # TODO: Check if player scored any TD during the game
                # This requires additional game data (all TD scorers)
                pass
        
        await self.db.commit()
        return graded_count

