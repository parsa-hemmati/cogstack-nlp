"""
De-identification Job Model
Tracks batch de-identification jobs
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class DeidentificationJob(Base):
    """
    De-identification batch job.

    Tracks batch de-identification operations with:
    - Job status (pending, processing, completed, failed, cancelled)
    - Progress tracking (total_notes, processed_notes, error_count)
    - Method used (removal, replacement, generalization)
    - Email notifications
    """

    __tablename__ = "deidentification_jobs"

    # Primary key
    job_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # User who created the job
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Job status
    status = Column(String(20), nullable=False, default="pending", index=True)
    # Valid values: pending, processing, completed, failed, cancelled

    # De-identification method
    method = Column(String(20), nullable=False, default="removal")
    # Valid values: removal, replacement, generalization

    # Progress tracking
    total_notes = Column(Integer, nullable=False)
    processed_notes = Column(Integer, nullable=False, default=0)
    error_count = Column(Integer, nullable=False, default=0)

    # Notification
    notify_email = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="deidentification_jobs")
    entities = relationship("PHIEntity", back_populates="job", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<DeidentificationJob(id={self.job_id}, status={self.status}, progress={self.processed_notes}/{self.total_notes})>"

    @property
    def progress_percentage(self) -> float:
        """Calculate job progress percentage."""
        if self.total_notes == 0:
            return 0.0
        return (self.processed_notes / self.total_notes) * 100

    @property
    def error_rate(self) -> float:
        """Calculate job error rate."""
        if self.processed_notes == 0:
            return 0.0
        return (self.error_count / self.processed_notes) * 100

    # Composite indexes
    __table_args__ = (
        Index("ix_deidentification_jobs_user_status", "user_id", "status"),
    )
