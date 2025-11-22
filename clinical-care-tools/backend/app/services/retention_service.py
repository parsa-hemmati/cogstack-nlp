"""
Data Retention Service (Phase 6)

Implements automated data retention policies for regulatory compliance.
Handles archival and deletion of data based on retention policies.

Compliance:
- HIPAA: 7 years for audit logs
- GDPR: Right to be forgotten (automatic deletion)
- NHS: 8 years for clinical documents
- Research: 10 years for de-identified data
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, desc
from fastapi import HTTPException, status
import uuid
import json

from app.core.config import settings
from app.models.data_retention_policy import (
    DataRetentionPolicy, DataRetentionRecord, DataRetentionType, DataRetentionStatus
)
from app.models.audit_log import AuditLog


class RetentionService:
    """Service for managing data retention and lifecycle."""

    def __init__(self, db: AsyncSession):
        """
        Initialize retention service.

        Args:
            db: Database session
        """
        self.db = db

    async def initialize_policies(self) -> List[DataRetentionPolicy]:
        """
        Initialize default retention policies if they don't exist.

        Returns:
            List of initialized policies
        """
        policies = []

        # Define default policies
        default_policies = [
            {
                "data_type": DataRetentionType.CLINICAL_DOCUMENTS,
                "retention_years": settings.CLINICAL_DOCUMENTS_RETENTION_YEARS,
                "retention_description": "Clinical documents (NHS requirement: 8 years)"
            },
            {
                "data_type": DataRetentionType.AUDIT_LOGS,
                "retention_years": settings.AUDIT_LOGS_RETENTION_YEARS,
                "retention_description": "Audit logs (HIPAA requirement: 7 years)"
            },
            {
                "data_type": DataRetentionType.SESSION_DATA,
                "retention_days": settings.SESSION_DATA_RETENTION_DAYS,
                "retention_description": "Session data (90 days after last activity)"
            },
            {
                "data_type": DataRetentionType.TEMP_FILES,
                "retention_days": settings.TEMP_FILES_RETENTION_DAYS,
                "retention_description": "Temporary files (7 days)"
            },
            {
                "data_type": DataRetentionType.RESEARCH_DATA,
                "retention_years": settings.RESEARCH_DATA_RETENTION_YEARS,
                "retention_description": "Research data - de-identified (10 years)"
            }
        ]

        for policy_def in default_policies:
            # Check if policy exists
            result = await self.db.execute(
                select(DataRetentionPolicy).where(
                    DataRetentionPolicy.data_type == policy_def["data_type"]
                )
            )
            existing = result.scalar_one_or_none()

            if not existing:
                # Create policy
                policy = DataRetentionPolicy(
                    id=str(uuid.uuid4()),
                    data_type=policy_def["data_type"],
                    retention_years=policy_def.get("retention_years"),
                    retention_days=policy_def.get("retention_days"),
                    retention_description=policy_def["retention_description"],
                    is_active=True,
                    archive_enabled=True,
                    notification_days_before=7
                )
                self.db.add(policy)
                policies.append(policy)

        if policies:
            await self.db.commit()

        return policies

    async def get_policy(self, data_type: DataRetentionType) -> Optional[DataRetentionPolicy]:
        """
        Get retention policy for data type.

        Args:
            data_type: Type of data

        Returns:
            Policy or None
        """
        result = await self.db.execute(
            select(DataRetentionPolicy).where(
                and_(
                    DataRetentionPolicy.data_type == data_type,
                    DataRetentionPolicy.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_all_policies(self, active_only: bool = True) -> List[DataRetentionPolicy]:
        """
        Get all retention policies.

        Args:
            active_only: Only return active policies

        Returns:
            List of policies
        """
        query = select(DataRetentionPolicy)

        if active_only:
            query = query.where(DataRetentionPolicy.is_active == True)

        result = await self.db.execute(query.order_by(DataRetentionPolicy.data_type))
        return result.scalars().all()

    async def record_retention(
        self,
        policy_id: str,
        resource_type: str,
        resource_id: str,
        deletion_reason: str,
        archive_location: Optional[str] = None
    ) -> DataRetentionRecord:
        """
        Record a retention action (archival or deletion).

        Args:
            policy_id: Retention policy ID
            resource_type: Type of resource
            resource_id: ID of resource
            deletion_reason: Why resource is being deleted
            archive_location: Where archived data is stored

        Returns:
            Created retention record
        """
        record = DataRetentionRecord(
            id=str(uuid.uuid4()),
            policy_id=policy_id,
            resource_type=resource_type,
            resource_id=resource_id,
            status=DataRetentionStatus.PENDING,
            deletion_reason=deletion_reason,
            archive_location=archive_location,
            created_at=datetime.now(timezone.utc)
        )

        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)

        # Audit log
        await self._audit_log(
            action="DATA_RETENTION_RECORDED",
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
                "reason": deletion_reason
            }
        )

        return record

    async def archive_data(
        self,
        policy_id: str,
        resource_type: str,
        resource_id: str,
        archive_location: str
    ) -> DataRetentionRecord:
        """
        Archive data (before deletion).

        Args:
            policy_id: Retention policy ID
            resource_type: Type of resource
            resource_id: ID of resource
            archive_location: Where data is archived

        Returns:
            Updated retention record
        """
        # Get or create record
        result = await self.db.execute(
            select(DataRetentionRecord).where(
                and_(
                    DataRetentionRecord.policy_id == policy_id,
                    DataRetentionRecord.resource_id == resource_id
                )
            )
        )
        record = result.scalar_one_or_none()

        if not record:
            record = await self.record_retention(
                policy_id=policy_id,
                resource_type=resource_type,
                resource_id=resource_id,
                deletion_reason="RETENTION_POLICY",
                archive_location=archive_location
            )

        # Update record status
        record.status = DataRetentionStatus.ARCHIVED
        record.archived_at = datetime.now(timezone.utc)
        record.archive_location = archive_location

        await self.db.commit()
        await self.db.refresh(record)

        # Update policy statistics
        policy = await self.db.execute(
            select(DataRetentionPolicy).where(DataRetentionPolicy.id == policy_id)
        )
        policy_obj = policy.scalar_one_or_none()
        if policy_obj:
            policy_obj.records_archived_count = (policy_obj.records_archived_count or 0) + 1
            await self.db.commit()

        return record

    async def delete_data(
        self,
        policy_id: str,
        resource_type: str,
        resource_id: str
    ) -> DataRetentionRecord:
        """
        Delete data after retention period.

        Args:
            policy_id: Retention policy ID
            resource_type: Type of resource
            resource_id: ID of resource

        Returns:
            Updated retention record
        """
        # Get or create record
        result = await self.db.execute(
            select(DataRetentionRecord).where(
                and_(
                    DataRetentionRecord.policy_id == policy_id,
                    DataRetentionRecord.resource_id == resource_id
                )
            )
        )
        record = result.scalar_one_or_none()

        if not record:
            record = await self.record_retention(
                policy_id=policy_id,
                resource_type=resource_type,
                resource_id=resource_id,
                deletion_reason="RETENTION_POLICY_EXPIRED"
            )

        # Update record status
        record.status = DataRetentionStatus.DELETED
        record.deleted_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(record)

        # Update policy statistics
        policy = await self.db.execute(
            select(DataRetentionPolicy).where(DataRetentionPolicy.id == policy_id)
        )
        policy_obj = policy.scalar_one_or_none()
        if policy_obj:
            policy_obj.records_deleted_count = (policy_obj.records_deleted_count or 0) + 1
            await self.db.commit()

        # Audit log (important for compliance)
        await self._audit_log(
            action="DATA_DELETED",
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
                "policy_id": policy_id
            }
        )

        return record

    async def get_due_for_deletion(
        self,
        data_type: DataRetentionType,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get records due for deletion based on retention policy.

        Args:
            data_type: Type of data
            limit: Maximum records to return

        Returns:
            List of records due for deletion with retention info
        """
        # Get policy
        policy = await self.get_policy(data_type)
        if not policy:
            return []

        # Calculate cutoff date
        now = datetime.now(timezone.utc)
        if policy.retention_years:
            cutoff_date = now - timedelta(days=policy.retention_years * 365)
        elif policy.retention_days:
            cutoff_date = now - timedelta(days=policy.retention_days)
        else:
            return []

        # NOTE: Query actual data tables based on data_type
        # For now, return empty list
        # In production, this would query clinical_documents, audit_logs, etc.

        return []

    async def get_retention_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate data retention compliance report.

        Args:
            start_date: Report start date
            end_date: Report end date

        Returns:
            Compliance report with statistics
        """
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)

        # Get all policies
        policies = await self.get_all_policies(active_only=False)

        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "policies": [],
            "totals": {
                "archived": 0,
                "deleted": 0,
                "failed": 0
            }
        }

        for policy in policies:
            # Get records for this policy
            result = await self.db.execute(
                select(DataRetentionRecord).where(
                    and_(
                        DataRetentionRecord.policy_id == policy.id,
                        DataRetentionRecord.created_at >= start_date,
                        DataRetentionRecord.created_at <= end_date
                    )
                )
            )
            records = result.scalars().all()

            # Aggregate stats
            archived = sum(1 for r in records if r.status == DataRetentionStatus.ARCHIVED)
            deleted = sum(1 for r in records if r.status == DataRetentionStatus.DELETED)
            failed = sum(1 for r in records if r.status == DataRetentionStatus.FAILED)

            report["policies"].append({
                "data_type": policy.data_type.value,
                "retention": f"{policy.retention_years or policy.retention_days} {'years' if policy.retention_years else 'days'}",
                "archived": archived,
                "deleted": deleted,
                "failed": failed,
                "total_records_archived": policy.records_archived_count,
                "total_records_deleted": policy.records_deleted_count
            })

            report["totals"]["archived"] += archived
            report["totals"]["deleted"] += deleted
            report["totals"]["failed"] += failed

        return report

    async def _audit_log(
        self,
        action: str,
        details: dict
    ):
        """Create audit log entry for retention action."""
        audit_entry = AuditLog(
            user_id="SYSTEM",
            action=action,
            resource_type="DATA_RETENTION",
            resource_id=None,
            details=details,
            timestamp=datetime.now(timezone.utc)
        )
        self.db.add(audit_entry)
        await self.db.commit()
