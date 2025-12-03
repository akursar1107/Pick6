"""Pick model"""

from sqlalchemy import Column, String, ForeignKey, DateTime, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum
from app.db.base import Base


class PickType(str, enum.Enum):
    """Pick type enum"""
    FTD = "FTD"  # First Touchdown
    ATTD = "ATTD"  # Anytime Touchdown


class PickResult(str, enum.Enum):
    """Pick result enum"""
    PENDING = "pending"
    WIN = "win"
    LOSS = "loss"
    VOID = "void"


class Pick(Base):
    """Pick model"""
    __tablename__ = "picks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False, index=True)
    
    pick_type = Column(Enum(PickType), nullable=False)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False)
    
    snapshot_odds = Column(String, nullable=True)  # Store odds at time of pick
    
    status = Column(Enum(PickResult), default=PickResult.PENDING)
    is_manual_override = Column(Boolean, default=False)  # True if Commissioner fixed it
    
    settled_at = Column(DateTime(timezone=True), nullable=True)
    pick_submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

