"""ImportJob model"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum
from app.db.base import Base


class ImportJobStatus(str, enum.Enum):
    """Import job status enum"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ImportJob(Base):
    """Tracks import operations"""

    __tablename__ = "import_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    season = Column(Integer, nullable=False, index=True)
    weeks = Column(ARRAY(Integer), nullable=True)
    grade_games = Column(Boolean, default=False, nullable=False)

    status = Column(
        Enum(ImportJobStatus),
        nullable=False,
        default=ImportJobStatus.PENDING,
        index=True,
    )

    # Progress tracking
    current_step = Column(String(200), nullable=True)
    games_processed = Column(Integer, default=0, nullable=False)
    total_games = Column(Integer, default=0, nullable=False)

    # Statistics
    teams_created = Column(Integer, default=0, nullable=False)
    players_created = Column(Integer, default=0, nullable=False)
    games_created = Column(Integer, default=0, nullable=False)
    games_updated = Column(Integer, default=0, nullable=False)
    games_graded = Column(Integer, default=0, nullable=False)

    # Error tracking
    errors = Column(ARRAY(String), default=list, nullable=False)

    # Audit fields
    admin_user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    started_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    admin_user = relationship("User", back_populates="import_jobs")
