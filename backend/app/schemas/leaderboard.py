"""Leaderboard schemas"""

from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, List, Literal


class Streak(BaseModel):
    """Current streak information"""

    type: Literal["win", "loss", "none"]
    count: int = Field(ge=0)


class WeekPerformance(BaseModel):
    """Weekly performance breakdown"""

    week: int = Field(ge=1, le=18)
    points: int = Field(ge=0)
    wins: int = Field(ge=0)
    losses: int = Field(ge=0)
    rank: int = Field(ge=1)


class LeaderboardEntry(BaseModel):
    """Leaderboard entry for a user"""

    rank: int = Field(ge=1)
    user_id: UUID
    username: str
    display_name: str
    total_points: int = Field(ge=0)
    ftd_points: int = Field(ge=0)
    attd_points: int = Field(ge=0)
    wins: int = Field(ge=0)
    losses: int = Field(ge=0)
    pending: int = Field(ge=0)
    win_percentage: float = Field(ge=0.0, le=100.0)
    is_tied: bool = False  # True if tied with previous rank

    class Config:
        from_attributes = True


class UserStats(BaseModel):
    """Detailed user statistics"""

    user_id: UUID
    username: str
    display_name: str

    # Overall stats
    total_points: int = Field(ge=0)
    total_wins: int = Field(ge=0)
    total_losses: int = Field(ge=0)
    total_pending: int = Field(ge=0)
    win_percentage: float = Field(ge=0.0, le=100.0)
    current_rank: int = Field(ge=1)

    # FTD stats
    ftd_wins: int = Field(ge=0)
    ftd_losses: int = Field(ge=0)
    ftd_points: int = Field(ge=0)
    ftd_percentage: float = Field(ge=0.0, le=100.0)

    # ATTD stats
    attd_wins: int = Field(ge=0)
    attd_losses: int = Field(ge=0)
    attd_points: int = Field(ge=0)
    attd_percentage: float = Field(ge=0.0, le=100.0)

    # Weekly performance
    best_week: Optional[WeekPerformance] = None
    worst_week: Optional[WeekPerformance] = None
    weekly_breakdown: List[WeekPerformance] = []

    # Streaks
    current_streak: Streak
    longest_win_streak: int = Field(ge=0)
    longest_loss_streak: int = Field(ge=0)

    class Config:
        from_attributes = True
