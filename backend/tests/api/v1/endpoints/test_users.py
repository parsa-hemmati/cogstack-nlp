"""Tests for user CRUD API endpoints.

Test suite for user management operations:
- List users (paginated)
- Get user by ID
- Create user (admin only)
- Update user (admin only)
- Delete user (soft delete, admin only)
"""
import uuid
from datetime import datetime

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.auth_service import AuthService


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user for testing."""
    user = User(
        id=uuid.uuid4(),
        username="admin_test",
        email="admin@test.com",
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
        username="clinician_test",
        email="clinician@test.com",
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


class TestListUsers:
    """Tests for GET /api/v1/users (list users)."""

    async def test_list_users_success(
        self, async_client: AsyncClient, admin_token: str, db_session: AsyncSession
    ):
        """Test successful user list retrieval."""
        # Arrange: Create additional test users
        for i in range(5):
            user = User(
                id=uuid.uuid4(),
                username=f"user_{i}",
                email=f"user_{i}@test.com",
                role="clinician",
                is_active=True,
            )
            user.set_password("TestPassword123!")
            db_session.add(user)
        await db_session.commit()

        # Act
        response = await async_client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) > 0
        assert data["total"] >= 5

    async def test_list_users_pagination(
        self, async_client: AsyncClient, admin_token: str, db_session: AsyncSession
    ):
        """Test user list pagination."""
        # Arrange: Create 15 test users
        for i in range(15):
            user = User(
                id=uuid.uuid4(),
                username=f"paginated_user_{i}",
                email=f"paginated_{i}@test.com",
                role="clinician",
                is_active=True,
            )
            user.set_password("TestPassword123!")
            db_session.add(user)
        await db_session.commit()

        # Act: Get first page (10 items)
        response = await async_client.get(
            "/api/v1/users?page=1&page_size=10",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 10
        assert data["page"] == 1
        assert data["page_size"] == 10

    async def test_list_users_unauthorized(self, async_client: AsyncClient):
        """Test user list without authentication."""
        # Act
        response = await async_client.get("/api/v1/users")

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_list_users_non_admin_forbidden(
        self, async_client: AsyncClient, clinician_token: str
    ):
        """Test user list as non-admin (should be admin-only)."""
        # Act
        response = await async_client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {clinician_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGetUser:
    """Tests for GET /api/v1/users/{id} (get user by ID)."""

    async def test_get_user_by_id_success(
        self, async_client: AsyncClient, admin_token: str, clinician_user: User
    ):
        """Test successful user retrieval by ID."""
        # Act
        response = await async_client.get(
            f"/api/v1/users/{clinician_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(clinician_user.id)
        assert data["username"] == clinician_user.username
        assert data["email"] == clinician_user.email
        assert "password_hash" not in data  # Security: no password in response

    async def test_get_user_not_found(
        self, async_client: AsyncClient, admin_token: str
    ):
        """Test user retrieval with non-existent ID."""
        # Arrange
        non_existent_id = uuid.uuid4()

        # Act
        response = await async_client.get(
            f"/api/v1/users/{non_existent_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_user_unauthorized(
        self, async_client: AsyncClient, clinician_user: User
    ):
        """Test user retrieval without authentication."""
        # Act
        response = await async_client.get(f"/api/v1/users/{clinician_user.id}")

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestCreateUser:
    """Tests for POST /api/v1/users (create user)."""

    async def test_create_user_success(
        self, async_client: AsyncClient, admin_token: str, db_session: AsyncSession
    ):
        """Test successful user creation (admin only)."""
        # Arrange
        user_data = {
            "username": "new_user",
            "email": "newuser@test.com",
            "password": "NewUserPassword123!",
            "role": "researcher",
            "is_active": True,
            "can_break_glass": False,
        }

        # Act
        response = await async_client.post(
            "/api/v1/users",
            json=user_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["username"] == "new_user"
        assert data["email"] == "newuser@test.com"
        assert data["role"] == "researcher"
        assert "password" not in data  # Security: no password in response

        # Verify user exists in database
        stmt = select(User).where(User.username == "new_user")
        result = await db_session.execute(stmt)
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.verify_password("NewUserPassword123!")

    async def test_create_user_weak_password(
        self, async_client: AsyncClient, admin_token: str
    ):
        """Test user creation with weak password."""
        # Arrange
        user_data = {
            "username": "weak_pwd_user",
            "email": "weakpwd@test.com",
            "password": "weak",  # Too short, no complexity
            "role": "clinician",
        }

        # Act
        response = await async_client.post(
            "/api/v1/users",
            json=user_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_create_user_duplicate_username(
        self, async_client: AsyncClient, admin_token: str, clinician_user: User
    ):
        """Test user creation with duplicate username."""
        # Arrange
        user_data = {
            "username": clinician_user.username,  # Duplicate
            "email": "different@test.com",
            "password": "ValidPassword123!",
            "role": "clinician",
        }

        # Act
        response = await async_client.post(
            "/api/v1/users",
            json=user_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username already exists" in response.json()["detail"].lower()

    async def test_create_user_non_admin_forbidden(
        self, async_client: AsyncClient, clinician_token: str
    ):
        """Test user creation as non-admin (should be admin-only)."""
        # Arrange
        user_data = {
            "username": "unauthorized_user",
            "email": "unauthorized@test.com",
            "password": "ValidPassword123!",
            "role": "clinician",
        }

        # Act
        response = await async_client.post(
            "/api/v1/users",
            json=user_data,
            headers={"Authorization": f"Bearer {clinician_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUpdateUser:
    """Tests for PUT /api/v1/users/{id} (update user)."""

    async def test_update_user_success(
        self,
        async_client: AsyncClient,
        admin_token: str,
        clinician_user: User,
        db_session: AsyncSession,
    ):
        """Test successful user update (admin only)."""
        # Arrange
        update_data = {
            "email": "updated@test.com",
            "role": "researcher",
            "can_break_glass": True,
        }

        # Act
        response = await async_client.put(
            f"/api/v1/users/{clinician_user.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "updated@test.com"
        assert data["role"] == "researcher"
        assert data["can_break_glass"] is True

        # Verify update in database
        await db_session.refresh(clinician_user)
        assert clinician_user.email == "updated@test.com"
        assert clinician_user.role == "researcher"

    async def test_update_user_partial(
        self,
        async_client: AsyncClient,
        admin_token: str,
        clinician_user: User,
        db_session: AsyncSession,
    ):
        """Test partial user update (only some fields)."""
        # Arrange
        original_email = clinician_user.email
        update_data = {"role": "admin"}  # Only update role

        # Act
        response = await async_client.put(
            f"/api/v1/users/{clinician_user.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["role"] == "admin"
        assert data["email"] == original_email  # Unchanged

    async def test_update_user_not_found(
        self, async_client: AsyncClient, admin_token: str
    ):
        """Test user update with non-existent ID."""
        # Arrange
        non_existent_id = uuid.uuid4()
        update_data = {"role": "admin"}

        # Act
        response = await async_client.put(
            f"/api/v1/users/{non_existent_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_user_non_admin_forbidden(
        self, async_client: AsyncClient, clinician_token: str, admin_user: User
    ):
        """Test user update as non-admin (should be admin-only)."""
        # Arrange
        update_data = {"role": "researcher"}

        # Act
        response = await async_client.put(
            f"/api/v1/users/{admin_user.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {clinician_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestDeleteUser:
    """Tests for DELETE /api/v1/users/{id} (soft delete user)."""

    async def test_delete_user_success(
        self,
        async_client: AsyncClient,
        admin_token: str,
        clinician_user: User,
        db_session: AsyncSession,
    ):
        """Test successful user deletion (soft delete, admin only)."""
        # Act
        response = await async_client.delete(
            f"/api/v1/users/{clinician_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify soft delete (is_active = False)
        await db_session.refresh(clinician_user)
        assert clinician_user.is_active is False

    async def test_delete_user_not_found(
        self, async_client: AsyncClient, admin_token: str
    ):
        """Test user deletion with non-existent ID."""
        # Arrange
        non_existent_id = uuid.uuid4()

        # Act
        response = await async_client.delete(
            f"/api/v1/users/{non_existent_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_user_non_admin_forbidden(
        self, async_client: AsyncClient, clinician_token: str, admin_user: User
    ):
        """Test user deletion as non-admin (should be admin-only)."""
        # Act
        response = await async_client.delete(
            f"/api/v1/users/{admin_user.id}",
            headers={"Authorization": f"Bearer {clinician_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_delete_user_cannot_delete_self(
        self, async_client: AsyncClient, admin_token: str, admin_user: User
    ):
        """Test admin cannot delete their own account."""
        # Act
        response = await async_client.delete(
            f"/api/v1/users/{admin_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "cannot delete your own account" in response.json()["detail"].lower()
