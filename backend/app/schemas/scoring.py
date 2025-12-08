"""Scoring schemas for API responses"""

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class UserScore(BaseModel):
    """User's total score and statistics"""

    user_id: UUID
    total_score: int = Field(description="Total points from all winning picks")
    total_wins: int = Field(description="Number of winning picks")
    total_losses: int = Field(description="Number of losing picks")
    win_percentage: float = Field(description="Win percentage (0-100)")

    class Config:
        from_attributes = True


class PickResultResponse(BaseModel):
    """Detailed result for a single pick"""

    pick_id: UUID
    status: str = Field(description="win or loss")
    ftd_points: int = Field(description="Points from FTD prediction")
    attd_points: int = Field(description="Points from ATTD prediction")
    total_points: int = Field(description="Total points earned")
    actual_first_td_scorer: Optional[UUID] = Field(
        description="Player who scored first TD"
    )
    all_td_scorers: list[UUID] = Field(description="All players who scored TDs")
    scored_at: Optional[datetime] = Field(description="When pick was graded")

    class Config:
        from_attributes = True


class GameResultResponse(BaseModel):
    """Scoring results for a game"""

    game_id: UUID
    first_td_scorer: Optional[UUID] = Field(description="First TD scorer")
    all_td_scorers: list[UUID] = Field(description="All TD scorers")
    scored_at: Optional[datetime] = Field(description="When game was scored")
    picks_graded: int = Field(description="Number of picks graded")
    is_manually_scored: bool = Field(description="Whether manually scored by admin")

    class Config:
        from_attributes = True


class ManualScoringRequest(BaseModel):
    """Request to manually score a game"""

    first_td_scorer: Optional[UUID] = Field(description="First TD scorer player ID")
    all_td_scorers: list[UUID] = Field(description="All TD scorer player IDs")


class OverridePickRequest(BaseModel):
    """Request to override a pick's score"""

    status: str = Field(description="win or loss")
    ftd_points: int = Field(ge=0, le=3, description="FTD points (0 or 3)")
    attd_points: int = Field(ge=0, le=1, description="ATTD points (0 or 1)")
