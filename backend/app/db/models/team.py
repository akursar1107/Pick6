"""Team model"""

from sqlalchemy import Column, String, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum
from app.db.base import Base


class League(str, enum.Enum):
    """League enum for future multi-sport support"""
    NFL = "NFL"
    NBA = "NBA"
    NHL = "NHL"
    MLB = "MLB"
    NCAAF = "NCAAF"


class Team(Base):
    """Team model"""
    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_name = Column(String, nullable=False, index=True)
    team_abbreviation = Column(String, nullable=False, unique=True, index=True)
    league = Column(Enum(League), default=League.NFL, nullable=False)
    logo_url = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    # home_games = relationship("Game", foreign_keys="Game.home_team_id", back_populates="home_team")
    # away_games = relationship("Game", foreign_keys="Game.away_team_id", back_populates="away_team")
    # players = relationship("Player", back_populates="team")

