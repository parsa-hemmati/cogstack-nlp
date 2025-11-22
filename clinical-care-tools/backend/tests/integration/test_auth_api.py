"""
Integration tests for authentication API endpoints.

Tests login endpoint with database and JWT token generation.
"""

import pytest
import httpx
from fastapi import status
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app
from app.core.database import Base, engine, AsyncSessionLocal
from app.models.user import User


@pytest.fixture
async def test_db():
    """Create test database tables and clean up after test."""
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def test_user(test_db):
    """Create a test user in the database."""
    async with AsyncSessionLocal() as db:
        user = User(
            username="testuser",
            email="test@example.com",
            role="clinician"
        )
        user.set_password("SecurePassword123!")
        db.add(user)
        await db.commit()
        await db.refresh(user)
        yield user


@pytest.fixture
async def client():
    """Create async HTTP client for testing."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_login_with_valid_credentials_returns_token(client, test_user):
    """Test that login with valid credentials returns 200 with token."""
    # Arrange
    login_data = {
        "username": "testuser",
        "password": "SecurePassword123!"
    }

    # Act
    response = await client.post("/api/v1/auth/login", json=login_data)

    # Assert
    assert response.status_code == status.HTTP_200_OK, \
        "Login with valid credentials should return 200"

    data = response.json()
    assert "access_token" in data, \
        "Response should contain access_token"
    assert "token_type" in data, \
        "Response should contain token_type"
    assert data["token_type"] == "bearer", \
        "Token type should be 'bearer'"
    assert "expires_at" in data, \
        "Response should contain expires_at timestamp"
    assert "user" in data, \
        "Response should contain user object"


@pytest.mark.asyncio
async def test_login_with_invalid_password_returns_401(client, test_user):
    """Test that login with wrong password returns 401."""
    # Arrange
    login_data = {
        "username": "testuser",
        "password": "WrongPassword456!"
    }

    # Act
    response = await client.post("/api/v1/auth/login", json=login_data)

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
        "Login with invalid password should return 401"

    data = response.json()
    assert "detail" in data, \
        "Error response should contain detail message"


@pytest.mark.asyncio
async def test_login_with_nonexistent_user_returns_401(client, test_db):
    """Test that login with non-existent username returns 401."""
    # Arrange
    login_data = {
        "username": "nonexistent",
        "password": "SomePassword123!"
    }

    # Act
    response = await client.post("/api/v1/auth/login", json=login_data)

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
        "Login with non-existent user should return 401"


@pytest.mark.asyncio
async def test_login_response_has_correct_token_format(client, test_user):
    """Test that login response contains properly formatted JWT token."""
    # Arrange
    login_data = {
        "username": "testuser",
        "password": "SecurePassword123!"
    }

    # Act
    response = await client.post("/api/v1/auth/login", json=login_data)
    data = response.json()

    # Assert
    token = data["access_token"]
    assert isinstance(token, str), \
        "Token should be string"
    assert len(token) > 50, \
        "JWT token should be reasonably long"
    assert token.count(".") == 2, \
        "JWT should have 3 parts separated by dots"


@pytest.mark.asyncio
async def test_login_response_does_not_expose_password(client, test_user):
    """Test that password is not exposed in login response."""
    # Arrange
    login_data = {
        "username": "testuser",
        "password": "SecurePassword123!"
    }

    # Act
    response = await client.post("/api/v1/auth/login", json=login_data)
    data = response.json()

    # Assert
    response_str = str(data).lower()
    assert "password" not in response_str, \
        "Password should not appear in response"
    assert "password_hash" not in response_str, \
        "Password hash should not appear in response"


@pytest.mark.asyncio
async def test_login_user_object_contains_expected_fields(client, test_user):
    """Test that user object in response has expected fields."""
    # Arrange
    login_data = {
        "username": "testuser",
        "password": "SecurePassword123!"
    }

    # Act
    response = await client.post("/api/v1/auth/login", json=login_data)
    data = response.json()

    # Assert
    user = data["user"]
    assert "id" in user, "User should have id"
    assert "username" in user, "User should have username"
    assert "email" in user, "User should have email"
    assert "role" in user, "User should have role"
    assert user["username"] == "testuser"
    assert user["role"] == "clinician"


@pytest.mark.asyncio
async def test_login_with_inactive_user_returns_401(client, test_db):
    """Test that login with inactive user returns 401."""
    # Arrange - Create inactive user
    async with AsyncSessionLocal() as db:
        user = User(
            username="inactive",
            email="inactive@example.com",
            role="clinician",
            is_active=False
        )
        user.set_password("Password123!")
        db.add(user)
        await db.commit()

    login_data = {
        "username": "inactive",
        "password": "Password123!"
    }

    # Act
    response = await client.post("/api/v1/auth/login", json=login_data)

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
        "Login with inactive user should return 401"


@pytest.mark.asyncio
async def test_token_can_be_used_for_subsequent_requests(client, test_user):
    """Test that token returned from login can be used for authentication."""
    # Arrange - Login to get token
    login_data = {
        "username": "testuser",
        "password": "SecurePassword123!"
    }
    login_response = await client.post("/api/v1/auth/login", json=login_data)
    token = login_response.json()["access_token"]

    # Act - Use token in Authorization header
    headers = {"Authorization": f"Bearer {token}"}

    # Try to access a protected endpoint (will create later)
    # For now, just verify token format is valid by calling verify
    from app.services.auth_service import verify_token
    payload = verify_token(token)

    # Assert
    assert "sub" in payload, \
        "Token should contain user ID"
    assert payload["role"] == "clinician", \
        "Token should contain user role"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
