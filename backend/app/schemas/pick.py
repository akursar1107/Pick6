"""Pick schemas"""

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class PickBase(BaseModel):
    """Base pick schema"""

    game_id: UUID
    player_id: UUID


class PickCreate(PickBase):
    """
    Schema for creating a pick.
    Requirements: 1.1
    """

    pass


class PickUpdate(BaseModel):
    """
    Schema for updating a pick.
    Requirements: 3.1
    """

    player_id: UUID


class GameInfo(BaseModel):
    """Nested game information in pick response"""

    id: UUID
    home_team: str
    away_team: str
    kickoff_time: datetime
    week_number: int

    class Config:
        from_attributes = True


class PlayerInfo(BaseModel):
    """Nested player information in pick response"""

    id: UUID
    name: str
    team: str
    position: Optional[str] = None

    class Config:
        from_attributes = True


class PickResponse(BaseModel):
    """
    Schema for pick response with nested game and player data.
    Requirements: 2.2
    """

    id: UUID
    user_id: UUID
    game_id: UUID
    player_id: UUID
    status: str
    is_manual_override: bool
    settled_at: Optional[datetime] = None
    pick_submitted_at: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None
    game: Optional[GameInfo] = None
    player: Optional[PlayerInfo] = None

    class Config:
        from_attributes = True
