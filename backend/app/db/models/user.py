"""User model"""

from sqlalchemy import Column, String, Boolean, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
import uuid
from app.db.base import Base


class User(Base):
    """User model"""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=True)
    display_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # WebAuthn fields
    webauthn_credential_id = Column(String, nullable=True)
    webauthn_public_key = Column(String, nullable=True)

    # Scoring fields
    total_score = Column(Integer, default=0, nullable=False)  # Sum of all points
    total_wins = Column(Integer, default=0, nullable=False)  # Count of winning picks
    total_losses = Column(Integer, default=0, nullable=False)  # Count of losing picks

    # Relationships
    import_jobs = relationship("ImportJob", back_populates="admin_user")

    @hybrid_property
    def win_percentage(self) -> float:
        """Calculate win percentage"""
        total_picks = self.total_wins + self.total_losses
        if total_picks == 0:
            return 0.0
        return (self.total_wins / total_picks) * 100
