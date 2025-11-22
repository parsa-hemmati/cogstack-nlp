"""
Unit tests for data retention service.

Tests cover:
- Retention policy initialization
- Policy retrieval
- Archival and deletion recording
- Retention reporting
- Cleanup operations
"""

import pytest
from uuid import uuid4

from app.services.retention_service import RetentionService
from app.models.data_retention_policy import DataRetentionType, DataRetentionStatus


@pytest.mark.unit
class TestRetentionService:
    """Test cases for retention service."""

    @pytest.fixture
    async def service(self, db_session):
        """Create service instance."""
        return RetentionService(db_session)

    @pytest.mark.asyncio
    async def test_initialize_policies(self, service):
        """Test initialization of default policies."""
        policies = await service.initialize_policies()

        # Should create policies for each data type
        assert len(policies) > 0

        # Check specific policies exist
        policy_types = {p.data_type for p in policies}
        assert DataRetentionType.CLINICAL_DOCUMENTS in policy_types
        assert DataRetentionType.AUDIT_LOGS in policy_types
        assert DataRetentionType.TEMP_FILES in policy_types

    @pytest.mark.asyncio
    async def test_get_policy(self, service):
        """Test retrieving a specific policy."""
        # Initialize first
        await service.initialize_policies()

        # Get audit logs policy
        policy = await service.get_policy(DataRetentionType.AUDIT_LOGS)

        assert policy is not None
        assert policy.data_type == DataRetentionType.AUDIT_LOGS
        assert policy.is_active is True

    @pytest.mark.asyncio
    async def test_get_all_policies(self, service):
        """Test retrieving all policies."""
        # Initialize
        await service.initialize_policies()

        # Get all
        policies = await service.get_all_policies(active_only=True)

        assert len(policies) > 0
        assert all(p.is_active for p in policies)

    @pytest.mark.asyncio
    async def test_record_retention(self, service):
        """Test recording a retention action."""
        # Initialize
        policies = await service.initialize_policies()
        policy_id = policies[0].id if policies else str(uuid4())

        # Record retention
        record = await service.record_retention(
            policy_id=policy_id,
            resource_type="document",
            resource_id=str(uuid4()),
            deletion_reason="retention_policy"
        )

        assert record is not None
        assert record.status == DataRetentionStatus.PENDING

    @pytest.mark.asyncio
    async def test_archive_data(self, service):
        """Test archiving data."""
        # Initialize
        policies = await service.initialize_policies()
        policy_id = policies[0].id if policies else str(uuid4())

        # Archive
        record = await service.archive_data(
            policy_id=policy_id,
            resource_type="document",
            resource_id=str(uuid4()),
            archive_location="s3://archive/doc-123"
        )

        assert record is not None
        assert record.status == DataRetentionStatus.ARCHIVED
        assert record.archive_location == "s3://archive/doc-123"

    @pytest.mark.asyncio
    async def test_delete_data(self, service):
        """Test deleting data."""
        # Initialize
        policies = await service.initialize_policies()
        policy_id = policies[0].id if policies else str(uuid4())

        # Delete
        record = await service.delete_data(
            policy_id=policy_id,
            resource_type="document",
            resource_id=str(uuid4())
        )

        assert record is not None
        assert record.status == DataRetentionStatus.DELETED
        assert record.deleted_at is not None

    @pytest.mark.asyncio
    async def test_get_retention_report(self, service):
        """Test generating retention report."""
        # Initialize
        await service.initialize_policies()

        # Generate report
        report = await service.get_retention_report()

        assert report is not None
        assert "generated_at" in report
        assert "period" in report
        assert "policies" in report
        assert "totals" in report

    @pytest.mark.asyncio
    async def test_report_includes_statistics(self, service):
        """Test that report includes policy statistics."""
        # Initialize
        policies = await service.initialize_policies()
        if policies:
            policy_id = policies[0].id

            # Archive some records
            for _ in range(3):
                await service.archive_data(
                    policy_id=policy_id,
                    resource_type="document",
                    resource_id=str(uuid4()),
                    archive_location="s3://archive"
                )

            # Delete some records
            for _ in range(2):
                await service.delete_data(
                    policy_id=policy_id,
                    resource_type="document",
                    resource_id=str(uuid4())
                )

        # Generate report
        report = await service.get_retention_report()

        assert report["totals"]["archived"] >= 3
        assert report["totals"]["deleted"] >= 2

    @pytest.mark.asyncio
    async def test_policy_statistics_updated(self, service):
        """Test that policy statistics are updated."""
        # Initialize
        policies = await service.initialize_policies()
        if policies:
            policy = policies[0]
            initial_archived = policy.records_archived_count

            # Archive a record
            await service.archive_data(
                policy_id=policy.id,
                resource_type="document",
                resource_id=str(uuid4()),
                archive_location="s3://archive"
            )

            # Get updated policy
            updated = await service.get_policy(policy.data_type)
            assert updated.records_archived_count > initial_archived

    @pytest.mark.asyncio
    async def test_different_retention_types(self, service):
        """Test handling of different retention data types."""
        # Initialize
        await service.initialize_policies()

        # Get different types
        clinical_policy = await service.get_policy(DataRetentionType.CLINICAL_DOCUMENTS)
        audit_policy = await service.get_policy(DataRetentionType.AUDIT_LOGS)
        session_policy = await service.get_policy(DataRetentionType.SESSION_DATA)

        assert clinical_policy is not None
        assert audit_policy is not None
        assert session_policy is not None

        # Check different retention periods
        assert clinical_policy.retention_years == 8  # NHS
        assert audit_policy.retention_years == 7  # HIPAA
        assert session_policy.retention_days == 90  # Activity-based

    @pytest.mark.asyncio
    async def test_get_due_for_deletion(self, service):
        """Test getting records due for deletion."""
        # Initialize
        await service.initialize_policies()

        # Get due for deletion (should be empty initially)
        due = await service.get_due_for_deletion(
            data_type=DataRetentionType.TEMP_FILES
        )

        # Should return a list (may be empty)
        assert isinstance(due, list)
