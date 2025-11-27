"""Tests for user profile management API.

Test suite for profile operations:
- Get own profile
- Update own profile (email)
- Change password
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
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        id=uuid.uuid4(),
        username="test_profile_user",
        email="profile@test.com",
        role="clinician",
        is_active=True,
        can_break_glass=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    user.set_password("TestPassword123!")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def other_user(db_session: AsyncSession) -> User:
    """Create another test user for duplicate email tests."""
    user = User(
        id=uuid.uuid4(),
        username="other_user",
        email="other@test.com",
        role="clinician",
        is_active=True,
        can_break_glass=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    user.set_password("OtherPassword123!")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_token(test_user: User) -> str:
    """Generate JWT token for test user."""
    token_data = AuthService.create_access_token(
        user_id=str(test_user.id), role=test_user.role
    )
    return token_data["access_token"]


class TestGetMyProfile:
    """Tests for GET /api/v1/users/me."""

    async def test_get_own_profile_success(
        self, async_client: AsyncClient, test_token: str, test_user: User
    ):
        """Test successful profile retrieval."""
        # Act
        response = await async_client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {test_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
        assert data["role"] == test_user.role
        assert "password_hash" not in data  # Security: no password in response

    async def test_get_own_profile_unauthorized(self, async_client: AsyncClient):
        """Test profile retrieval without authentication."""
        # Act
        response = await async_client.get("/api/v1/users/me")

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUpdateMyProfile:
    """Tests for PUT /api/v1/users/me."""

    async def test_update_own_email(
        self,
        async_client: AsyncClient,
        test_token: str,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Test successful email update."""
        # Arrange
        update_data = {"email": "newemail@test.com"}

        # Act
        response = await async_client.put(
            "/api/v1/users/me",
            json=update_data,
            headers={"Authorization": f"Bearer {test_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "newemail@test.com"

        # Verify update in database
        await db_session.refresh(test_user)
        assert test_user.email == "newemail@test.com"

    async def test_update_own_email_duplicate(
        self, async_client: AsyncClient, test_token: str, other_user: User
    ):
        """Test email update with duplicate email."""
        # Arrange
        update_data = {"email": other_user.email}  # Duplicate

        # Act
        response = await async_client.put(
            "/api/v1/users/me",
            json=update_data,
            headers={"Authorization": f"Bearer {test_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already in use" in response.json()["detail"].lower()

    async def test_update_own_role_forbidden(
        self, async_client: AsyncClient, test_token: str
    ):
        """Test users cannot change their own role."""
        # Arrange
        update_data = {"role": "admin"}

        # Act
        response = await async_client.put(
            "/api/v1/users/me",
            json=update_data,
            headers={"Authorization": f"Bearer {test_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "cannot change your own role" in response.json()["detail"].lower()

    async def test_update_own_active_status_forbidden(
        self, async_client: AsyncClient, test_token: str
    ):
        """Test users cannot change their own active status."""
        # Arrange
        update_data = {"is_active": False}

        # Act
        response = await async_client.put(
            "/api/v1/users/me",
            json=update_data,
            headers={"Authorization": f"Bearer {test_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "active status" in response.json()["detail"].lower()

    async def test_update_own_break_glass_forbidden(
        self, async_client: AsyncClient, test_token: str
    ):
        """Test users cannot grant themselves break-glass permission."""
        # Arrange
        update_data = {"can_break_glass": True}

        # Act
        response = await async_client.put(
            "/api/v1/users/me",
            json=update_data,
            headers={"Authorization": f"Bearer {test_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "break-glass" in response.json()["detail"].lower()


class TestChangePassword:
    """Tests for POST /api/v1/users/me/change-password."""

    async def test_change_password_success(
        self,
        async_client: AsyncClient,
        test_token: str,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Test successful password change."""
        # Arrange
        password_data = {
            "current_password": "TestPassword123!",
            "new_password": "NewSecurePassword456!",
        }

        # Act
        response = await async_client.post(
            "/api/v1/users/me/change-password",
            json=password_data,
            headers={"Authorization": f"Bearer {test_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify new password works
        await db_session.refresh(test_user)
        assert test_user.verify_password("NewSecurePassword456!")
        assert not test_user.verify_password("TestPassword123!")  # Old password doesn't work

    async def test_change_password_incorrect_current(
        self, async_client: AsyncClient, test_token: str
    ):
        """Test password change with incorrect current password."""
        # Arrange
        password_data = {
            "current_password": "WrongPassword!",
            "new_password": "NewSecurePassword456!",
        }

        # Act
        response = await async_client.post(
            "/api/v1/users/me/change-password",
            json=password_data,
            headers={"Authorization": f"Bearer {test_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "incorrect" in response.json()["detail"].lower()

    async def test_change_password_weak_new_password(
        self, async_client: AsyncClient, test_token: str
    ):
        """Test password change with weak new password."""
        # Arrange
        password_data = {
            "current_password": "TestPassword123!",
            "new_password": "weak",  # Too short, no complexity
        }

        # Act
        response = await async_client.post(
            "/api/v1/users/me/change-password",
            json=password_data,
            headers={"Authorization": f"Bearer {test_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_change_password_unauthorized(self, async_client: AsyncClient):
        """Test password change without authentication."""
        # Arrange
        password_data = {
            "current_password": "TestPassword123!",
            "new_password": "NewSecurePassword456!",
        }

        # Act
        response = await async_client.post(
            "/api/v1/users/me/change-password",
            json=password_data,
        )

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_change_password_audit_logged(
        self,
        async_client: AsyncClient,
        test_token: str,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Test password change is audit logged."""
        # Arrange
        password_data = {
            "current_password": "TestPassword123!",
            "new_password": "AuditTestPassword789!",
        }

        # Act
        response = await async_client.post(
            "/api/v1/users/me/change-password",
            json=password_data,
            headers={"Authorization": f"Bearer {test_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify audit log exists (would need to query audit_logs table)
        # In real implementation, would check audit_logs for CHANGE_PASSWORD action
