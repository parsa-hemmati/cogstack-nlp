"""
Integration tests for User Management API.

Tests CRUD operations for users with admin-only access control.
"""

import uuid
from datetime import datetime
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.security import hash_password


@pytest.fixture
async def admin_token(test_client: AsyncClient, test_db: AsyncSession):
    """Create an admin user and return JWT token."""
    admin_user = User(
        id=uuid.uuid4(),
        username="admin_test",
        email="admin@test.com",
        password_hash=hash_password("Test@Admin123!"),
        role="admin",
        is_active=True,
        created_at=datetime.utcnow()
    )
    test_db.add(admin_user)
    await test_db.commit()

    # Login to get token
    response = await test_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "Test@Admin123!"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
async def regular_token(test_client: AsyncClient, test_db: AsyncSession):
    """Create a regular user and return JWT token."""
    user = User(
        id=uuid.uuid4(),
        username="user_test",
        email="user@test.com",
        password_hash=hash_password("Test@User123!"),
        role="clinician",
        is_active=True,
        created_at=datetime.utcnow()
    )
    test_db.add(user)
    await test_db.commit()

    # Login to get token
    response = await test_client.post(
        "/api/v1/auth/login",
        json={"email": "user@test.com", "password": "Test@User123!"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
async def sample_user(test_db: AsyncSession):
    """Create a sample user in the database."""
    user = User(
        id=uuid.uuid4(),
        username="sample_user",
        email="sample@test.com",
        password_hash=hash_password("Sample@Pass123!"),
        role="researcher",
        is_active=True,
        created_at=datetime.utcnow()
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


class TestUsersList:
    """Tests for GET /api/v1/users endpoint."""

    async def test_list_users_as_admin(
        self, test_client: AsyncClient, admin_token: str, sample_user: User
    ):
        """Admin should be able to list all users."""
        response = await test_client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert data["total"] >= 2  # Admin + sample user

    async def test_list_users_with_pagination(
        self, test_client: AsyncClient, admin_token: str, test_db: AsyncSession
    ):
        """Test pagination parameters."""
        # Create multiple users
        for i in range(5):
            user = User(
                id=uuid.uuid4(),
                username=f"user_{i}",
                email=f"user{i}@test.com",
                password_hash=hash_password("Test@Pass123!"),
                role="researcher",
                is_active=True,
                created_at=datetime.utcnow()
            )
            test_db.add(user)
        await test_db.commit()

        # Test pagination
        response = await test_client.get(
            "/api/v1/users?page=1&per_page=3",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 3
        assert data["page"] == 1
        assert data["per_page"] == 3

    async def test_list_users_forbidden_for_non_admin(
        self, test_client: AsyncClient, regular_token: str
    ):
        """Non-admin users should not be able to list users."""
        response = await test_client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {regular_token}"}
        )
        assert response.status_code == 403

    async def test_list_users_unauthorized(self, test_client: AsyncClient):
        """Unauthenticated requests should return 401."""
        response = await test_client.get("/api/v1/users")
        assert response.status_code == 401


class TestCreateUser:
    """Tests for POST /api/v1/users endpoint."""

    async def test_create_user_as_admin(
        self, test_client: AsyncClient, admin_token: str
    ):
        """Admin should be able to create new users."""
        user_data = {
            "username": "new_user",
            "email": "new@test.com",
            "password": "NewUser@Pass123!",
            "role": "clinician",
            "is_active": True
        }

        response = await test_client.post(
            "/api/v1/users",
            json=user_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "new_user"
        assert data["email"] == "new@test.com"
        assert data["role"] == "clinician"
        assert data["is_active"] is True
        assert "id" in data
        assert "password" not in data
        assert "password_hash" not in data

    async def test_create_user_duplicate_email(
        self, test_client: AsyncClient, admin_token: str, sample_user: User
    ):
        """Creating user with duplicate email should fail."""
        user_data = {
            "username": "another_user",
            "email": sample_user.email,  # Duplicate email
            "password": "AnotherUser@Pass123!",
            "role": "clinician"
        }

        response = await test_client.post(
            "/api/v1/users",
            json=user_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    async def test_create_user_invalid_role(
        self, test_client: AsyncClient, admin_token: str
    ):
        """Creating user with invalid role should fail."""
        user_data = {
            "username": "invalid_role_user",
            "email": "invalid_role@test.com",
            "password": "Invalid@Role123!",
            "role": "invalid_role"
        }

        response = await test_client.post(
            "/api/v1/users",
            json=user_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 422

    async def test_create_user_weak_password(
        self, test_client: AsyncClient, admin_token: str
    ):
        """Creating user with weak password should fail."""
        user_data = {
            "username": "weak_pass_user",
            "email": "weak@test.com",
            "password": "weak",  # Too weak
            "role": "clinician"
        }

        response = await test_client.post(
            "/api/v1/users",
            json=user_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400
        assert "password" in response.json()["detail"].lower()

    async def test_create_user_forbidden_for_non_admin(
        self, test_client: AsyncClient, regular_token: str
    ):
        """Non-admin users should not be able to create users."""
        user_data = {
            "username": "forbidden_user",
            "email": "forbidden@test.com",
            "password": "Forbidden@Pass123!",
            "role": "clinician"
        }

        response = await test_client.post(
            "/api/v1/users",
            json=user_data,
            headers={"Authorization": f"Bearer {regular_token}"}
        )
        assert response.status_code == 403


class TestGetUser:
    """Tests for GET /api/v1/users/{id} endpoint."""

    async def test_get_user_by_id(
        self, test_client: AsyncClient, admin_token: str, sample_user: User
    ):
        """Admin should be able to get user details by ID."""
        response = await test_client.get(
            f"/api/v1/users/{sample_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_user.id)
        assert data["username"] == sample_user.username
        assert data["email"] == sample_user.email
        assert "password_hash" not in data

    async def test_get_nonexistent_user(
        self, test_client: AsyncClient, admin_token: str
    ):
        """Getting non-existent user should return 404."""
        fake_id = uuid.uuid4()
        response = await test_client.get(
            f"/api/v1/users/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404

    async def test_get_user_forbidden_for_non_admin(
        self, test_client: AsyncClient, regular_token: str, sample_user: User
    ):
        """Non-admin users should not be able to get other users."""
        response = await test_client.get(
            f"/api/v1/users/{sample_user.id}",
            headers={"Authorization": f"Bearer {regular_token}"}
        )
        assert response.status_code == 403


class TestUpdateUser:
    """Tests for PATCH /api/v1/users/{id} endpoint."""

    async def test_update_user_fields(
        self, test_client: AsyncClient, admin_token: str, sample_user: User
    ):
        """Admin should be able to update user fields."""
        update_data = {
            "email": "updated@test.com",
            "role": "admin",
            "is_active": False
        }

        response = await test_client.patch(
            f"/api/v1/users/{sample_user.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "updated@test.com"
        assert data["role"] == "admin"
        assert data["is_active"] is False

    async def test_update_user_password(
        self, test_client: AsyncClient, admin_token: str, sample_user: User
    ):
        """Admin should be able to reset user password."""
        update_data = {
            "password": "NewPassword@123!"
        }

        response = await test_client.patch(
            f"/api/v1/users/{sample_user.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200

        # Verify new password works
        login_response = await test_client.post(
            "/api/v1/auth/login",
            json={"email": sample_user.email, "password": "NewPassword@123!"}
        )
        assert login_response.status_code == 200

    async def test_update_nonexistent_user(
        self, test_client: AsyncClient, admin_token: str
    ):
        """Updating non-existent user should return 404."""
        fake_id = uuid.uuid4()
        response = await test_client.patch(
            f"/api/v1/users/{fake_id}",
            json={"email": "test@test.com"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404

    async def test_update_user_forbidden_for_non_admin(
        self, test_client: AsyncClient, regular_token: str, sample_user: User
    ):
        """Non-admin users should not be able to update other users."""
        response = await test_client.patch(
            f"/api/v1/users/{sample_user.id}",
            json={"email": "hacker@test.com"},
            headers={"Authorization": f"Bearer {regular_token}"}
        )
        assert response.status_code == 403


class TestDeleteUser:
    """Tests for DELETE /api/v1/users/{id} endpoint."""

    async def test_soft_delete_user(
        self, test_client: AsyncClient, admin_token: str, sample_user: User, test_db: AsyncSession
    ):
        """Admin should be able to soft delete users."""
        response = await test_client.delete(
            f"/api/v1/users/{sample_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 204

        # Verify user is soft deleted (is_active = False)
        await test_db.refresh(sample_user)
        assert sample_user.is_active is False

    async def test_delete_nonexistent_user(
        self, test_client: AsyncClient, admin_token: str
    ):
        """Deleting non-existent user should return 404."""
        fake_id = uuid.uuid4()
        response = await test_client.delete(
            f"/api/v1/users/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404

    async def test_delete_user_forbidden_for_non_admin(
        self, test_client: AsyncClient, regular_token: str, sample_user: User
    ):
        """Non-admin users should not be able to delete users."""
        response = await test_client.delete(
            f"/api/v1/users/{sample_user.id}",
            headers={"Authorization": f"Bearer {regular_token}"}
        )
        assert response.status_code == 403

    async def test_cannot_delete_self(
        self, test_client: AsyncClient, test_db: AsyncSession
    ):
        """Admin should not be able to delete their own account."""
        # Create admin and get token
        admin_user = User(
            id=uuid.uuid4(),
            username="self_delete_admin",
            email="self_delete@test.com",
            password_hash=hash_password("SelfDelete@123!"),
            role="admin",
            is_active=True,
            created_at=datetime.utcnow()
        )
        test_db.add(admin_user)
        await test_db.commit()

        response = await test_client.post(
            "/api/v1/auth/login",
            json={"email": "self_delete@test.com", "password": "SelfDelete@123!"}
        )
        token = response.json()["access_token"]

        # Try to delete self
        response = await test_client.delete(
            f"/api/v1/users/{admin_user.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400
        assert "cannot delete" in response.json()["detail"].lower()