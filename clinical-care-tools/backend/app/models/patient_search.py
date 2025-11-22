"""
Patient Search Module Models

Models for the patient search module.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Index, Integer, func, JSON
from sqlalchemy.orm import mapped_column, Mapped

from app.models import Base


class PatientSearchResult(Base):
    """
    Patient search result model for the patient search module.

    Attributes:
        id: Unique search result identifier (UUID)
        task_id: Reference to task (from tasks table)
        user_id: User who performed the search
        query: Search criteria as JSON
        result_count: Number of results returned
        results: Result data as JSON
        created_at: When search was performed
    """

    __tablename__ = "patient_search_results"

    # Primary Key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Foreign Keys
    task_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(nullable=False, index=True)

    # Search Data
    query: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    result_count: Mapped[int] = mapped_column(Integer, nullable=False)
    results: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())

    # Indexes
    __table_args__ = (
        Index("idx_patient_search_task", "task_id"),
        Index("idx_patient_search_user", "user_id"),
    )

    def __repr__(self) -> str:
        """String representation of PatientSearchResult."""
        return f"<PatientSearchResult(id={self.id}, task={self.task_id}, results={self.result_count})>"
