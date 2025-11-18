"""Search Analytics model for tracking search queries."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class SearchAnalytic(Base):
    """
    Search analytics tracking model.

    Tracks all search queries for:
    - Popular query analysis
    - Zero-result query identification
    - Click-through rate measurement
    - Performance monitoring
    """

    __tablename__ = "search_analytics"

    id: UUID = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid(),
    )

    user_id: UUID = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    query: str = Column(Text, nullable=False)

    filters: dict = Column(JSONB, nullable=True)

    total_results: int = Column(Integer, nullable=False)

    page: int = Column(Integer, nullable=False, default=1)

    execution_time_ms: Optional[int] = Column(Integer, nullable=True)

    clicked_result_id: Optional[UUID] = Column(
        PGUUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
    )

    clicked_result_rank: Optional[int] = Column(Integer, nullable=True)

    session_id: Optional[UUID] = Column(PGUUID(as_uuid=True), nullable=True)

    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        index=True,
    )

    # Relationships
    user = relationship("User", back_populates="search_analytics")
    clicked_document = relationship("Document", foreign_keys=[clicked_result_id])

    def __repr__(self) -> str:
        return (
            f"<SearchAnalytic(id={self.id}, query='{self.query}', "
            f"results={self.total_results}, user_id={self.user_id})>"
        )
