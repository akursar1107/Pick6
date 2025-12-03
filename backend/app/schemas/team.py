"""Team schemas"""

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class TeamBase(BaseModel):
    """Base team schema"""
    team_name: str
    team_abbreviation: str
    league: str = "NFL"
    logo_url: Optional[str] = None


class TeamCreate(TeamBase):
    """Schema for creating a team"""
    pass


class TeamUpdate(BaseModel):
    """Schema for updating a team"""
    team_name: Optional[str] = None
    team_abbreviation: Optional[str] = None
    logo_url: Optional[str] = None


class TeamResponse(TeamBase):
    """Schema for team response"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

