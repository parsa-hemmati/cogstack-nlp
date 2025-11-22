"""
Timeline Module Models

Models for the timeline visualization module.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.orm import mapped_column, Mapped

from app.models import Base


class TimelineView(Base):
    """
    Timeline view model for the timeline module.

    Attributes:
        id: Unique timeline view identifier (UUID)
        task_id: Reference to task (from tasks table)
        user_id: User viewing the timeline
        patient_id: Patient identifier (MRN or NHS number)
        viewed_at: When the timeline was viewed
    """

    __tablename__ = "timeline_views"

    # Primary Key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Foreign Keys
    task_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(nullable=False, index=True)

    # Patient Reference
    patient_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Timestamp
    viewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())

    # Indexes
    __table_args__ = (
        Index("idx_timeline_views_task", "task_id"),
        Index("idx_timeline_views_user", "user_id"),
        Index("idx_timeline_views_patient", "patient_id"),
    )

    def __repr__(self) -> str:
        """String representation of TimelineView."""
        return f"<TimelineView(id={self.id}, patient={self.patient_id}, user={self.user_id})>"
