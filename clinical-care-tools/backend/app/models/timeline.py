"""
Timeline Module Models

Models for the timeline visualization module.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4
from uuid import UUID as PyUUID

from sqlalchemy import DateTime, Index, String, Boolean, Text, Integer, CheckConstraint, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
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
    id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    task_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    user_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

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


class TimelineFilter(Base):
    """
    Saved timeline filter preset.
    
    Corresponds to timeline_filters table created in migration 004.
    """
    
    __tablename__ = "timeline_filters"
    
    id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    filters: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='timeline_filters_user_name_unique'),
        CheckConstraint("LENGTH(name) >= 3", name='timeline_filters_name_min_length'),
    )


class TimelineExport(Base):
    """
    Timeline export record.
    
    Corresponds to timeline_exports table created in migration 004.
    """
    
    __tablename__ = "timeline_exports"
    
    id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    patient_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    user_id: Mapped[Optional[PyUUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    format: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="processing")
    filters: Mapped[dict] = mapped_column(JSONB, nullable=False)
    options: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    download_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    audit_log_id: Mapped[Optional[PyUUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    
    __table_args__ = (
        CheckConstraint("format IN ('pdf', 'fhir', 'json')", name='timeline_exports_format_check'),
        CheckConstraint("status IN ('processing', 'completed', 'failed')", name='timeline_exports_status_check'),
    )
