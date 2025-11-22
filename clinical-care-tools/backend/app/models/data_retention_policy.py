"""
Data Retention Policy Model (Phase 6)

Implements automated data retention policies for regulatory compliance.
Supports different retention periods for different data types.

Compliance:
- HIPAA: 7 years for audit logs
- GDPR: Right to be forgotten (automatic deletion)
- NHS: 8 years for clinical documents
- Research: 10 years for de-identified data
"""

from datetime import datetime
from typing import Optional
from enum import Enum

from sqlalchemy import DateTime, Index, String, func, Boolean, Integer, Enum as SQLEnum, Text
from sqlalchemy.orm import mapped_column, Mapped

from app.models import Base


class DataRetentionType(str, Enum):
    """Types of data subject to retention policies."""
    CLINICAL_DOCUMENTS = "clinical_documents"  # 8 years (NHS)
    AUDIT_LOGS = "audit_logs"  # 7 years (HIPAA)
    SESSION_DATA = "session_data"  # 90 days after last activity
    TEMP_FILES = "temp_files"  # 7 days
    RESEARCH_DATA = "research_data"  # 10 years (de-identified)
    USER_DATA = "user_data"  # GDPR: 30 days after account deletion


class DataRetentionStatus(str, Enum):
    """Status of retention processing."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    ARCHIVED = "archived"
    DELETED = "deleted"
    FAILED = "failed"


class DataRetentionPolicy(Base):
    """
    Data retention policy and execution tracking.

    Implements automated data lifecycle management:
    - Archives old data (compliance-approved retention)
    - Deletes expired data (beyond retention period)
    - Tracks retention execution and compliance

    Attributes:
        id: Unique policy identifier
        data_type: Type of data (clinical_documents, audit_logs, etc.)
        retention_years: Retention period in years
        retention_days: Retention period in days (for shorter periods)
        retention_description: Human-readable description of policy
        is_active: Whether policy is currently enforced
        archive_enabled: Whether to archive instead of delete
        notification_days_before: Send notification N days before deletion
        last_executed_at: When retention job last ran
        next_execution_at: When retention job should run next
        records_archived_count: Total records archived
        records_deleted_count: Total records deleted
        created_at: When policy was created
        updated_at: Last update to policy

    Compliance Features:
        - Configurable retention periods per data type
        - Archive before delete (compliance trail)
        - Notification warnings (right to be forgotten)
        - Execution tracking and audit trail
        - Failure tracking and alerts
    """

    __tablename__ = "data_retention_policies"

    # Primary Key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Policy Definition
    data_type: Mapped[DataRetentionType] = mapped_column(
        SQLEnum(DataRetentionType),
        nullable=False,
        unique=True,
        index=True,
        comment="Type of data (clinical_documents, audit_logs, etc.)"
    )

    # Retention Period
    retention_years: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Retention period in years (for long-term data)"
    )
    retention_days: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Retention period in days (for short-term data)"
    )

    # Policy Details
    retention_description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Human-readable description (e.g., 'HIPAA requirement: 7 years')"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether policy is currently enforced"
    )

    # Archive Configuration
    archive_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Archive data before deletion (compliance trail)"
    )
    archive_location: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Location to archive data (S3 bucket, file path, etc.)"
    )

    # Notification Settings
    notification_days_before: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=7,
        comment="Send notification N days before deletion (GDPR: right to be forgotten)"
    )

    # Execution Tracking
    last_executed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When retention job last ran"
    )
    next_execution_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When retention job should run next"
    )

    # Statistics
    records_archived_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Total records archived under this policy"
    )
    records_deleted_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Total records deleted under this policy"
    )

    # Audit Trail
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        comment="When policy was created"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        comment="Last update to policy"
    )

    # Indexes
    __table_args__ = (
        Index("idx_retention_policy_type", "data_type"),
        Index("idx_retention_policy_active", "is_active"),
        Index("idx_retention_policy_executed", "last_executed_at"),
    )

    def __repr__(self) -> str:
        """String representation of DataRetentionPolicy."""
        return f"<DataRetentionPolicy(data_type={self.data_type}, retention_years={self.retention_years})>"


class DataRetentionRecord(Base):
    """
    Individual record tracking for data retention execution.

    Tracks each deletion/archival operation for compliance audit trail.

    Attributes:
        id: Unique record identifier
        policy_id: Reference to retention policy
        resource_type: Type of resource (document, log, session, etc.)
        resource_id: ID of resource being retained/deleted
        status: Current status (pending/archived/deleted/failed)
        archived_at: When data was archived
        deleted_at: When data was deleted
        archive_location: Where archived data is stored
        deletion_reason: Why data was deleted (retention policy, GDPR request, etc.)
        created_at: When retention record was created
    """

    __tablename__ = "data_retention_records"

    # Primary Key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Foreign Keys
    policy_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
        comment="Reference to retention policy"
    )

    # Resource Information
    resource_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Type of resource (document, log, session, file)"
    )
    resource_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
        comment="ID of resource being retained/deleted"
    )

    # Status Tracking
    status: Mapped[DataRetentionStatus] = mapped_column(
        SQLEnum(DataRetentionStatus),
        nullable=False,
        default=DataRetentionStatus.PENDING,
        index=True,
        comment="pending/archived/deleted/failed"
    )

    # Operation Details
    archived_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When data was archived"
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When data was deleted"
    )
    archive_location: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Where archived data is stored"
    )
    deletion_reason: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Why deleted: retention_policy/gdpr_request/user_deletion"
    )

    # Audit Trail
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        comment="When retention record was created"
    )

    # Indexes
    __table_args__ = (
        Index("idx_retention_record_policy", "policy_id"),
        Index("idx_retention_record_resource", "resource_type", "resource_id"),
        Index("idx_retention_record_status", "status"),
        Index("idx_retention_record_deleted", "deleted_at"),
    )

    def __repr__(self) -> str:
        """String representation of DataRetentionRecord."""
        return f"<DataRetentionRecord(resource_type={self.resource_type}, resource_id={self.resource_id}, status={self.status})>"
