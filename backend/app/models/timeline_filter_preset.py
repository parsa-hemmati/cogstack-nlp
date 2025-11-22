"""Timeline filter preset model for saving filter configurations."""

import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class TimelineFilterPreset(Base):
    """Saved filter preset for timeline view.

    Allows users to save frequently used filter combinations
    (concept CUIs, date ranges, meta-annotations, document types)
    for quick access.

    Attributes:
        id: Unique preset ID
        user_id: Owner user ID (foreign key to users table)
        name: Preset name (e.g., "Diabetes Management", "Recent Hypertension")
        filters: Serialized TimelineFilterRequest (JSONB)
        is_default: Whether this is the user's default preset
        created_at: Creation timestamp
        updated_at: Last update timestamp
        user: Relationship to User model
    """

    __tablename__ = "timeline_filter_presets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    filters = Column(JSON, nullable=False)  # uses JSONB in PostgreSQL
    is_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="timeline_filter_presets")

    # Indexes defined in Alembic migration
    __table_args__ = (
        Index("idx_timeline_filter_presets_user_id", "user_id"),
        Index("idx_timeline_filter_presets_user_name", "user_id", "name", unique=True),
        Index("idx_timeline_filter_presets_user_default", "user_id", "is_default"),
    )

    def __repr__(self):
        return f"<TimelineFilterPreset(id={self.id}, user_id={self.user_id}, name={self.name}, is_default={self.is_default})>"
