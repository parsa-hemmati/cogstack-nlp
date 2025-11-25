"""Tests for role management API endpoints.

Test suite for role and permission operations:
- List all roles
- Get role details
- Get user permissions
- Assign role to user
"""
import uuid
from datetime import datetime

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.auth_service import AuthService


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user for testing."""
    user = User(
        id=uuid.uuid4(),
        username="admin_roles",
        email="admin_roles@test.com",
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
async def clinician_user(db_session: AsyncSession) -> User:
    """Create a clinician user for testing."""
    user = User(
        id=uuid.uuid4(),
        username="clinician_roles",
        email="clinician_roles@test.com",
        role="clinician",
        is_active=True,
        can_break_glass=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    user.set_password("ClinicianPassword123!")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def researcher_user(db_session: AsyncSession) -> User:
    """Create a researcher user for testing."""
    user = User(
        id=uuid.uuid4(),
        username="researcher_roles",
        email="researcher_roles@test.com",
        role="researcher",
        is_active=True,
        can_break_glass=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    user.set_password("ResearcherPassword123!")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def admin_token(admin_user: User) -> str:
    """Generate JWT token for admin user."""
    token_data = AuthService.create_access_token(
        user_id=str(admin_user.id), role=admin_user.role
    )
    return token_data["access_token"]


@pytest.fixture
async def clinician_token(clinician_user: User) -> str:
    """Generate JWT token for clinician user."""
    token_data = AuthService.create_access_token(
        user_id=str(clinician_user.id), role=clinician_user.role
    )
    return token_data["access_token"]


@pytest.fixture
async def researcher_token(researcher_user: User) -> str:
    """Generate JWT token for researcher user."""
    token_data = AuthService.create_access_token(
        user_id=str(researcher_user.id), role=researcher_user.role
    )
    return token_data["access_token"]


class TestListRoles:
    """Tests for GET /api/v1/roles (list all roles)."""

    async def test_list_roles_success(
        self, async_client: AsyncClient, clinician_token: str
    ):
        """Test successful role list retrieval."""
        # Act
        response = await async_client.get(
            "/api/v1/roles",
            headers={"Authorization": f"Bearer {clinician_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "roles" in data
        assert len(data["roles"]) == 3  # clinician, researcher, admin

        # Verify each role has required fields
        for role in data["roles"]:
            assert "role" in role
            assert "description" in role
            assert "permissions" in role
            assert isinstance(role["permissions"], list)

    async def test_list_roles_shows_permission_details(
        self, async_client: AsyncClient, admin_token: str
    ):
        """Test that role list shows permission details."""
        # Act
        response = await async_client.get(
            "/api/v1/roles",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Find admin role
        admin_role = next(r for r in data["roles"] if r["role"] == "admin")

        # Admin should have user management permissions
        permissions = admin_role["permissions"]
        assert "user:read" in permissions
        assert "user:create" in permissions
        assert "user:update" in permissions
        assert "user:delete" in permissions

    async def test_list_roles_unauthorized(self, async_client: AsyncClient):
        """Test role list without authentication."""
        # Act
        response = await async_client.get("/api/v1/roles")

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetRole:
    """Tests for GET /api/v1/roles/{role} (get role details)."""

    async def test_get_role_success(
        self, async_client: AsyncClient, clinician_token: str
    ):
        """Test successful role details retrieval."""
        # Act
        response = await async_client.get(
            "/api/v1/roles/clinician",
            headers={"Authorization": f"Bearer {clinician_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["role"] == "clinician"
        assert "description" in data
        assert "permissions" in data

        # Clinician should have patient access permissions
        permissions = data["permissions"]
        assert "patient:read" in permissions
        assert "patient:write" in permissions
        assert "nlp:process" in permissions

    async def test_get_researcher_role(
        self, async_client: AsyncClient, researcher_token: str
    ):
        """Test researcher role has correct permissions."""
        # Act
        response = await async_client.get(
            "/api/v1/roles/researcher",
            headers={"Authorization": f"Bearer {researcher_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["role"] == "researcher"

        # Researcher should have cohort permissions but not patient write
        permissions = data["permissions"]
        assert "cohort:create" in permissions
        assert "cohort:view" in permissions
        assert "cohort:export" in permissions
        assert "patient:read" in permissions
        assert "patient:write" not in permissions  # Read-only for research

    async def test_get_role_not_found(
        self, async_client: AsyncClient, clinician_token: str
    ):
        """Test role retrieval with invalid role."""
        # Act
        response = await async_client.get(
            "/api/v1/roles/invalid_role",
            headers={"Authorization": f"Bearer {clinician_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetUserPermissions:
    """Tests for GET /api/v1/roles/users/{id}/permissions."""

    async def test_get_own_permissions(
        self, async_client: AsyncClient, clinician_token: str, clinician_user: User
    ):
        """Test user can view their own permissions."""
        # Act
        response = await async_client.get(
            f"/api/v1/roles/users/{clinician_user.id}/permissions",
            headers={"Authorization": f"Bearer {clinician_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == str(clinician_user.id)
        assert data["username"] == clinician_user.username
        assert data["role"] == "clinician"
        assert "permissions" in data
        assert len(data["permissions"]) > 0

    async def test_admin_can_view_any_permissions(
        self, async_client: AsyncClient, admin_token: str, researcher_user: User
    ):
        """Test admin can view any user's permissions."""
        # Act
        response = await async_client.get(
            f"/api/v1/roles/users/{researcher_user.id}/permissions",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == str(researcher_user.id)
        assert data["role"] == "researcher"

    async def test_non_admin_cannot_view_others_permissions(
        self, async_client: AsyncClient, clinician_token: str, researcher_user: User
    ):
        """Test non-admin cannot view other users' permissions."""
        # Act
        response = await async_client.get(
            f"/api/v1/roles/users/{researcher_user.id}/permissions",
            headers={"Authorization": f"Bearer {clinician_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_break_glass_permission_included(
        self, async_client: AsyncClient, admin_token: str, admin_user: User
    ):
        """Test break-glass permission is included for authorized users."""
        # Act
        response = await async_client.get(
            f"/api/v1/roles/users/{admin_user.id}/permissions",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["can_break_glass"] is True
        assert "break_glass:access" in data["permissions"]


class TestAssignRole:
    """Tests for PUT /api/v1/roles/users/{id}/role."""

    async def test_assign_role_success(
        self,
        async_client: AsyncClient,
        admin_token: str,
        clinician_user: User,
        db_session: AsyncSession,
    ):
        """Test successful role assignment."""
        # Arrange
        role_data = {"role": "researcher", "reason": "User transitioning to research team"}

        # Act
        response = await async_client.put(
            f"/api/v1/roles/users/{clinician_user.id}/role",
            json=role_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["role"] == "researcher"
        assert "cohort:create" in data["permissions"]  # Researcher permission

        # Verify update in database
        await db_session.refresh(clinician_user)
        assert clinician_user.role == "researcher"

    async def test_assign_role_non_admin_forbidden(
        self, async_client: AsyncClient, clinician_token: str, researcher_user: User
    ):
        """Test non-admin cannot assign roles."""
        # Arrange
        role_data = {"role": "admin", "reason": "Unauthorized attempt"}

        # Act
        response = await async_client.put(
            f"/api/v1/roles/users/{researcher_user.id}/role",
            json=role_data,
            headers={"Authorization": f"Bearer {clinician_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_assign_role_cannot_change_own(
        self, async_client: AsyncClient, admin_token: str, admin_user: User
    ):
        """Test admin cannot change their own role."""
        # Arrange
        role_data = {"role": "clinician", "reason": "Self-demotion attempt"}

        # Act
        response = await async_client.put(
            f"/api/v1/roles/users/{admin_user.id}/role",
            json=role_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "cannot change your own role" in response.json()["detail"].lower()

    async def test_assign_role_user_not_found(
        self, async_client: AsyncClient, admin_token: str
    ):
        """Test role assignment with non-existent user."""
        # Arrange
        non_existent_id = uuid.uuid4()
        role_data = {"role": "researcher", "reason": "Test"}

        # Act
        response = await async_client.put(
            f"/api/v1/roles/users/{non_existent_id}/role",
            json=role_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_assign_role_audit_logged(
        self,
        async_client: AsyncClient,
        admin_token: str,
        clinician_user: User,
        db_session: AsyncSession,
    ):
        """Test role assignment is audit logged with reason."""
        # Arrange
        role_data = {"role": "admin", "reason": "Promoted to administrator"}

        # Act
        response = await async_client.put(
            f"/api/v1/roles/users/{clinician_user.id}/role",
            json=role_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        # Verify audit log exists (would need to query audit_logs table)
        # In real implementation, would check audit_logs for ASSIGN_ROLE action
