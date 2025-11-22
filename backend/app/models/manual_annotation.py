"""
Manual Annotation Model

Stores human-reviewed PHI annotations for continuous model improvement.
Supports human-in-the-loop workflow to catch missed PHI (8% safety net).
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.base_class import Base


class ManualAnnotation(Base):
    """
    Manual PHI annotation created by human reviewer.

    Attributes:
        annotation_id: Unique annotation identifier
        note_id: Note identifier from source system
        user_id: User who created the annotation
        text: Annotated PHI text (max 500 characters)
        start_offset: Character start position in note
        end_offset: Character end position in note
        entity_type: PHI category (NAME, DOB, MRN, etc.)
        confidence: Annotator confidence (0.0-1.0)
        created_at: Creation timestamp
        updated_at: Last update timestamp
        is_active: Soft delete flag
    """

    __tablename__ = "manual_annotations"

    annotation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    note_id = Column(String(255), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    text = Column(String(500), nullable=False)
    start_offset = Column(Integer, nullable=False)
    end_offset = Column(Integer, nullable=False)
    entity_type = Column(String(50), nullable=False, index=True)
    confidence = Column(Float, nullable=False, default=1.0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    # Relationships
    user = relationship("User", back_populates="manual_annotations")

    def __repr__(self) -> str:
        return (
            f"<ManualAnnotation("
            f"annotation_id={self.annotation_id}, "
            f"note_id={self.note_id}, "
            f"entity_type={self.entity_type}, "
            f"text={self.text[:20]}...)"
            f")>"
        )

    @property
    def length(self) -> int:
        """Calculate annotation length in characters."""
        return self.end_offset - self.start_offset

    def to_dict(self) -> dict:
        """Convert annotation to dictionary representation."""
        return {
            "annotation_id": str(self.annotation_id),
            "note_id": self.note_id,
            "user_id": str(self.user_id),
            "text": self.text,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "entity_type": self.entity_type,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active,
        }
