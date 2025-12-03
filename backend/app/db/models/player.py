"""Player model"""

from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum
from app.db.base import Base
from app.db.models.team import League


class Player(Base):
    """Player model"""
    __tablename__ = "players"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False, index=True)
    position = Column(String, nullable=True)  # QB, RB, WR, etc.
    jersey_number = Column(Integer, nullable=True)
    league = Column(Enum(League), default=League.NFL, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # External ID from BallDontLie or other API
    external_id = Column(String, nullable=True, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    # team = relationship("Team", back_populates="players")

