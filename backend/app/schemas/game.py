"""Game schemas"""

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class GameBase(BaseModel):
    """Base game schema"""

    external_id: str
    season_year: int
    week_number: int
    game_type: str
    home_team_id: UUID
    away_team_id: UUID
    game_date: datetime
    kickoff_time: datetime


class GameCreate(GameBase):
    """Schema for creating a game"""

    pass


class GameResponse(GameBase):
    """Schema for game response"""

    id: UUID
    status: str
    first_td_scorer_player_id: Optional[UUID] = None
    final_score_home: Optional[int] = None
    final_score_away: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PickInfo(BaseModel):
    """Schema for pick information in game response"""

    id: UUID
    player_name: str


class GameWithPickResponse(BaseModel):
    """
    Schema for available games with user's pick information.
    Requirements: 7.2, 8.1, 8.2
    """

    id: UUID
    home_team: str
    away_team: str
    kickoff_time: datetime
    week_number: int
    season: int  # Added for admin filtering
    status: str  # Added for admin visibility
    user_pick: Optional[PickInfo] = None

    class Config:
        from_attributes = True
