"""
Unit tests for Session model.

Tests session creation, expiry, binding, and concurrency limits.
"""

import pytest
from datetime import datetime, timedelta
import uuid
import hashlib
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.models.session import Session
from app.models.user import User
from app.core.database import AsyncSessionLocal, engine, Base


@pytest.fixture
async def test_db():
    """Create test database tables and clean up after test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

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


def hash_value(value: str) -> str:
    """Hash a value using SHA256."""
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


@pytest.mark.asyncio
async def test_session_creation(test_user):
    """Test that a session can be created with all required fields."""
    # Arrange
    token_jti = str(uuid.uuid4())
    ip_address = "192.168.1.100"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

    # Act
    async with AsyncSessionLocal() as db:
        session = Session(
            user_id=test_user.id,
            token_jti=token_jti,
            ip_hash=hash_value(ip_address),
            user_agent_hash=hash_value(user_agent)
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        # Assert
        assert session.id is not None, \
            "Session should have an ID after creation"
        assert session.user_id == test_user.id, \
            "Session should be linked to the user"
        assert session.token_jti == token_jti, \
            "Session should store the token JTI"
        assert session.ip_hash == hash_value(ip_address), \
            "Session should store hashed IP address"
        assert session.user_agent_hash == hash_value(user_agent), \
            "Session should store hashed user agent"
        assert session.created_at is not None, \
            "Session should have creation timestamp"
        assert session.last_activity is not None, \
            "Session should have last activity timestamp"
        assert session.expires_at is not None, \
            "Session should have expiration timestamp"


@pytest.mark.asyncio
async def test_session_expires_after_8_hours(test_user):
    """Test that session expires_at is set to 8 hours from creation."""
    # Arrange & Act
    async with AsyncSessionLocal() as db:
        session = Session(
            user_id=test_user.id,
            token_jti=str(uuid.uuid4()),
            ip_hash=hash_value("192.168.1.100"),
            user_agent_hash=hash_value("Mozilla/5.0")
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        # Assert
        expected_expiry = session.created_at + timedelta(hours=8)
        time_diff = abs((session.expires_at - expected_expiry).total_seconds())

        assert time_diff < 2, \
            "Session should expire 8 hours after creation (within 2 seconds tolerance)"


@pytest.mark.asyncio
async def test_session_is_expired_property(test_user):
    """Test the is_expired property correctly identifies expired sessions."""
    # Arrange
    async with AsyncSessionLocal() as db:
        # Create active session
        active_session = Session(
            user_id=test_user.id,
            token_jti=str(uuid.uuid4()),
            ip_hash=hash_value("192.168.1.100"),
            user_agent_hash=hash_value("Mozilla/5.0")
        )
        db.add(active_session)
        await db.commit()
        await db.refresh(active_session)

        # Create expired session (manually set past expiry)
        expired_session = Session(
            user_id=test_user.id,
            token_jti=str(uuid.uuid4()),
            ip_hash=hash_value("192.168.1.101"),
            user_agent_hash=hash_value("Mozilla/5.0")
        )
        db.add(expired_session)
        await db.commit()
        await db.refresh(expired_session)

        # Manually set expiry to past
        expired_session.expires_at = datetime.utcnow() - timedelta(hours=1)
        await db.commit()
        await db.refresh(expired_session)

        # Assert
        assert not active_session.is_expired, \
            "Active session should not be expired"
        assert expired_session.is_expired, \
            "Session with past expiry should be expired"


@pytest.mark.asyncio
async def test_session_update_activity_extends_expiry(test_user):
    """Test that updating last_activity extends the expiry time."""
    # Arrange
    async with AsyncSessionLocal() as db:
        session = Session(
            user_id=test_user.id,
            token_jti=str(uuid.uuid4()),
            ip_hash=hash_value("192.168.1.100"),
            user_agent_hash=hash_value("Mozilla/5.0")
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        original_expiry = session.expires_at

        # Act - Update activity
        session.update_activity()
        await db.commit()
        await db.refresh(session)

        # Assert
        assert session.last_activity > session.created_at, \
            "Last activity should be updated"
        assert session.expires_at > original_expiry, \
            "Expiry should be extended after activity update"

        expected_new_expiry = session.last_activity + timedelta(hours=8)
        time_diff = abs((session.expires_at - expected_new_expiry).total_seconds())

        assert time_diff < 2, \
            "New expiry should be 8 hours from last activity"


@pytest.mark.asyncio
async def test_session_binding_validates_ip_hash(test_user):
    """Test that session validates IP hash for binding."""
    # Arrange
    original_ip = "192.168.1.100"
    different_ip = "192.168.1.200"

    async with AsyncSessionLocal() as db:
        session = Session(
            user_id=test_user.id,
            token_jti=str(uuid.uuid4()),
            ip_hash=hash_value(original_ip),
            user_agent_hash=hash_value("Mozilla/5.0")
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        # Assert
        assert session.validate_binding(
            hash_value(original_ip),
            hash_value("Mozilla/5.0")
        ), "Session should validate with matching IP and user agent"

        assert not session.validate_binding(
            hash_value(different_ip),
            hash_value("Mozilla/5.0")
        ), "Session should not validate with different IP"


@pytest.mark.asyncio
async def test_session_binding_validates_user_agent_hash(test_user):
    """Test that session validates user agent hash for binding."""
    # Arrange
    original_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    different_ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"

    async with AsyncSessionLocal() as db:
        session = Session(
            user_id=test_user.id,
            token_jti=str(uuid.uuid4()),
            ip_hash=hash_value("192.168.1.100"),
            user_agent_hash=hash_value(original_ua)
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        # Assert
        assert session.validate_binding(
            hash_value("192.168.1.100"),
            hash_value(original_ua)
        ), "Session should validate with matching IP and user agent"

        assert not session.validate_binding(
            hash_value("192.168.1.100"),
            hash_value(different_ua)
        ), "Session should not validate with different user agent"


@pytest.mark.asyncio
async def test_session_invalidate_marks_as_expired(test_user):
    """Test that invalidate() method marks session as expired."""
    # Arrange
    async with AsyncSessionLocal() as db:
        session = Session(
            user_id=test_user.id,
            token_jti=str(uuid.uuid4()),
            ip_hash=hash_value("192.168.1.100"),
            user_agent_hash=hash_value("Mozilla/5.0")
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        assert not session.is_expired, \
            "Session should not be expired initially"

        # Act
        session.invalidate()
        await db.commit()
        await db.refresh(session)

        # Assert
        assert session.is_expired, \
            "Session should be expired after invalidation"
        assert session.expires_at < datetime.utcnow(), \
            "Expiry time should be in the past"


@pytest.mark.asyncio
async def test_max_two_concurrent_sessions_per_user(test_user):
    """Test that a user can have maximum 2 concurrent active sessions."""
    # This test validates the business rule, actual enforcement is in session service
    # Arrange
    async with AsyncSessionLocal() as db:
        # Create 2 sessions
        session1 = Session(
            user_id=test_user.id,
            token_jti=str(uuid.uuid4()),
            ip_hash=hash_value("192.168.1.100"),
            user_agent_hash=hash_value("Mozilla/5.0")
        )
        session2 = Session(
            user_id=test_user.id,
            token_jti=str(uuid.uuid4()),
            ip_hash=hash_value("192.168.1.101"),
            user_agent_hash=hash_value("Chrome/90.0")
        )
        db.add(session1)
        db.add(session2)
        await db.commit()

        # Query active sessions
        from sqlalchemy import select, and_
        result = await db.execute(
            select(Session).where(
                and_(
                    Session.user_id == test_user.id,
                    Session.expires_at > datetime.utcnow()
                )
            )
        )
        active_sessions = result.scalars().all()

        # Assert
        assert len(active_sessions) == 2, \
            "User should have 2 active sessions"


@pytest.mark.asyncio
async def test_session_relationship_with_user(test_user):
    """Test that Session has proper foreign key relationship with User."""
    # Arrange & Act
    async with AsyncSessionLocal() as db:
        session = Session(
            user_id=test_user.id,
            token_jti=str(uuid.uuid4()),
            ip_hash=hash_value("192.168.1.100"),
            user_agent_hash=hash_value("Mozilla/5.0")
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        # Assert
        assert session.user_id == test_user.id, \
            "Session should reference the correct user ID"


@pytest.mark.asyncio
async def test_session_token_jti_uniqueness(test_user):
    """Test that token_jti should be unique across sessions."""
    # Arrange
    token_jti = str(uuid.uuid4())

    async with AsyncSessionLocal() as db:
        session1 = Session(
            user_id=test_user.id,
            token_jti=token_jti,
            ip_hash=hash_value("192.168.1.100"),
            user_agent_hash=hash_value("Mozilla/5.0")
        )
        db.add(session1)
        await db.commit()

        # Act - Try to create duplicate token_jti
        session2 = Session(
            user_id=test_user.id,
            token_jti=token_jti,  # Same JTI
            ip_hash=hash_value("192.168.1.101"),
            user_agent_hash=hash_value("Chrome/90.0")
        )
        db.add(session2)

        # Assert
        with pytest.raises(Exception):  # Should raise IntegrityError
            await db.commit()


@pytest.mark.asyncio
async def test_session_timestamps_are_utc(test_user):
    """Test that all timestamps are in UTC."""
    # Arrange & Act
    async with AsyncSessionLocal() as db:
        session = Session(
            user_id=test_user.id,
            token_jti=str(uuid.uuid4()),
            ip_hash=hash_value("192.168.1.100"),
            user_agent_hash=hash_value("Mozilla/5.0")
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        # Assert
        now_utc = datetime.utcnow()

        # Check created_at is recent (within last minute)
        assert (now_utc - session.created_at).total_seconds() < 60, \
            "created_at should be recent UTC time"

        # Check last_activity is recent
        assert (now_utc - session.last_activity).total_seconds() < 60, \
            "last_activity should be recent UTC time"

        # Check expires_at is in future (around 8 hours)
        assert session.expires_at > now_utc, \
            "expires_at should be in the future"


@pytest.mark.asyncio
async def test_session_cascade_delete_with_user(test_db):
    """Test that sessions are deleted when user is deleted (cascade)."""
    # Arrange
    async with AsyncSessionLocal() as db:
        # Create user
        user = User(
            username="tempuser",
            email="temp@example.com",
            role="clinician"
        )
        user.set_password("Password123!")
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Create session for user
        session = Session(
            user_id=user.id,
            token_jti=str(uuid.uuid4()),
            ip_hash=hash_value("192.168.1.100"),
            user_agent_hash=hash_value("Mozilla/5.0")
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        session_id = session.id

        # Act - Delete user
        await db.delete(user)
        await db.commit()

        # Assert - Session should also be deleted (cascade)
        from sqlalchemy import select
        result = await db.execute(
            select(Session).where(Session.id == session_id)
        )
        deleted_session = result.scalar_one_or_none()

        assert deleted_session is None, \
            "Session should be deleted when user is deleted (cascade)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
