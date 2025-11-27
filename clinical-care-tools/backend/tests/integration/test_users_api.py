"""
Integration tests for User Management API endpoints.

Tests:
- GET /api/v1/users (list all users)
- POST /api/v1/users (create new user)
- PATCH /api/v1/users/{id} (update user)
- Permission checks (admin only)
- Audit logging
"""

import pytest
from httpx import AsyncClient

from app.models.user import User
from app.models.audit_log import AuditLog
from sqlalchemy import select


pytestmark = pytest.mark.asyncio


async def test_get_users_as_admin_returns_200(admin_client: AsyncClient):
    """Test that admin can retrieve user list."""
    response = await admin_client.get("/api/v1/users")

    assert response.status_code == 200, \
        "Admin should be able to retrieve user list"

    data = response.json()
    assert isinstance(data, list), "Response should be a list of users"
    assert len(data) > 0, "Should return at least one user (admin)"

    # Check user structure
    user = data[0]
    assert "id" in user
    assert "username" in user
    assert "full_name" in user
    assert "role" in user
    assert "is_active" in user
    assert "hashed_password" not in user, "Should not expose password hash"


async def test_get_users_as_clinician_returns_403(clinician_client: AsyncClient):
    """Test that non-admin users cannot access user list."""
    response = await clinician_client.get("/api/v1/users")

    assert response.status_code == 403, \
        "Clinician should not be able to access user list"

    data = response.json()
    assert "detail" in data
    assert "admin" in data["detail"].lower() or "permission" in data["detail"].lower()


async def test_create_user_as_admin_returns_201(admin_client: AsyncClient, db_session):
    """Test that admin can create new user."""
    user_data = {
        "username": "new_user_001",
        "full_name": "New Test User",
        "password": "SecurePass123!",
        "role": "clinician"
    }

    response = await admin_client.post("/api/v1/users", json=user_data)

    assert response.status_code == 201, \
        "Admin should be able to create new user"

    data = response.json()
    assert data["username"] == "new_user_001"
    assert data["full_name"] == "New Test User"
    assert data["role"] == "clinician"
    assert data["is_active"] is True
    assert data["must_change_password"] is True, \
        "New users should be required to change password"
    assert "hashed_password" not in data
    assert "password" not in data

    # Verify user was created in database with hashed password
    result = await db_session.execute(
        select(User).where(User.username == "new_user_001")
    )
    created_user = result.scalar_one()
    assert created_user is not None
    assert created_user.hashed_password != "SecurePass123!", \
        "Password should be hashed, not stored in plaintext"
    assert len(created_user.hashed_password) > 50, \
        "Hashed password should be significantly longer than plaintext"


async def test_create_user_with_duplicate_username_returns_400(admin_client: AsyncClient, test_admin):
    """Test that creating user with duplicate username fails."""
    user_data = {
        "username": test_admin.username,  # Duplicate
        "full_name": "Duplicate User",
        "password": "SecurePass123!",
        "role": "viewer"
    }

    response = await admin_client.post("/api/v1/users", json=user_data)

    assert response.status_code == 400, \
        "Creating user with duplicate username should fail"

    data = response.json()
    assert "detail" in data
    assert "username" in data["detail"].lower() or "exists" in data["detail"].lower()


async def test_create_user_as_clinician_returns_403(clinician_client: AsyncClient):
    """Test that non-admin cannot create users."""
    user_data = {
        "username": "unauthorized_user",
        "full_name": "Unauthorized User",
        "password": "SecurePass123!",
        "role": "viewer"
    }

    response = await clinician_client.post("/api/v1/users", json=user_data)

    assert response.status_code == 403, \
        "Non-admin should not be able to create users"


async def test_create_user_with_invalid_role_returns_422(admin_client: AsyncClient):
    """Test that creating user with invalid role fails validation."""
    user_data = {
        "username": "invalid_role_user",
        "full_name": "Invalid Role User",
        "password": "SecurePass123!",
        "role": "superuser"  # Invalid role
    }

    response = await admin_client.post("/api/v1/users", json=user_data)

    assert response.status_code == 422, \
        "Creating user with invalid role should fail validation"


async def test_create_user_with_weak_password_returns_400(admin_client: AsyncClient):
    """Test that creating user with weak password fails."""
    user_data = {
        "username": "weak_password_user",
        "full_name": "Weak Password User",
        "password": "123",  # Too weak
        "role": "viewer"
    }

    response = await admin_client.post("/api/v1/users", json=user_data)

    assert response.status_code == 400, \
        "Creating user with weak password should fail"

    data = response.json()
    assert "password" in data["detail"].lower()


async def test_update_user_as_admin_returns_200(admin_client: AsyncClient, test_clinician, db_session):
    """Test that admin can update user."""
    update_data = {
        "full_name": "Updated Clinician Name",
        "is_active": False
    }

    response = await admin_client.patch(
        f"/api/v1/users/{test_clinician.id}",
        json=update_data
    )

    assert response.status_code == 200, \
        "Admin should be able to update user"

    data = response.json()
    assert data["full_name"] == "Updated Clinician Name"
    assert data["is_active"] is False

    # Verify database was updated
    await db_session.refresh(test_clinician)
    assert test_clinician.full_name == "Updated Clinician Name"
    assert test_clinician.is_active is False


async def test_update_user_role_as_admin_returns_200(admin_client: AsyncClient, test_viewer, db_session):
    """Test that admin can change user role."""
    update_data = {
        "role": "researcher"
    }

    response = await admin_client.patch(
        f"/api/v1/users/{test_viewer.id}",
        json=update_data
    )

    assert response.status_code == 200

    data = response.json()
    assert data["role"] == "researcher"

    # Verify database was updated
    await db_session.refresh(test_viewer)
    assert test_viewer.role == "researcher"


async def test_update_user_as_clinician_returns_403(clinician_client: AsyncClient, test_viewer):
    """Test that non-admin cannot update users."""
    update_data = {
        "full_name": "Unauthorized Update"
    }

    response = await clinician_client.patch(
        f"/api/v1/users/{test_viewer.id}",
        json=update_data
    )

    assert response.status_code == 403, \
        "Non-admin should not be able to update users"


async def test_update_nonexistent_user_returns_404(admin_client: AsyncClient):
    """Test that updating non-existent user fails."""
    update_data = {
        "full_name": "Ghost User"
    }

    response = await admin_client.patch(
        "/api/v1/users/00000000-0000-0000-0000-000000000000",
        json=update_data
    )

    assert response.status_code == 404, \
        "Updating non-existent user should return 404"


async def test_create_user_creates_audit_log(admin_client: AsyncClient, db_session, test_admin):
    """Test that creating user generates audit log."""
    user_data = {
        "username": "audit_test_user",
        "full_name": "Audit Test User",
        "password": "SecurePass123!",
        "role": "viewer"
    }

    response = await admin_client.post("/api/v1/users", json=user_data)
    assert response.status_code == 201

    created_user_id = response.json()["id"]

    # Check audit log exists
    result = await db_session.execute(
        select(AuditLog)
        .where(AuditLog.action == "CREATE_USER")
        .where(AuditLog.resource_id == created_user_id)
        .where(AuditLog.user_id == str(test_admin.id))
    )
    audit_log = result.scalar_one_or_none()

    assert audit_log is not None, \
        "Creating user should generate audit log"
    assert audit_log.resource_type == "user"
    assert audit_log.username == test_admin.username


async def test_update_user_creates_audit_log(admin_client: AsyncClient, db_session, test_admin, test_viewer):
    """Test that updating user generates audit log."""
    update_data = {
        "full_name": "Audit Update Test"
    }

    response = await admin_client.patch(
        f"/api/v1/users/{test_viewer.id}",
        json=update_data
    )
    assert response.status_code == 200

    # Check audit log exists
    result = await db_session.execute(
        select(AuditLog)
        .where(AuditLog.action == "UPDATE_USER")
        .where(AuditLog.resource_id == str(test_viewer.id))
        .where(AuditLog.user_id == str(test_admin.id))
    )
    audit_log = result.scalar_one_or_none()

    assert audit_log is not None, \
        "Updating user should generate audit log"
    assert audit_log.resource_type == "user"


async def test_get_users_returns_correct_fields(admin_client: AsyncClient):
    """Test that user response includes all expected fields and excludes sensitive ones."""
    response = await admin_client.get("/api/v1/users")
    assert response.status_code == 200

    users = response.json()
    assert len(users) > 0

    user = users[0]

    # Required fields
    required_fields = ["id", "username", "full_name", "role", "is_active", "must_change_password", "created_at"]
    for field in required_fields:
        assert field in user, f"User response should include '{field}'"

    # Sensitive fields should NOT be exposed
    sensitive_fields = ["hashed_password", "password"]
    for field in sensitive_fields:
        assert field not in user, f"User response should NOT include '{field}'"
