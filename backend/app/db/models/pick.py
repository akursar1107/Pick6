"""Pick model"""

from sqlalchemy import (
    Column,
    ForeignKey,
    DateTime,
    Enum,
    Boolean,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum
from app.db.base import Base


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
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    game_id = Column(
        UUID(as_uuid=True), ForeignKey("games.id"), nullable=False, index=True
    )
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False)

    status = Column(Enum(PickResult), default=PickResult.PENDING)
    is_manual_override = Column(Boolean, default=False)  # True if Commissioner fixed it

    settled_at = Column(DateTime(timezone=True), nullable=True)
    pick_submitted_at = Column(DateTime(timezone=True), server_default=func.now())

    # Scoring fields
    scored_at = Column(DateTime(timezone=True), nullable=True)  # When pick was graded
    ftd_points = Column(Integer, default=0, nullable=False)  # Points from FTD (0 or 3)
    attd_points = Column(
        Integer, default=0, nullable=False
    )  # Points from ATTD (0 or 1)
    total_points = Column(
        Integer, default=0, nullable=False
    )  # ftd_points + attd_points
    override_by_user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )  # Admin who overrode
    override_at = Column(
        DateTime(timezone=True), nullable=True
    )  # When override happened

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (UniqueConstraint("user_id", "game_id", name="uq_user_game_pick"),)
