"""Tests for break-glass emergency access API.

Test suite for break-glass workflow:
- Request emergency access (with justification)
- View break-glass audit logs
- Authorization checks (can_break_glass permission)
"""
import uuid
from datetime import datetime

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.user import User
from app.services.auth_service import AuthService


@pytest.fixture
async def admin_with_break_glass(db_session: AsyncSession) -> User:
    """Create an admin user with break-glass permission."""
    user = User(
        id=uuid.uuid4(),
        username="admin_break_glass",
        email="admin_bg@test.com",
        role="admin",
        is_active=True,
        can_break_glass=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    user.set_password("AdminPassword123!")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def clinician_with_break_glass(db_session: AsyncSession) -> User:
    """Create a clinician user with break-glass permission."""
    user = User(
        id=uuid.uuid4(),
        username="clinician_bg",
        email="clinician_bg@test.com",
        role="clinician",
        is_active=True,
        can_break_glass=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    user.set_password("ClinicianPassword123!")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def clinician_without_break_glass(db_session: AsyncSession) -> User:
    """Create a clinician user without break-glass permission."""
    user = User(
        id=uuid.uuid4(),
        username="clinician_no_bg",
        email="clinician_no_bg@test.com",
        role="clinician",
        is_active=True,
        can_break_glass=False,  # No break-glass permission
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    user.set_password("ClinicianPassword123!")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def admin_bg_token(admin_with_break_glass: User) -> str:
    """Generate JWT token for admin with break-glass."""
    token_data = AuthService.create_access_token(
        user_id=str(admin_with_break_glass.id), role=admin_with_break_glass.role
    )
    return token_data["access_token"]


@pytest.fixture
async def clinician_bg_token(clinician_with_break_glass: User) -> str:
    """Generate JWT token for clinician with break-glass."""
    token_data = AuthService.create_access_token(
        user_id=str(clinician_with_break_glass.id), role=clinician_with_break_glass.role
    )
    return token_data["access_token"]


@pytest.fixture
async def clinician_no_bg_token(clinician_without_break_glass: User) -> str:
    """Generate JWT token for clinician without break-glass."""
    token_data = AuthService.create_access_token(
        user_id=str(clinician_without_break_glass.id),
        role=clinician_without_break_glass.role,
    )
    return token_data["access_token"]


class TestRequestBreakGlassAccess:
    """Tests for POST /api/v1/break-glass/access."""

    async def test_request_break_glass_success(
        self,
        async_client: AsyncClient,
        clinician_bg_token: str,
        clinician_with_break_glass: User,
        db_session: AsyncSession,
    ):
        """Test successful break-glass access request."""
        # Arrange
        request_data = {
            "patient_id": "PATIENT-12345",
            "resource_type": "patient_record",
            "resource_id": "record-789",
            "justification": "Emergency situation: Patient unconscious, need immediate access to allergy information for treatment",
        }

        # Act
        response = await async_client.post(
            "/api/v1/break-glass/access",
            json=request_data,
            headers={"Authorization": f"Bearer {clinician_bg_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["access_granted"] is True
        assert data["user_id"] == str(clinician_with_break_glass.id)
        assert data["username"] == clinician_with_break_glass.username
        assert data["justification"] == request_data["justification"]
        assert data["resource_type"] == "patient_record"
        assert "expires_at" in data
        assert "EMERGENCY ACCESS GRANTED" in data["message"]

        # Verify audit log exists
        stmt = select(AuditLog).where(
            AuditLog.action == "BREAK_GLASS_ACCESS",
            AuditLog.user_id == clinician_with_break_glass.id,
        )
        result = await db_session.execute(stmt)
        audit_log = result.scalar_one_or_none()
        assert audit_log is not None
        assert audit_log.resource_type == "patient_record"
        assert audit_log.details["justification"] == request_data["justification"]
        assert audit_log.details["patient_id"] == "PATIENT-12345"

    async def test_request_break_glass_without_permission(
        self,
        async_client: AsyncClient,
        clinician_no_bg_token: str,
    ):
        """Test break-glass request without permission."""
        # Arrange
        request_data = {
            "patient_id": "PATIENT-12345",
            "resource_type": "patient_record",
            "justification": "Emergency: Need access to patient data",
        }

        # Act
        response = await async_client.post(
            "/api/v1/break-glass/access",
            json=request_data,
            headers={"Authorization": f"Bearer {clinician_no_bg_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "not authorized" in response.json()["detail"].lower()

    async def test_request_break_glass_insufficient_justification(
        self,
        async_client: AsyncClient,
        clinician_bg_token: str,
    ):
        """Test break-glass request with insufficient justification."""
        # Arrange
        request_data = {
            "patient_id": "PATIENT-12345",
            "resource_type": "patient_record",
            "justification": "Emergency",  # Too short (< 20 chars)
        }

        # Act
        response = await async_client.post(
            "/api/v1/break-glass/access",
            json=request_data,
            headers={"Authorization": f"Bearer {clinician_bg_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_request_break_glass_unauthorized(
        self,
        async_client: AsyncClient,
    ):
        """Test break-glass request without authentication."""
        # Arrange
        request_data = {
            "patient_id": "PATIENT-12345",
            "resource_type": "patient_record",
            "justification": "Emergency situation: Patient unconscious",
        }

        # Act
        response = await async_client.post(
            "/api/v1/break-glass/access",
            json=request_data,
        )

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_request_break_glass_audit_logged(
        self,
        async_client: AsyncClient,
        admin_bg_token: str,
        admin_with_break_glass: User,
        db_session: AsyncSession,
    ):
        """Test break-glass access is properly audit logged."""
        # Arrange
        request_data = {
            "patient_id": "PATIENT-99999",
            "resource_type": "medication_list",
            "resource_id": "med-456",
            "justification": "Critical emergency: Need to check medication interactions immediately",
        }

        # Act
        response = await async_client.post(
            "/api/v1/break-glass/access",
            json=request_data,
            headers={"Authorization": f"Bearer {admin_bg_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        # Verify audit log has all required fields
        stmt = select(AuditLog).where(
            AuditLog.action == "BREAK_GLASS_ACCESS",
            AuditLog.resource_id == "med-456",
        )
        result = await db_session.execute(stmt)
        audit_log = result.scalar_one_or_none()
        assert audit_log is not None
        assert audit_log.user_id == admin_with_break_glass.id
        assert audit_log.username == admin_with_break_glass.username
        assert audit_log.resource_type == "medication_list"
        assert audit_log.details["patient_id"] == "PATIENT-99999"
        assert "granted_at" in audit_log.details
        assert "expires_at" in audit_log.details


class TestListBreakGlassLogs:
    """Tests for GET /api/v1/break-glass/logs."""

    async def test_list_break_glass_logs_success(
        self,
        async_client: AsyncClient,
        admin_bg_token: str,
        clinician_bg_token: str,
        clinician_with_break_glass: User,
        db_session: AsyncSession,
    ):
        """Test successful break-glass log retrieval."""
        # Arrange: Create some break-glass events
        for i in range(3):
            await async_client.post(
                "/api/v1/break-glass/access",
                json={
                    "patient_id": f"PATIENT-{i}",
                    "resource_type": "patient_record",
                    "justification": f"Emergency situation {i}: Urgent access needed for immediate patient care",
                },
                headers={"Authorization": f"Bearer {clinician_bg_token}"},
            )

        # Act: Admin views logs
        response = await async_client.get(
            "/api/v1/break-glass/logs",
            headers={"Authorization": f"Bearer {admin_bg_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 3

        # Verify log entry structure
        log_entry = data["items"][0]
        assert "id" in log_entry
        assert "user_id" in log_entry
        assert "username" in log_entry
        assert "patient_id" in log_entry
        assert "resource_type" in log_entry
        assert "justification" in log_entry
        assert "timestamp" in log_entry

    async def test_list_break_glass_logs_pagination(
        self,
        async_client: AsyncClient,
        admin_bg_token: str,
        clinician_bg_token: str,
    ):
        """Test break-glass log pagination."""
        # Arrange: Create 5 break-glass events
        for i in range(5):
            await async_client.post(
                "/api/v1/break-glass/access",
                json={
                    "patient_id": f"PATIENT-PAGE-{i}",
                    "resource_type": "patient_record",
                    "justification": f"Emergency pagination test {i}: Critical access needed",
                },
                headers={"Authorization": f"Bearer {clinician_bg_token}"},
            )

        # Act: Get first page (2 items)
        response = await async_client.get(
            "/api/v1/break-glass/logs?page=1&page_size=2",
            headers={"Authorization": f"Bearer {admin_bg_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2

    async def test_list_break_glass_logs_filter_by_user(
        self,
        async_client: AsyncClient,
        admin_bg_token: str,
        clinician_bg_token: str,
        clinician_with_break_glass: User,
    ):
        """Test filtering break-glass logs by user."""
        # Arrange: Create break-glass event
        await async_client.post(
            "/api/v1/break-glass/access",
            json={
                "patient_id": "PATIENT-FILTER",
                "resource_type": "patient_record",
                "justification": "Emergency filter test: Immediate access required",
            },
            headers={"Authorization": f"Bearer {clinician_bg_token}"},
        )

        # Act: Filter by clinician user ID
        response = await async_client.get(
            f"/api/v1/break-glass/logs?user_id={clinician_with_break_glass.id}",
            headers={"Authorization": f"Bearer {admin_bg_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # All logs should be for the specified user
        for log in data["items"]:
            assert log["user_id"] == str(clinician_with_break_glass.id)

    async def test_list_break_glass_logs_non_admin_forbidden(
        self,
        async_client: AsyncClient,
        clinician_bg_token: str,
    ):
        """Test non-admin cannot view break-glass logs."""
        # Act
        response = await async_client.get(
            "/api/v1/break-glass/logs",
            headers={"Authorization": f"Bearer {clinician_bg_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_list_break_glass_logs_unauthorized(
        self,
        async_client: AsyncClient,
    ):
        """Test viewing break-glass logs without authentication."""
        # Act
        response = await async_client.get("/api/v1/break-glass/logs")

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
