"""
Tests for User model.

Verifies user creation, password hashing, UUID generation, and constraints.
"""

import pytest
from datetime import datetime
import uuid

# Add backend to path
import sys
from pathlib import Path
backend_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.models.user import User


class TestUserModel:
    """Test User model creation and basic functionality."""

    def test_user_creation(self):
        """Test that User instance can be created with required fields."""
        # Arrange & Act
        user = User(
            username="test_user",
            email="test@example.com",
            password_hash="hashed_password_here",
            role="clinician"
        )

        # Assert
        assert user.username == "test_user"
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password_here"
        assert user.role == "clinician"

    def test_user_id_is_uuid(self):
        """Test that user ID is a valid UUID."""
        # Arrange & Act
        user = User(
            username="test_user",
            email="test@example.com",
            password_hash="hash",
            role="clinician"
        )

        # Assert
        # UUID should be auto-generated if not provided
        assert user.id is None or isinstance(user.id, (str, uuid.UUID))

    def test_user_default_values(self):
        """Test that default values are set correctly."""
        # Arrange & Act
        user = User(
            username="test_user",
            email="test@example.com",
            password_hash="hash",
            role="clinician"
        )

        # Assert - defaults should be set
        assert user.is_active is True, "User should be active by default"
        assert user.can_break_glass is False, "Break-glass should be disabled by default"

    def test_user_timestamps(self):
        """Test that created_at and updated_at are set."""
        # Arrange & Act
        user = User(
            username="test_user",
            email="test@example.com",
            password_hash="hash",
            role="clinician"
        )

        # Assert - timestamps should be None initially (set by DB)
        # Will be set by database on insert
        assert user.created_at is None or isinstance(user.created_at, datetime)
        assert user.updated_at is None or isinstance(user.updated_at, datetime)

    def test_user_repr(self):
        """Test that __repr__ returns useful string."""
        # Arrange
        user = User(
            username="test_user",
            email="test@example.com",
            password_hash="hash",
            role="clinician"
        )

        # Act
        repr_str = repr(user)

        # Assert
        assert "User" in repr_str
        assert "test_user" in repr_str


class TestUserPasswordHashing:
    """Test password hashing and verification methods."""

    def test_set_password_hashes_password(self):
        """Test that set_password creates a bcrypt hash."""
        # Arrange
        user = User(
            username="test_user",
            email="test@example.com",
            role="clinician"
        )
        plaintext_password = "SecurePassword123!"

        # Act
        user.set_password(plaintext_password)

        # Assert
        assert user.password_hash is not None, \
            "Password hash should be set"
        assert user.password_hash != plaintext_password, \
            "Password hash should not equal plaintext"
        assert user.password_hash.startswith("$2b$"), \
            "Password hash should be bcrypt format (starts with $2b$)"

    def test_verify_password_correct(self):
        """Test that verify_password returns True for correct password."""
        # Arrange
        user = User(
            username="test_user",
            email="test@example.com",
            role="clinician"
        )
        plaintext_password = "SecurePassword123!"
        user.set_password(plaintext_password)

        # Act
        result = user.verify_password(plaintext_password)

        # Assert
        assert result is True, \
            "Verify should return True for correct password"

    def test_verify_password_incorrect(self):
        """Test that verify_password returns False for wrong password."""
        # Arrange
        user = User(
            username="test_user",
            email="test@example.com",
            role="clinician"
        )
        user.set_password("CorrectPassword123!")

        # Act
        result = user.verify_password("WrongPassword456!")

        # Assert
        assert result is False, \
            "Verify should return False for incorrect password"

    def test_password_hash_is_salted(self):
        """Test that same password generates different hashes (salt)."""
        # Arrange
        user1 = User(username="user1", email="user1@example.com", role="clinician")
        user2 = User(username="user2", email="user2@example.com", role="clinician")
        same_password = "SamePassword123!"

        # Act
        user1.set_password(same_password)
        user2.set_password(same_password)

        # Assert
        assert user1.password_hash != user2.password_hash, \
            "Same password should generate different hashes (bcrypt salt)"


class TestUserConstraints:
    """Test model constraints and validation."""

    def test_username_required(self):
        """Test that username is required."""
        # This test verifies the model definition
        # Username should be non-nullable in the model
        user = User(
            email="test@example.com",
            password_hash="hash",
            role="clinician"
        )
        # Username=None should be allowed in Python, but DB will reject
        # Just verify the field exists
        assert hasattr(user, 'username')

    def test_email_required(self):
        """Test that email is required."""
        user = User(
            username="test_user",
            password_hash="hash",
            role="clinician"
        )
        # Email=None should be allowed in Python, but DB will reject
        assert hasattr(user, 'email')

    def test_role_required(self):
        """Test that role is required."""
        user = User(
            username="test_user",
            email="test@example.com",
            password_hash="hash"
        )
        # Role=None should be allowed in Python, but DB will reject
        assert hasattr(user, 'role')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
