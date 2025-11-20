"""
SearchAnalytics Model

SQLAlchemy ORM model for search_analytics table.
Tracks query performance, result quality, and user behavior.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, Text, DateTime, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class SearchAnalytics(Base):
    """
    Search analytics model for tracking query performance and user behavior.

    Attributes:
        id: UUID primary key
        user_id: Foreign key to users table
        query: Raw search query string
        filters: JSONB field for applied filters
        results_count: Number of results returned
        execution_time_ms: Query execution time in milliseconds
        clicked_documents: Array of document UUIDs that user clicked
        created_at: When search was executed

    Relationships:
        user: The user who executed this search

    Use Cases:
        - Query performance monitoring (slow query detection)
        - Search quality tracking (zero-result queries)
        - User behavior analysis (click-through rates)
        - Query autocomplete/suggestions (GIN index on query field)
    """

    __tablename__ = "search_analytics"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Foreign key to users
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Search parameters
    query = Column(Text, nullable=False)  # Raw search query
    filters = Column(JSONB, nullable=True)  # Applied filters

    # Performance metrics
    results_count = Column(Integer, nullable=False, index=True)  # Number of results returned
    execution_time_ms = Column(Integer, nullable=False)  # Query execution time

    # User behavior
    clicked_documents = Column(ARRAY(UUID(as_uuid=True)), nullable=True)  # Document IDs user clicked

    # Timestamp
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", backref="search_analytics")

    # Table indexes (GIN index on query created via migration 011)
    __table_args__ = (
        Index("ix_search_analytics_created_at_desc", "created_at", postgresql_using="btree", postgresql_ops={"created_at": "DESC"}),
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<SearchAnalytics(id={self.id}, user_id={self.user_id}, query='{self.query[:30]}...', results={self.results_count})>"

    def to_dict(self) -> dict:
        """
        Convert SearchAnalytics to dictionary for serialization.

        Returns:
            Dictionary representation of search analytics
        """
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "query": self.query,
            "filters": self.filters,
            "results_count": self.results_count,
            "execution_time_ms": self.execution_time_ms,
            "clicked_documents": [str(doc_id) for doc_id in self.clicked_documents] if self.clicked_documents else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
