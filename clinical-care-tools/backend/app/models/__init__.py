"""
Database Models

All SQLAlchemy models for the Clinical Care Tools application.
Follows SQLAlchemy 2.0+ async patterns with type hints.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


# Import all models to ensure they're registered with Base
from app.models.user import User  # noqa: E402, F401
from app.models.session import Session  # noqa: E402, F401
from app.models.audit_log import AuditLog  # noqa: E402, F401
from app.models.project import Project, ProjectMember, Task  # noqa: E402, F401
from app.models.document import Document  # noqa: E402, F401
from app.models.extracted_entity import ExtractedEntity  # noqa: E402, F401
from app.models.patient import Patient  # noqa: E402, F401
from app.models.module import Module  # noqa: E402, F401
from app.models.patient_search import PatientSearchResult  # noqa: E402, F401
from app.models.timeline import TimelineView  # noqa: E402, F401
# Phase 5-6 Models
from app.models.break_glass_access import BreakGlassAccess, BreakGlassStatus  # noqa: E402, F401
from app.models.data_retention_policy import (  # noqa: E402, F401
    DataRetentionPolicy, DataRetentionRecord, DataRetentionType, DataRetentionStatus
)
from app.models.clinical_safety import (  # noqa: E402, F401
    ClinicalSafetyWarning, ClinicalSafetyOverride, SafetyWarningType, SafetyWarningLevel
)

__all__ = [
    "Base",
    "User",
    "Session",
    "AuditLog",
    "Project",
    "ProjectMember",
    "Task",
    "Document",
    "ExtractedEntity",
    "Patient",
    "Module",
    "PatientSearchResult",
    "TimelineView",
    # Phase 5-6
    "BreakGlassAccess",
    "BreakGlassStatus",
    "DataRetentionPolicy",
    "DataRetentionRecord",
    "DataRetentionType",
    "DataRetentionStatus",
    "ClinicalSafetyWarning",
    "ClinicalSafetyOverride",
    "SafetyWarningType",
    "SafetyWarningLevel",
]
