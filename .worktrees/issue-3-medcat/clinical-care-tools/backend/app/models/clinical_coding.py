"""Clinical Coding Models (Sprint 5)"""

from sqlalchemy import Column, String, Text, Float, Integer, Boolean, ForeignKey, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base_class import Base


class ICD10Library(Base):
    """ICD-10-CM code library (reference data)"""

    __tablename__ = "icd10_library"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(10), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(200), nullable=True)

    # ICD-10 metadata
    billable = Column(Boolean, default=True)
    valid_for_coding = Column(Boolean, default=True)

    # Version tracking
    version = Column(String(10), default="2024")  # CMS version year
    effective_date = Column(DateTime, nullable=True)

    # Relationships
    # coding_assignments = relationship("CodingAssignment", back_populates="icd10_code")

    # Indexes for full-text search
    __table_args__ = (
        Index('idx_icd10_code', 'code'),
        Index('idx_icd10_description_gin', 'description', postgresql_using='gin',
              postgresql_ops={'description': 'gin_trgm_ops'}),
    )

    def __repr__(self):
        return f"<ICD10Library(code={self.code}, description={self.description[:50]})>"


class CodingAssignment(Base):
    """ICD-10 code assignment to document"""

    __tablename__ = "coding_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Document reference
    document_id = Column(
        UUID(as_uuid=True),
        # ForeignKey("documents.id"),  # TODO: Uncomment when documents table exists
        nullable=False,
        index=True
    )

    # ICD-10 code
    icd10_code = Column(String(10), nullable=False, index=True)
    # icd10_code_id = Column(UUID(as_uuid=True), ForeignKey("icd10_library.id"), nullable=True)

    # Assignment metadata
    is_primary = Column(Boolean, default=False, comment="Is this the primary diagnosis code?")
    source = Column(String(20), nullable=False, comment="Source: ai, manual, approved")

    # AI-specific fields
    confidence = Column(Float, nullable=True, comment="AI confidence score (if source=ai)")
    evidence = Column(Text, nullable=True, comment="Text evidence (if source=ai)")

    # Audit fields
    assigned_by = Column(
        UUID(as_uuid=True),
        # ForeignKey("users.id"),  # TODO: Uncomment when users table exists
        nullable=False
    )
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    # document = relationship("Document", back_populates="coding_assignments")
    # icd10 = relationship("ICD10Library", back_populates="coding_assignments")
    # assigned_by_user = relationship("User")

    def __repr__(self):
        return (
            f"<CodingAssignment(document={self.document_id}, "
            f"code={self.icd10_code}, source={self.source})>"
        )


class CodingMetric(Base):
    """Coding quality metrics (Sprint 5)"""

    __tablename__ = "coding_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Time period
    date = Column(DateTime, nullable=False, index=True)
    period = Column(String(20), default="daily", comment="Period: daily, weekly, monthly")

    # Coder performance
    coder_id = Column(
        UUID(as_uuid=True),
        # ForeignKey("users.id"),  # TODO: Uncomment when users table exists
        nullable=True,
        index=True
    )

    # Volume metrics
    documents_coded = Column(Integer, default=0)
    codes_assigned = Column(Integer, default=0)
    avg_codes_per_document = Column(Float, default=0.0)

    # AI performance
    ai_suggestions_accepted = Column(Integer, default=0)
    ai_suggestions_rejected = Column(Integer, default=0)
    ai_precision = Column(Float, nullable=True, comment="AI precision (accepted / total)")
    ai_recall = Column(Float, nullable=True, comment="AI recall (accepted / all codes)")

    # Time metrics
    avg_time_per_document = Column(Float, nullable=True, comment="Average time in seconds")
    total_coding_time = Column(Float, nullable=True, comment="Total time in seconds")

    # Quality metrics
    code_validation_errors = Column(Integer, default=0)
    duplicate_codes = Column(Integer, default=0)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    # coder = relationship("User")

    def __repr__(self):
        return (
            f"<CodingMetric(date={self.date}, coder={self.coder_id}, "
            f"docs={self.documents_coded})>"
        )
