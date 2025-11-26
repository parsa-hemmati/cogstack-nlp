"""CDS Clinical Guidelines model for storing evidence-based recommendations."""

import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, String, Text, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.db.base_class import Base


class CDSGuideline(Base):
    """Clinical decision support guideline from authoritative sources.

    Stores evidence-based clinical guidelines from ADA (American Diabetes Association),
    AHA (American Heart Association), USPSTF (US Preventive Services Task Force),
    and NICE (National Institute for Health and Care Excellence).

    Guidelines are matched to patient conditions using ICD-10 or SNOMED CT codes
    and provide clinical recommendations with evidence levels.

    Attributes:
        id: Unique guideline ID
        guideline_source: Source organization ('ADA', 'AHA', 'USPSTF', 'NICE')
        guideline_name: Guideline title/name
        condition_code: ICD-10 or SNOMED CT condition code
        recommendation: Clinical recommendation text
        evidence_level: Evidence strength ('A' = strong, 'B' = moderate, 'C' = weak)
        rationale: Supporting evidence and rationale
        last_updated: Date guideline was last updated by source organization
        created_at: Date record was created in database
    """

    __tablename__ = "cds_guidelines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guideline_source = Column(String(50), nullable=False, comment='Guideline source: ADA, AHA, USPSTF, NICE')
    guideline_name = Column(String(255), nullable=False, comment='Guideline name/title')
    condition_code = Column(String(50), nullable=False, comment='ICD-10 or SNOMED CT condition code')
    recommendation = Column(Text, nullable=False, comment='Clinical recommendation text')
    evidence_level = Column(String(10), nullable=False, comment='Evidence level: A (strong), B (moderate), C (weak)')
    rationale = Column(Text, nullable=False, comment='Rationale and supporting evidence')
    last_updated = Column(DateTime(timezone=True), nullable=False, comment='Date guideline was last updated by source')
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, comment='Date record was created in database')

    # Indexes and constraints are defined in Alembic migration 015
    # This __table_args__ is just for documentation (actual constraints are in DB)
    __table_args__ = (
        # Unique constraint: prevent duplicate guidelines for same source/name/condition
        Index('uq_cds_guidelines_source_name_condition', 'guideline_source', 'guideline_name', 'condition_code', unique=True),

        # Index for fast lookups by condition code (primary query pattern)
        Index('ix_cds_guidelines_condition_code', 'condition_code'),

        # Additional indexes for query patterns
        Index('ix_cds_guidelines_source', 'guideline_source'),
        Index('ix_cds_guidelines_evidence_level', 'evidence_level'),

        # Check constraints
        CheckConstraint(
            "guideline_source IN ('ADA', 'AHA', 'USPSTF', 'NICE')",
            name='ck_cds_guidelines_source'
        ),
        CheckConstraint(
            "evidence_level IN ('A', 'B', 'C')",
            name='ck_cds_guidelines_evidence_level'
        ),
    )

    def __repr__(self):
        return f"<CDSGuideline(id={self.id}, source={self.guideline_source}, name={self.guideline_name}, condition={self.condition_code}, evidence={self.evidence_level})>"

    def to_dict(self):
        """Convert model to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "guideline_source": self.guideline_source,
            "guideline_name": self.guideline_name,
            "condition_code": self.condition_code,
            "recommendation": self.recommendation,
            "evidence_level": self.evidence_level,
            "rationale": self.rationale,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
