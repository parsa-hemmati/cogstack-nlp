"""Cohort models for population health management."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import Column, String, Text, Boolean, Integer, Float, ForeignKey, DateTime, Date
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CohortDefinition(Base):
    """Cohort definition model for saved patient groups.

    Stores the query definition and criteria for patient cohorts
    used in population health analysis.

    Attributes:
        id: Unique identifier
        name: Human-readable cohort name
        description: Detailed description
        query_definition: Saved search query (ES query format)
        inclusion_criteria: Additional inclusion rules
        exclusion_criteria: Exclusion rules
        is_dynamic: Whether membership auto-updates
        is_public: Visible to all users
        patient_count: Cached member count
        last_refreshed: When membership was last updated
        created_by: User who created the cohort
    """
    __tablename__ = "cohort_definitions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    query_definition = Column(JSONB, nullable=False)
    inclusion_criteria = Column(JSONB, nullable=True)
    exclusion_criteria = Column(JSONB, nullable=True)
    is_dynamic = Column(Boolean, nullable=False, server_default='true')
    is_public = Column(Boolean, nullable=False, server_default='false')
    patient_count = Column(Integer, nullable=True)
    last_refreshed = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    memberships = relationship("CohortMembership", back_populates="cohort", cascade="all, delete-orphan")
    metrics = relationship("PopulationMetric", back_populates="cohort", cascade="all, delete-orphan")
    reports = relationship("SavedReport", back_populates="cohort")

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "query_definition": self.query_definition,
            "inclusion_criteria": self.inclusion_criteria,
            "exclusion_criteria": self.exclusion_criteria,
            "is_dynamic": self.is_dynamic,
            "is_public": self.is_public,
            "patient_count": self.patient_count,
            "last_refreshed": self.last_refreshed.isoformat() if self.last_refreshed else None,
            "created_by": str(self.created_by),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CohortMembership(Base):
    """Cohort membership model for patient-cohort associations.

    Tracks which patients belong to which cohorts.

    Attributes:
        id: Unique identifier
        cohort_id: Reference to cohort definition
        patient_id: Reference to patient
        added_at: When patient was added
        added_by: User who added (NULL if auto-added)
        match_score: Relevance score if applicable
        metadata: Why this patient matched
    """
    __tablename__ = "cohort_memberships"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    cohort_id = Column(PG_UUID(as_uuid=True), ForeignKey('cohort_definitions.id', ondelete='CASCADE'), nullable=False)
    patient_id = Column(PG_UUID(as_uuid=True), ForeignKey('patients.id'), nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    added_by = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    match_score = Column(Float, nullable=True)
    metadata = Column(JSONB, nullable=True)

    # Relationships
    cohort = relationship("CohortDefinition", back_populates="memberships")
    patient = relationship("Patient", foreign_keys=[patient_id])
    adder = relationship("User", foreign_keys=[added_by])

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "cohort_id": str(self.cohort_id),
            "patient_id": str(self.patient_id),
            "added_at": self.added_at.isoformat() if self.added_at else None,
            "added_by": str(self.added_by) if self.added_by else None,
            "match_score": self.match_score,
            "metadata": self.metadata,
        }
