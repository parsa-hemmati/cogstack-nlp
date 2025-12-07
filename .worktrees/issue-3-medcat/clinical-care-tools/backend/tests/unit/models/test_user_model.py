"""Tests for User model."""

import pytest
from datetime import datetime, timedelta

from app.models.user import User, UserRole


def test_user_creation():
    """Test creating a user."""
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        role=UserRole.CLINICIAN,
    )

    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.full_name == "Test User"
    assert user.role == UserRole.CLINICIAN
    assert user.is_active is True
    assert user.can_break_glass is False


def test_password_hashing():
    """Test password hashing."""
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
    )

    password = "securepassword123"
    user.set_password(password)

    # Password should be hashed
    assert user.password_hash != password
    assert len(user.password_hash) > 0

    # Verify password works
    assert user.verify_password(password) is True
    assert user.verify_password("wrongpassword") is False


def test_is_locked():
    """Test account lockout detection."""
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
    )

    # Not locked by default
    assert user.is_locked is False

    # Lock account for 15 minutes
    user.locked_until = datetime.utcnow() + timedelta(minutes=15)
    assert user.is_locked is True

    # Expired lockout
    user.locked_until = datetime.utcnow() - timedelta(minutes=1)
    assert user.is_locked is False


def test_failed_login_tracking():
    """Test failed login attempt tracking."""
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
    )

    assert user.failed_login_attempts == 0

    # Increment failed attempts
    user.increment_failed_login()
    assert user.failed_login_attempts == 1

    user.increment_failed_login()
    assert user.failed_login_attempts == 2

    # Reset
    user.reset_failed_login()
    assert user.failed_login_attempts == 0
    assert user.locked_until is None


def test_user_repr():
    """Test user string representation."""
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        role=UserRole.CLINICIAN,
    )

    repr_str = repr(user)
    assert "testuser" in repr_str
    assert "test@example.com" in repr_str
    assert "clinician" in repr_str.lower()
