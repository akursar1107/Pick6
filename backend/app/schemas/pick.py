"""Pick schemas"""

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class PickBase(BaseModel):
    """Base pick schema"""
    game_id: UUID
    pick_type: str
    player_id: UUID
    snapshot_odds: Optional[str] = None


class PickCreate(PickBase):
    """Schema for creating a pick"""
    pass


class PickUpdate(BaseModel):
    """Schema for updating a pick"""
    player_id: Optional[UUID] = None
    snapshot_odds: Optional[str] = None


class PickResponse(PickBase):
    """Schema for pick response"""
    id: UUID
    user_id: UUID
    status: str
    is_manual_override: bool
    settled_at: Optional[datetime] = None
    pick_submitted_at: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

