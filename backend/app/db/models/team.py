"""Team model"""

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base


class Team(Base):
    """Team model"""

    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    abbreviation = Column(String, nullable=False)
    city = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    # home_games = relationship("Game", foreign_keys="Game.home_team_id", back_populates="home_team")
    # away_games = relationship("Game", foreign_keys="Game.away_team_id", back_populates="away_team")
    # players = relationship("Player", back_populates="team")
