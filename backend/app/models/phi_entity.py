"""
PHI Entity Model
Tracks individual PHI entities detected during de-identification
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class PHIEntity(Base):
    """
    PHI entity detected during de-identification.

    Tracks individual PHI entities (name, date, location, etc.) with:
    - Entity type and offsets
    - Confidence score
    - Manual review status
    - Action taken (remove, replace, generalize)
    """

    __tablename__ = "phi_entities"

    # Primary key
    entity_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Foreign key to job
    job_id = Column(UUID(as_uuid=True), ForeignKey("deidentification_jobs.job_id", ondelete="CASCADE"), nullable=False, index=True)

    # Note and entity information
    note_id = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)  # NAME, DATE, LOCATION, etc.

    # Position in text
    start_offset = Column(Integer, nullable=False)
    end_offset = Column(Integer, nullable=False)

    # Confidence and review
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    manually_reviewed = Column(Boolean, nullable=False, default=False, index=True)

    # Action taken
    action = Column(String(20), nullable=False)  # remove, replace, generalize

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationship to job
    job = relationship("DeidentificationJob", back_populates="entities")

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<PHIEntity(type={self.entity_type}, confidence={self.confidence:.2f}, action={self.action})>"

    # Composite indexes
    __table_args__ = (
        Index("ix_phi_entities_job_manually_reviewed", "job_id", "manually_reviewed"),
    )
