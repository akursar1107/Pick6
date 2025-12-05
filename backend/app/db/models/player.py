"""Player model"""

from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base


class Player(Base):
    """Player model"""

    __tablename__ = "players"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False, index=True)
    team_id = Column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False, index=True
    )
    position = Column(String, nullable=True)  # QB, RB, WR, etc.
    jersey_number = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    # team = relationship("Team", back_populates="players")
