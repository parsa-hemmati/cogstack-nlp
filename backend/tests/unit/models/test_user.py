"""
Test User Model
Unit tests for User model with password hashing and validation
"""
import uuid
import pytest
from datetime import datetime
from app.models.user import User, pwd_context


class TestUserModel:
    """Test User model creation, password hashing, and methods."""

    def test_user_creation(self):
        """Test that User can be instantiated."""
        user = User(
            username="testuser",
            email="test@example.com",
            role="clinician",
        )

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == "clinician"
        assert user.is_active is True  # Default value
        assert user.can_break_glass is False  # Default value

    def test_user_id_is_uuid(self):
        """Test that user ID is auto-generated UUID."""
        user = User(username="testuser", email="test@example.com")

        # ID should be auto-generated
        assert user.id is not None
        assert isinstance(user.id, uuid.UUID)

    def test_password_hashing(self):
        """Test that password is hashed correctly."""
        user = User(username="testuser", email="test@example.com")
        plaintext_password = "SecurePassword123!"

        user.set_password(plaintext_password)

        # Password hash should be set
        assert user.password_hash is not None
        # Password hash should NOT equal plaintext
        assert user.password_hash != plaintext_password
        # Password hash should start with bcrypt prefix
        assert user.password_hash.startswith("$2b$")

    def test_password_verification_correct(self):
        """Test that correct password verifies successfully."""
        user = User(username="testuser", email="test@example.com")
        password = "MySecurePassword456"

        user.set_password(password)
        assert user.verify_password(password) is True

    def test_password_verification_incorrect(self):
        """Test that incorrect password fails verification."""
        user = User(username="testuser", email="test@example.com")
        correct_password = "CorrectPassword123"
        incorrect_password = "WrongPassword456"

        user.set_password(correct_password)
        assert user.verify_password(incorrect_password) is False

    def test_password_hash_is_unique(self):
        """Test that hashing same password twice produces different hashes."""
        user1 = User(username="user1", email="user1@example.com")
        user2 = User(username="user2", email="user2@example.com")
        password = "SamePassword123"

        user1.set_password(password)
        user2.set_password(password)

        # Hashes should be different (bcrypt uses random salt)
        assert user1.password_hash != user2.password_hash
        # But both should verify correctly
        assert user1.verify_password(password) is True
        assert user2.verify_password(password) is True

    def test_user_roles(self):
        """Test that all valid user roles can be set."""
        roles = ["clinician", "researcher", "admin"]

        for role in roles:
            user = User(username=f"user_{role}", email=f"{role}@example.com", role=role)
            assert user.role == role

    def test_user_can_break_glass(self):
        """Test that can_break_glass flag can be set."""
        user = User(username="emergencyuser", email="emergency@example.com", can_break_glass=True)
        assert user.can_break_glass is True

    def test_user_to_dict_excludes_password_hash(self):
        """Test that to_dict() excludes password_hash by default."""
        user = User(username="testuser", email="test@example.com")
        user.set_password("password123")

        user_dict = user.to_dict()

        assert "password_hash" not in user_dict
        assert user_dict["username"] == "testuser"
        assert user_dict["email"] == "test@example.com"

    def test_user_to_dict_includes_password_hash_when_requested(self):
        """Test that to_dict() includes password_hash when explicitly requested."""
        user = User(username="testuser", email="test@example.com")
        user.set_password("password123")

        user_dict = user.to_dict(include_password_hash=True)

        assert "password_hash" in user_dict
        assert user_dict["password_hash"] == user.password_hash

    def test_user_repr(self):
        """Test that __repr__() returns correct string representation."""
        user = User(username="testuser", email="test@example.com", role="admin")

        repr_str = repr(user)

        assert "testuser" in repr_str
        assert "admin" in repr_str
        assert "User(" in repr_str

    def test_timestamps_auto_set(self):
        """Test that created_at and updated_at are auto-set."""
        user = User(username="testuser", email="test@example.com")

        # Timestamps should be auto-set to current time
        assert user.created_at is not None
        assert user.updated_at is not None
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
