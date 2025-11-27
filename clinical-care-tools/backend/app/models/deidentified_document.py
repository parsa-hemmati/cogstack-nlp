"""De-identified Document Model (Sprint 4)"""

from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base_class import Base


class DeidentifiedDocument(Base):
    """De-identified document storage

    Stores de-identified copies of clinical documents.
    Original documents are NOT modified.
    """

    __tablename__ = "deidentified_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Link to original document
    original_document_id = Column(
        UUID(as_uuid=True),
        # ForeignKey("documents.id"),  # TODO: Uncomment when documents table exists
        nullable=False,
        index=True
    )

    # Redaction mode used
    redaction_mode = Column(
        String(20),
        nullable=False,
        comment="Redaction mode: mask, surrogate, remove"
    )

    # De-identified text
    redacted_text = Column(Text, nullable=False)

    # Metadata
    entities_redacted = Column(Integer, nullable=False, default=0)

    # Audit fields
    created_by = Column(
        UUID(as_uuid=True),
        # ForeignKey("users.id"),  # TODO: Uncomment when users table exists
        nullable=False
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    # original_document = relationship("Document", back_populates="deidentified_versions")
    # created_by_user = relationship("User")

    def __repr__(self):
        return (
            f"<DeidentifiedDocument(id={self.id}, "
            f"original={self.original_document_id}, "
            f"mode={self.redaction_mode}, "
            f"entities={self.entities_redacted})>"
        )
