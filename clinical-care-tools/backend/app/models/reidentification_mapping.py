"""Re-identification Mapping Model (Sprint 4, Phase 4.3)"""

from sqlalchemy import Column, String, DateTime, LargeBinary, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base_class import Base


class ReidentificationMapping(Base):
    """Re-identification mapping (encrypted)

    Stores encrypted mapping from original PHI to surrogates.
    Enables re-identification for research purposes.

    **Security**: original_value_encrypted is encrypted using pgcrypto.
    """

    __tablename__ = "reidentification_mappings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Document reference
    document_id = Column(
        UUID(as_uuid=True),
        # ForeignKey("documents.id"),  # TODO: Uncomment when documents table exists
        nullable=False,
        index=True
    )

    # Entity type (PERSON, DATE, ID, etc.)
    entity_type = Column(String(50), nullable=False)

    # Encrypted original value (encrypted using pgcrypto)
    original_value_encrypted = Column(
        LargeBinary,
        nullable=False,
        comment="Original PHI value (encrypted with pgcrypto)"
    )

    # Surrogate value (not encrypted, used for replacement)
    surrogate_value = Column(String(200), nullable=False, index=True)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    # document = relationship("Document", back_populates="reid_mappings")

    def __repr__(self):
        return (
            f"<ReidentificationMapping(id={self.id}, "
            f"document={self.document_id}, "
            f"type={self.entity_type}, "
            f"surrogate={self.surrogate_value})>"
        )


class DeidentificationJob(Base):
    """Batch de-identification job tracking (Sprint 4, Phase 4.4)"""

    __tablename__ = "deidentification_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # User who created job
    user_id = Column(
        UUID(as_uuid=True),
        # ForeignKey("users.id"),  # TODO: Uncomment when users table exists
        nullable=False,
        index=True
    )

    # Job configuration
    redaction_mode = Column(String(20), nullable=False)
    store_mapping = Column(String(5), nullable=False, default="true")  # "true" or "false" as string

    # Job status
    status = Column(
        String(20),
        default="pending",
        nullable=False,
        index=True,
        comment="Status: pending, processing, completed, failed"
    )

    # Progress tracking
    total_documents = Column(Integer, nullable=False)
    processed_documents = Column(Integer, default=0, nullable=False)
    failed_documents = Column(Integer, default=0, nullable=False)

    # Error tracking
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    # user = relationship("User")

    def __repr__(self):
        return (
            f"<DeidentificationJob(id={self.id}, "
            f"status={self.status}, "
            f"progress={self.processed_documents}/{self.total_documents})>"
        )
