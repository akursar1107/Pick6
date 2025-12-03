"""Game model"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum
from app.db.base import Base


class GameStatus(str, enum.Enum):
    """Game status enum"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SUSPENDED = "suspended"


class GameType(str, enum.Enum):
    """Game type enum"""
    TNF = "TNF"  # Thursday Night Football
    SNF = "SNF"  # Sunday Night Football
    MNF = "MNF"  # Monday Night Football
    SATURDAY = "Saturday"
    SUNDAY_EARLY = "Sunday_early"
    SUNDAY_MAIN = "Sunday_main"


class Game(Base):
    """Game model"""
    __tablename__ = "games"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id = Column(String, unique=True, nullable=False, index=True)  # BallDontLie ID
    season_year = Column(Integer, nullable=False)
    week_number = Column(Integer, nullable=False)
    game_type = Column(Enum(GameType), nullable=False)
    
    home_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    
    game_date = Column(DateTime(timezone=True), nullable=False)
    kickoff_time = Column(DateTime(timezone=True), nullable=False)
    
    status = Column(Enum(GameStatus), default=GameStatus.SCHEDULED)
    
    # Results
    first_td_scorer_player_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=True)
    final_score_home = Column(Integer, nullable=True)
    final_score_away = Column(Integer, nullable=True)
    
    # Snapshot data from API
    home_team_data = Column(JSONB, nullable=True)
    away_team_data = Column(JSONB, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

