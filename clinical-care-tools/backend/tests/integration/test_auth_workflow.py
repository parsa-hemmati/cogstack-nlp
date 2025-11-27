"""Integration tests for authentication workflow."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.audit_log import AuditLog
from app.models.user import User


@pytest.mark.asyncio
class TestAuthWorkflow:
    """Test complete authentication workflows."""

    async def test_user_registration_login_workflow(
        self, client: AsyncClient, db_session
    ):
        """Test user can register and then login."""
        # Register new user
        register_data = {
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "full_name": "New User",
            "role": "clinician",
        }

        register_response = await client.post(
            "/api/v1/auth/register",
            json=register_data,
        )

        assert register_response.status_code == 201
        user_data = register_response.json()
        assert user_data["email"] == "newuser@example.com"
        assert "id" in user_data
        assert "hashed_password" not in user_data  # Security

        # Login with new user
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "newuser@example.com",
                "password": "SecurePassword123!",
            },
        )

        assert login_response.status_code == 200
        token_data = login_response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"

        # Verify audit logs
        query = select(AuditLog).where(
            AuditLog.action.in_(["USER_REGISTERED", "LOGIN"])
        )
        result = await db_session.execute(query)
        audit_logs = result.scalars().all()

        assert len(audit_logs) >= 2
        actions = [log.action for log in audit_logs]
        assert "USER_REGISTERED" in actions
        assert "LOGIN" in actions

    async def test_failed_login_lockout(self, client: AsyncClient, test_user, db_session):
        """Test account lockout after failed login attempts."""
        # Attempt login with wrong password 5 times
        for i in range(5):
            response = await client.post(
                "/api/v1/auth/login",
                data={
                    "username": test_user.email,
                    "password": "WrongPassword123!",
                },
            )
            assert response.status_code == 401

        # Verify user is locked
        query = select(User).where(User.id == test_user.id)
        result = await db_session.execute(query)
        user = result.scalar_one()

        assert user.is_locked is True
        assert user.failed_login_attempts >= 5

        # Try to login with correct password - should fail (locked)
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "clinicianpass123",  # Correct password
            },
        )

        assert response.status_code == 403
        assert "locked" in response.json()["detail"].lower()

    async def test_authenticated_access(
        self, client: AsyncClient, test_clinician_user
    ):
        """Test accessing protected endpoints with authentication."""
        # Login
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_clinician_user.email,
                "password": "clinicianpass123",
            },
        )
        token = login_response.json()["access_token"]

        # Access protected endpoint (get current user)
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        user_data = response.json()
        assert user_data["email"] == test_clinician_user.email
        assert user_data["role"] == "clinician"

    async def test_unauthorized_access(self, client: AsyncClient):
        """Test accessing protected endpoints without authentication."""
        # Try to access protected endpoint without token
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401

    async def test_invalid_token_access(self, client: AsyncClient):
        """Test accessing protected endpoints with invalid token."""
        # Try with invalid token
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token_12345"},
        )

        assert response.status_code == 401

    async def test_role_based_access(
        self, client: AsyncClient, test_clinician_user, test_viewer_user
    ):
        """Test role-based access control."""
        # Login as clinician
        clinician_login = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_clinician_user.email,
                "password": "clinicianpass123",
            },
        )
        clinician_token = clinician_login.json()["access_token"]

        # Login as viewer
        viewer_login = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_viewer_user.email,
                "password": "viewerpass123",
            },
        )
        viewer_token = viewer_login.json()["access_token"]

        # Clinician can create patient
        clinician_create = await client.post(
            "/api/v1/patients",
            json={
                "mrn": "TEST-ROLE-001",
                "first_name": "Test",
                "last_name": "Patient",
                "date_of_birth": "1980-01-01",
            },
            headers={"Authorization": f"Bearer {clinician_token}"},
        )
        assert clinician_create.status_code == 201

        # Viewer cannot create patient (read-only)
        viewer_create = await client.post(
            "/api/v1/patients",
            json={
                "mrn": "TEST-ROLE-002",
                "first_name": "Test2",
                "last_name": "Patient2",
                "date_of_birth": "1980-01-01",
            },
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert viewer_create.status_code == 403
