"""Player schemas"""

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class PlayerBase(BaseModel):
    """Base player schema"""
    first_name: str
    last_name: str
    team_id: UUID
    position: Optional[str] = None
    jersey_number: Optional[int] = None
    league: str = "NFL"
    is_active: bool = True
    external_id: Optional[str] = None


class PlayerCreate(PlayerBase):
    """Schema for creating a player"""
    pass


class PlayerUpdate(BaseModel):
    """Schema for updating a player"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    team_id: Optional[UUID] = None
    position: Optional[str] = None
    jersey_number: Optional[int] = None
    is_active: Optional[bool] = None


class PlayerResponse(PlayerBase):
    """Schema for player response"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

