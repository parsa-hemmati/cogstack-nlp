"""
SavedSearch Model

SQLAlchemy ORM model for saved_searches table.
Stores user-defined reusable search queries with filters.
"""
import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, String, Text, DateTime, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class SavedSearch(Base):
    """
    Saved search query model for reusable complex searches.

    Attributes:
        id: UUID primary key
        user_id: Foreign key to users table
        name: Search name (max 100 characters)
        description: Optional description of what this search finds
        query: Full-text search query string
        filters: JSONB field for meta-annotation filters (Negation, Temporality, etc.)
        is_shared: Whether search is shared with other users
        execution_count: Number of times this search has been run
        created_at: When search was created
        updated_at: When search was last modified

    Relationships:
        user: The user who created this search

    Constraints:
        Unique (user_id, name): User cannot have duplicate search names
    """

    __tablename__ = "saved_searches"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Foreign key to users
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Search metadata
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # Search parameters
    query = Column(Text, nullable=False)  # Full-text search query
    filters = Column(JSONB, nullable=True)  # Meta-annotation filters, date ranges, etc.

    # Sharing and usage tracking
    is_shared = Column(Boolean, nullable=False, default=False, index=True)
    execution_count = Column(Integer, nullable=False, default=0)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="saved_searches")

    # Table constraints
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_saved_searches_user_name"),
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<SavedSearch(id={self.id}, user_id={self.user_id}, name='{self.name}')>"

    def to_dict(self) -> dict:
        """
        Convert SavedSearch to dictionary for serialization.

        Returns:
            Dictionary representation of saved search
        """
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "name": self.name,
            "description": self.description,
            "query": self.query,
            "filters": self.filters,
            "is_shared": self.is_shared,
            "execution_count": self.execution_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
